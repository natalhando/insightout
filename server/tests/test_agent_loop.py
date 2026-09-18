import json

import pytest
from google.genai import types

from app.agent import loop
from fixtures import FakeClient, FakeModels, message, response


def test_chat_message_forbids_extra_fields():
    with pytest.raises(ValueError):
        loop.ChatMessage(role="user", content="hello", extra="rejected")


def test_get_client_requires_api_key_and_caches_created_client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    loop._client = None

    with pytest.raises(ValueError, match="GEMINI_API_KEY is not set"):
        loop.get_client()

    created = object()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(loop.genai, "Client", lambda api_key: created)
    loop._client = None

    assert loop.get_client() is created
    assert loop.get_client() is created


def test_build_contents_maps_roles_and_text():
    contents = loop.build_contents([message(), message("model", "A result")])

    assert [content.role for content in contents] == ["user", "model"]
    assert [content.parts[0].text for content in contents] == ["How many users?", "A result"]


def test_generate_with_fallback_deduplicates_models_and_retries_capacity_errors(monkeypatch):
    models = FakeModels(
        responses=[response(text="ok")],
        errors=[RuntimeError("503 capacity"), RuntimeError("404 model"), None],
    )
    client = FakeClient(models)
    monkeypatch.setenv("GEMINI_MODEL", "primary")

    result = loop.generate_with_fallback(client, [], types.GenerateContentConfig())

    assert result.text == "ok"
    assert [call["model"] for call in models.calls] == ["primary", *loop.FALLBACK_MODELS]


def test_generate_with_fallback_does_not_hide_non_retryable_errors():
    models = FakeModels(errors=[RuntimeError("400 invalid request")])

    with pytest.raises(RuntimeError, match="400 invalid request"):
        loop.generate_with_fallback(FakeClient(models), [], types.GenerateContentConfig())


def test_execute_tool_calls_emits_specific_activity_and_unknown_tool_error(monkeypatch):
    calls = []
    monkeypatch.setitem(loop.TOOL_MAP, "get_ga4_schema", lambda: "schema result")
    function_calls = [
        types.FunctionCall(name="get_ga4_schema", args={}),
        types.FunctionCall(name="missing_tool", args={}),
    ]

    history = loop.execute_tool_calls(response(function_calls=function_calls), calls.append)

    assert calls == ["schema", "tool"]
    assert len(history) == 3
    assert history[1].parts[0].function_response.response == {"result": "schema result"}
    assert history[2].parts[0].function_response.response == {"result": json.dumps({"error": "Unknown tool missing_tool"})}


def test_parse_agent_response_preserves_fallback_and_filters_suggestions():
    assert loop.parse_agent_response("not json") == {"message": "not json", "suggestions": []}
    assert loop.parse_agent_response(json.dumps({"message": "answer", "suggestions": ["next", "", 3]})) == {
        "message": "answer",
        "suggestions": ["next"],
    }
    assert loop.parse_agent_response(json.dumps({"message": "answer", "suggestions": "invalid"})) == {
        "message": "answer",
        "suggestions": [],
    }


def test_run_agentic_loop_executes_tools_then_returns_answer(monkeypatch):
    models = FakeModels(
        responses=[
            response(function_calls=[types.FunctionCall(name="get_ga4_schema", args={})]),
            response(text=json.dumps({"message": "Done", "suggestions": ["More?"]})),
        ]
    )
    monkeypatch.setattr(loop, "get_client", lambda: FakeClient(models))
    monkeypatch.setitem(loop.TOOL_MAP, "get_ga4_schema", lambda: "schema")
    activities = []

    result = loop.run_agentic_loop([message()], activities.append)

    assert result == {"message": "Done", "suggestions": ["More?"]}
    assert activities == ["thinking", "schema", "reviewing", "answer"]
    assert len(models.calls) == 2


def test_run_agentic_loop_returns_limit_error_when_model_never_answers(monkeypatch):
    models = FakeModels(responses=[response(function_calls=[]) for _ in range(loop.MAX_AGENT_TURNS)])
    monkeypatch.setattr(loop, "get_client", lambda: FakeClient(models))

    result = loop.run_agentic_loop([message()])

    assert result == {
        "message": "Reached maximum turn limit without completing analysis.",
        "suggestions": [],
    }
    assert len(models.calls) == loop.MAX_AGENT_TURNS