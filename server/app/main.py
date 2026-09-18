import asyncio
import json
import logging
from collections.abc import AsyncIterator
from queue import Queue
from typing import Literal, TypedDict

from app.agent.loop import ActivityCode, ChatMessage, ChatResult, run_agentic_loop
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, ValidationError

logger = logging.getLogger(__name__)

# Automatically locate and load the server/.env file
load_dotenv(find_dotenv())

app = FastAPI(title="InsightOut API")

# Allow Vite React Dev Server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[ChatMessage]


class StatusEvent(TypedDict):
    type: Literal["status"]
    code: ActivityCode


class ResultEvent(ChatResult):
    type: Literal["result"]


class ErrorEvent(TypedDict):
    type: Literal["error"]
    message: str


StreamEvent = StatusEvent | ResultEvent | ErrorEvent


def run_chat_request(messages: list[ChatMessage], events: Queue[StreamEvent]) -> None:
    def on_activity(activity: ActivityCode) -> None:
        events.put({"type": "status", "code": activity})

    try:
        result = run_agentic_loop(messages, on_activity)
        events.put({"type": "result", **result})
    except (TypeError, ValueError, ValidationError) as exc:
        events.put({"type": "error", "message": str(exc)})
    except Exception:
        logger.exception("Chat request failed")
        events.put({"type": "error", "message": "Unable to process chat request"})


def format_sse(event: StreamEvent) -> str:
    return f"data: {json.dumps(event)}\n\n"


async def stream_chat_events(messages: list[ChatMessage]) -> AsyncIterator[str]:
    events: Queue[StreamEvent] = Queue()
    task = asyncio.create_task(asyncio.to_thread(run_chat_request, messages, events))
    while True:
        event = await asyncio.to_thread(events.get)
        yield format_sse(event)
        if event["type"] in {"result", "error"}:
            break
    await task


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(stream_chat_events(request.messages), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)