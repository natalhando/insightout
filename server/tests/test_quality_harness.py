import json

from app.agent import harness
from app.agent.loop import AgentTrace, ChatMessage, ToolCallTrace


def test_validate_answer_requires_query_support_for_data_questions():
    report = harness.validate_answer(
        "How many users?",
        {"message": "There were 100 users.", "suggestions": ["Compare devices?", "Compare dates?"]},
        AgentTrace(),
    )

    assert report.passed is False
    assert [issue.code for issue in report.issues] == ["missing_query"]


def test_validate_answer_allows_a_valid_answer_with_one_clickable_suggestion():
    report = harness.validate_answer(
        "What is the weather?",
        {"message": "The answer is unavailable.", "suggestions": ["Show me an interesting insight"]},
        AgentTrace(),
    )

    assert report.passed is True


def test_validate_answer_rejects_tool_errors_and_invalid_charts():
    trace = AgentTrace(
        tool_calls=[
            ToolCallTrace(
                name="execute_sql_query",
                args={"sql_query": "SELECT 1"},
                result=json.dumps({"error": "BigQuery query failed."}),
            )
        ]
    )
    answer = {
        "message": "```chart\n{\"type\":\"line\",\"data\":[]}\n```",
        "suggestions": ["Try again?", "Compare dates?"],
    }

    report = harness.validate_answer("What is revenue?", answer, trace)

    assert report.passed is False
    assert {issue.code for issue in report.issues} == {"tool_error", "unsupported_chart"}


def test_validate_answer_does_not_accept_data_answer_after_query_error():
    trace = AgentTrace(
        tool_calls=[
            ToolCallTrace(
                "execute_sql_query",
                {"sql_query": "SELECT event_name, COUNT(*) FROM events"},
                '{"error":"BigQuery rejected the query: SELECT list expression references column event_name"}',
            )
        ]
    )

    report = harness.validate_answer(
        "How many events were there?",
        {"message": "There were 100 events.", "suggestions": ["Compare dates?", "Compare devices?"]},
        trace,
    )

    assert report.passed is False
    assert any(issue.code == "tool_error" for issue in report.issues)


def test_quality_harness_returns_human_readable_tool_failure(monkeypatch):
    def failing_agent(messages, on_activity, trace):
        trace.tool_calls.append(ToolCallTrace("execute_sql_query", {"sql_query": "SELECT 1"}, '{"error":"query failed"}'))
        return {"message": "There were 100 users.", "suggestions": ["Compare dates?"]}

    monkeypatch.setattr(harness, "run_agentic_loop", failing_agent)

    result = harness.run_with_quality_harness([ChatMessage(role="user", content="How many users?")])

    assert result["message"] == (
        "It seems I don't have the right tools to answer that question right now. "
        "Is there anything else I can help you with?"
    )
    assert "tool_error" not in result["message"]


def test_quality_harness_repairs_once_before_returning_answer(monkeypatch):
    attempts = []

    def fake_agent(messages, on_activity, trace):
        attempts.append(messages[-1].content)
        if len(attempts) == 1:
            return {"message": "Unsupported answer", "suggestions": ["Only one"]}
        trace.tool_calls.append(ToolCallTrace("execute_sql_query", {"sql_query": "SELECT 1"}, '{"data":[{"value":1}]}'))
        return {"message": "Verified answer", "suggestions": ["Compare dates?", "Compare devices?"]}

    monkeypatch.setattr(harness, "run_agentic_loop", fake_agent)

    result = harness.run_with_quality_harness([ChatMessage(role="user", content="What is revenue?")])

    assert result["message"] == "Verified answer"
    assert len(attempts) == 2
    assert "failed a quality check" in attempts[1]