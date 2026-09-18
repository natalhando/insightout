import asyncio
import json
from queue import Queue

import pytest
from app import main
from pydantic import ValidationError


def test_chat_request_validates_messages_and_rejects_extra_fields():
    request = main.ChatRequest(messages=[{"role": "user", "content": "hello"}])

    assert request.messages[0].content == "hello"
    with pytest.raises(ValidationError):
        main.ChatRequest(messages=[], unexpected=True)


def test_run_chat_request_emits_statuses_and_result(monkeypatch):
    def fake_agent(messages, on_activity):
        on_activity("thinking")
        return {"message": "Answer", "suggestions": ["Next"]}

    monkeypatch.setattr(main, "run_agentic_loop", fake_agent)
    events = Queue()

    main.run_chat_request([], events)

    assert events.get_nowait() == {"type": "status", "code": "thinking"}
    assert events.get_nowait() == {
        "type": "result",
        "message": "Answer",
        "suggestions": ["Next"],
    }


@pytest.mark.parametrize(
    "error, expected",
    [
        (ValueError("bad input"), "bad input"),
        (TypeError("bad type"), "bad type"),
        (RuntimeError("provider failed"), "Unable to process chat request"),
    ],
)
def test_run_chat_request_translates_expected_errors(monkeypatch, error, expected):
    def failing_agent(messages, on_activity):
        raise error

    monkeypatch.setattr(main, "run_agentic_loop", failing_agent)
    events = Queue()

    main.run_chat_request([], events)

    assert events.get_nowait() == {"type": "error", "message": expected}


def test_format_sse_serializes_event_with_expected_framing():
    event = {"type": "result", "message": "Done", "suggestions": []}

    assert main.format_sse(event) == f"data: {json.dumps(event)}\n\n"


def test_stream_chat_events_yields_until_terminal_event(monkeypatch):
    monkeypatch.setattr(
        main,
        "run_chat_request",
        lambda messages, events: events.put({"type": "result", "message": "Done", "suggestions": []}),
    )

    async def collect():
        return [event async for event in main.stream_chat_events([])]

    assert asyncio.run(collect()) == ['data: {"type": "result", "message": "Done", "suggestions": []}\n\n']