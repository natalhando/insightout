import json
import math
import re
from dataclasses import dataclass
from numbers import Real
from typing import Literal

from app.agent.loop import (
    ActivityCallback,
    AgentTrace,
    ChatMessage,
    ChatResult,
    run_agentic_loop,
)

CHART_PATTERN = re.compile(r"```chart\s*(\{.*?\})\s*```", re.DOTALL)
DATA_QUESTION_TERMS = (
    "how many",
    "revenue",
    "sales",
    "users",
    "orders",
    "purchases",
    "conversion",
    "product",
    "top",
    "compare",
    "average",
    "trend",
)
REPAIR_PROMPT = """Your previous response failed a quality check: {issues}
Re-run the analysis as needed and return only the required JSON response. Use a read-only SQL query when the answer depends on data, and do not make claims unsupported by the tool results."""
QualityIssueCode = Literal[
    "empty_answer",
    "suggestion_count",
    "tool_error",
    "missing_query",
    "invalid_chart_json",
    "unsupported_chart",
    "invalid_chart_data",
]


@dataclass
class QualityIssue:
    code: QualityIssueCode
    message: str


@dataclass
class QualityReport:
    issues: list[QualityIssue]

    @property
    def passed(self) -> bool:
        return not self.issues


USER_FACING_FAILURES: dict[QualityIssueCode, str] = {
    "tool_error": "It seems I don't have the right tools to answer that question right now. Is there anything else I can help you with?",
    "missing_query": "I couldn't verify an answer from the available data. Could you try asking about a metric, product, customer, or trend?",
    "empty_answer": "I wasn't able to produce an answer this time. Please try asking again.",
    "suggestion_count": "I couldn't finish formatting that answer. Please try asking again.",
    "invalid_chart_json": "I couldn't format the visual for that answer. Please try asking again.",
    "unsupported_chart": "I couldn't create a supported visual for that answer. Please try asking again.",
    "invalid_chart_data": "I couldn't validate the visual data for that answer. Please try asking again.",
}


def _failure_message(report: QualityReport) -> str:
    for issue in report.issues:
        message = USER_FACING_FAILURES.get(issue.code)
        if message:
            return message
    return "I wasn't able to verify that answer. Please try asking again."


def _validate_chart_payload(chart: object) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    if not isinstance(chart, dict) or chart.get("type") != "bar":
        return [QualityIssue("unsupported_chart", "Only bar charts are supported.")]
    if not isinstance(chart.get("title"), str) or not chart["title"].strip():
        issues.append(QualityIssue("invalid_chart_data", "A chart must contain a non-empty title."))
    data = chart.get("data")
    if not isinstance(data, list) or not data:
        return issues + [QualityIssue("invalid_chart_data", "A chart must contain at least one data item.")]
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("label"), str)
        or not isinstance(item.get("value"), Real)
        or isinstance(item.get("value"), bool)
        or not math.isfinite(item["value"])
        for item in data
    ):
        issues.append(QualityIssue("invalid_chart_data", "Chart items need string labels and finite numeric values."))
    return issues


def _validate_chart(message: str) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for match in CHART_PATTERN.finditer(message):
        try:
            chart = json.loads(match.group(1))
        except json.JSONDecodeError:
            issues.append(QualityIssue("invalid_chart_json", "The chart block is not valid JSON."))
            continue

        issues.extend(_validate_chart_payload(chart))
    return issues


def _tool_call_failed(result: str) -> bool:
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, dict) and isinstance(parsed.get("error"), str)


def validate_answer(question: str, answer: ChatResult, trace: AgentTrace) -> QualityReport:
    issues: list[QualityIssue] = []
    message = answer.get("message", "")
    suggestions = answer.get("suggestions", [])

    if not isinstance(message, str) or not message.strip():
        issues.append(QualityIssue("empty_answer", "The answer must contain a non-empty message."))
    if not isinstance(suggestions, list) or len(suggestions) > 3:
        issues.append(QualityIssue("suggestion_count", "The answer may contain up to three suggestions."))
    if any(_tool_call_failed(call.result) for call in trace.tool_calls):
        issues.append(QualityIssue("tool_error", "The answer was based on a failed tool call."))

    normalized_question = question.lower()
    requires_query = any(term in normalized_question for term in DATA_QUESTION_TERMS)
    used_query = any(call.name == "execute_sql_query" for call in trace.tool_calls)
    if requires_query and not used_query:
        issues.append(QualityIssue("missing_query", "A data answer must be supported by an SQL query."))

    issues.extend(_validate_chart(message))
    return QualityReport(issues)


def run_with_quality_harness(
    messages: list[ChatMessage],
    on_activity: ActivityCallback | None = None,
    max_attempts: int = 2,
) -> ChatResult:
    """Run the agent behind deterministic quality gates and one bounded repair loop."""
    if not messages:
        raise ValueError("At least one message is required.")

    question = messages[-1].content
    current_messages = list(messages)
    last_report = QualityReport([])

    for attempt in range(max_attempts):
        trace = AgentTrace()
        answer = run_agentic_loop(current_messages, on_activity, trace)
        last_report = validate_answer(question, answer, trace)
        if last_report.passed:
            return answer
        if attempt + 1 < max_attempts:
            issue_text = "; ".join(issue.message for issue in last_report.issues)
            current_messages.append(ChatMessage(role="user", content=REPAIR_PROMPT.format(issues=issue_text)))

    return {
        "message": _failure_message(last_report),
        "suggestions": [],
    }