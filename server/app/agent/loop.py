import json
import os
from collections.abc import Sequence
from typing import Literal

from app.agent.tools import TOOL_MAP, TOOLS
from dotenv import find_dotenv, load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict

load_dotenv(find_dotenv())

_client = None
MAX_AGENT_TURNS = 5
FALLBACK_MODELS = ("gemini-3.5-flash", "gemini-3.6-flash")
DEFAULT_MODEL = "gemini-3.5-flash-lite"


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "model"]
    content: str


def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please add GEMINI_API_KEY=your_key_here to your server/.env file. "
                "You can obtain a key at https://aistudio.google.com/."
            )
        _client = genai.Client(api_key=api_key)
    return _client


SYSTEM_INSTRUCTION = """
You are InsightOut, an expert E-commerce Analytics AI assistant.
Your goal is to answer user questions using Google Analytics 4 (GA4) BigQuery data.

Guidelines:
1. When asked a question, check the schema using `get_ga4_schema` if needed.
2. Formulate and execute standard BigQuery SQL queries using `execute_sql_query`.
3. Analyze the output and present a clear, conversational answer.
4. If appropriate, return a JSON block for charting at the end of your message in this format:
   ```chart
   {"type": "bar", "title": "Top Products", "data": [{"label": "Product A", "value": 100}]}
   ```
5. Your final response must be a JSON object with exactly two fields:
    {"message": "your answer in markdown", "suggestions": ["a relevant follow-up question"]}
    The message field contains the complete answer, including any chart block. The suggestions field
    contains 2-3 concise questions that naturally follow from the user's previous message and your answer.
    Return only the JSON object, without a markdown fence or other text.
   """


def build_contents(messages: Sequence[ChatMessage]) -> list[types.Content]:
    contents: list[types.Content] = []
    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
    return contents


def generate_with_fallback(
    client: genai.Client,
    contents: Sequence[types.Content],
    config: types.GenerateContentConfig,
) -> types.GenerateContentResponse:
    """Attempts generation with primary model, falling back if experiencing 503 capacity spikes."""
    candidate_models = (
        os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
        *FALLBACK_MODELS,
    )
    unique_models = list(dict.fromkeys(candidate_models))
    last_error = None

    for model_name in unique_models:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as exc:  # pragma: no branch - provider-specific retries
            err_str = str(exc)
            if "503" in err_str or "404" in err_str:
                last_error = exc
                continue
            raise
    if last_error:
        raise last_error

    raise RuntimeError("No Gemini model could be reached for this request.")


def execute_tool_calls(response: types.GenerateContentResponse) -> list[types.Content]:
    tool_history: list[types.Content] = []
    if response.candidates and response.candidates[0].content:
        tool_history.append(response.candidates[0].content)

    for call in response.function_calls or []:
        fn_name = call.name
        fn_args = call.args or {}
        result_str = TOOL_MAP[fn_name](**fn_args) if fn_name in TOOL_MAP else json.dumps({"error": f"Unknown tool {fn_name}"})
        tool_history.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result_str},
                    )
                ],
            )
        )
    return tool_history


def parse_agent_response(response_text: str) -> dict[str, object]:
    """Normalize the model's structured response while preserving a useful fallback."""
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        return {"message": response_text, "suggestions": []}

    if not isinstance(parsed, dict) or not isinstance(parsed.get("message"), str):
        return {"message": response_text, "suggestions": []}

    suggestions = parsed.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []

    return {
        "message": parsed["message"],
        "suggestions": [item for item in suggestions if isinstance(item, str) and item.strip()],
    }


def run_agentic_loop(messages: list[ChatMessage]) -> dict[str, object]:
    """Executes the loop: User Prompt -> Gemini -> Tool Execution -> Loop -> Final Answer."""
    client = get_client()
    contents = build_contents(messages)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=0.2,
    )

    for _ in range(MAX_AGENT_TURNS):
        response = generate_with_fallback(
            client=client,
            contents=contents,
            config=config,
        )

        if response.function_calls:
            contents.extend(execute_tool_calls(response))
            continue

        if response.text:
            return parse_agent_response(response.text)

    return {
        "message": "Reached maximum turn limit without completing analysis.",
        "suggestions": [],
    }
