import json
import re
from dataclasses import dataclass
from numbers import Number

from app.agent.loop import AgentTrace, ChatMessage, ChatResult, run_agentic_loop

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


@dataclass
class QualityIssue:
    code: str
    message: str


@dataclass
class QualityReport:
    issues: list[QualityIssue]

    @property
    def passed(self) -> bool:
        return not self.issues


def _validate_chart(message: str) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    match = CHART_PATTERN.search(message)
    if not match:
        return issues

    try:
        chart = json.loads(match.group(1))
    except json.JSONDecodeError:
        return [QualityIssue("invalid_chart_json", "The chart block is not valid JSON.")]

    if not isinstance(chart, dict) or chart.get("type") != "bar":
        issues.append(QualityIssue("unsupported_chart", "Only bar charts are supported."))
        return issues
    data = chart.get("data")
    if not isinstance(data, list) or not data:
        issues.append(QualityIssue("invalid_chart_data", "A chart must contain at least one data item."))
        return issues
    for item in data:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("label"), str)
            or not isinstance(item.get("value"), Number)
            or isinstance(item.get("value"), bool)
        ):
            issues.append(QualityIssue("invalid_chart_data", "Chart items need string labels and numeric values."))
            break
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
    if not isinstance(suggestions, list) or not 2 <= len(suggestions) <= 3:
        issues.append(QualityIssue("suggestion_count", "The answer must contain two or three suggestions."))
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
    on_activity=None,
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

    issue_codes = ", ".join(issue.code for issue in last_report.issues)
    return {
        "message": f"I couldn't produce a verified answer for this question ({issue_codes}).",
        "suggestions": [],
    }