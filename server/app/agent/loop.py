import json
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal, TypedDict

from app.agent.tools import TOOL_MAP, TOOLS
from dotenv import find_dotenv, load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict

load_dotenv(find_dotenv())

_client = None
MAX_AGENT_TURNS = 8
FALLBACK_MODELS = ("gemini-3.5-flash", "gemini-3.6-flash")
DEFAULT_MODEL = "gemini-3.5-flash-lite"
AGENT_TEMPERATURE = 0.2
ActivityCode = Literal["thinking", "reviewing", "schema", "query", "tool", "answer"]
ActivityCallback = Callable[[ActivityCode], None]
TerminationReason = Literal["answer", "max_turns"]


@dataclass
class ToolCallTrace:
    name: str
    args: dict[str, object]
    result: str


@dataclass
class AgentTrace:
    turns: int = 0
    model_attempts: list[str] = field(default_factory=list)
    activities: list[ActivityCode] = field(default_factory=list)
    tool_calls: list[ToolCallTrace] = field(default_factory=list)
    termination_reason: TerminationReason | None = None


class ChatResult(TypedDict):
    message: str
    suggestions: list[str]


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
You are InsightOut, an expert e-commerce analytics AI assistant.
Your job is to answer user questions using Google Analytics 4 (GA4) BigQuery data.
Provide a complete analysis with clear reasoning, relevant visuals when useful, and a concise narrative that explains the findings.

Operating rules:
1. When a question requires it, check the schema using `get_ga4_schema`.
2. Formulate and execute standard BigQuery SQL queries with `execute_sql_query`.
3. Analyze the output and present a clear, conversational answer grounded in the data.
4. Prefer the smallest reliable query that answers the user's question.

Charting rules:
- If a visual helps communicate the main takeaway, return a JSON chart block at the end of your message in this format:
  ```chart
  {"type": "bar", "title": "Top Products", "data": [{"label": "Product A", "value": 100}]}
  ```
- First decide the key insight the user should take away from the data. Only chart when a visual makes that insight easier to compare or spot than a concise sentence.
- This interface supports only vertical bar charts, so use one for discrete comparisons, rankings, or a small number of ordered periods.
- Use a standard Markdown table with a header row for exact values, many categories, or several metrics.
- Use prose for trends over time, composition, or any question that would require another chart type.
- A chart should add insight, not replace exact supporting details.
- Do not chart a single value, noisy or excessively long lists, or raw data without a clear comparison.
- Aggregate and calculate the meaningful metric first when possible, limit the result to the categories that support the takeaway, and state the key insight in the surrounding text.
- Keep labels concise, title the chart with the metric and scope, and ensure every `data` item has a string `label` and numeric `value`.
- Do not return a table and a chart for the same data. Choose the clearer format, or use them together only when they show different data.

Final response contract:
- Your final response must be a JSON object with exactly two fields:
  {"message": "your answer in markdown", "suggestions": ["a relevant follow-up question"]}
- The `message` field contains the complete answer, including any chart block.
- The `suggestions` field contains 2-3 concise questions that naturally follow from the user's previous message and your answer.
- Return only the JSON object, without a markdown fence or any other text.
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
    trace: AgentTrace | None = None,
) -> types.GenerateContentResponse:
    """Attempts generation with primary model, falling back if experiencing 503 capacity spikes."""
    candidate_models = (
        os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
        *FALLBACK_MODELS,
    )
    unique_models = list(dict.fromkeys(candidate_models))
    last_error = None

    for model_name in unique_models:
        if trace is not None:
            trace.model_attempts.append(model_name)
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            err_str = str(exc)
            if "503" in err_str or "404" in err_str:
                last_error = exc
                continue
            raise
    if last_error:
        raise last_error

    raise RuntimeError("No Gemini model could be reached for this request.")


def execute_tool_calls(
    response: types.GenerateContentResponse,
    on_activity: ActivityCallback | None = None,
    trace: AgentTrace | None = None,
) -> list[types.Content]:
    tool_history: list[types.Content] = []
    if response.candidates and response.candidates[0].content:
        tool_history.append(response.candidates[0].content)

    for call in response.function_calls or []:
        fn_name = call.name
        fn_args = call.args or {}
        activity = {
            "get_ga4_schema": "schema",
            "execute_sql_query": "query",
        }.get(fn_name, "tool")
        emit_activity(on_activity, activity, trace)
        result_str = TOOL_MAP[fn_name](**fn_args) if fn_name in TOOL_MAP else json.dumps({"error": f"Unknown tool {fn_name}"})
        if trace is not None:
            trace.tool_calls.append(ToolCallTrace(name=fn_name, args=dict(fn_args), result=result_str))
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


def emit_activity(
    callback: ActivityCallback | None,
    activity: ActivityCode,
    trace: AgentTrace | None = None,
) -> None:
    if trace is not None:
        trace.activities.append(activity)
    if callback is not None:
        callback(activity)


def parse_agent_response(response_text: str) -> ChatResult:
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


def run_agentic_loop(
    messages: list[ChatMessage],
    on_activity: ActivityCallback | None = None,
    trace: AgentTrace | None = None,
) -> ChatResult:
    """Executes the loop: User Prompt -> Gemini -> Tool Execution -> Loop -> Final Answer."""
    client = get_client()
    contents = build_contents(messages)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=AGENT_TEMPERATURE,
    )

    for turn in range(MAX_AGENT_TURNS):
        if trace is not None:
            trace.turns = turn + 1
        emit_activity(on_activity, "thinking" if turn == 0 else "reviewing", trace)
        response = generate_with_fallback(
            client=client,
            contents=contents,
            config=config,
            trace=trace,
        )

        if response.function_calls:
            contents.extend(execute_tool_calls(response, on_activity, trace))
            continue

        if response.text:
            if trace is not None:
                trace.termination_reason = "answer"
            emit_activity(on_activity, "answer", trace)
            return parse_agent_response(response.text)

    if trace is not None:
        trace.termination_reason = "max_turns"
    return {
        "message": "Reached maximum turn limit without completing analysis.",
        "suggestions": [],
    }
