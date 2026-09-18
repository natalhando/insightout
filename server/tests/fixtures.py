import json

from app.agent import loop
from google.genai import types


def message(role="user", content="How many users?"):
    return loop.ChatMessage(role=role, content=content)


class FakeModels:
    def __init__(self, responses=None, errors=None):
        self.responses = list(responses or [])
        self.errors = list(errors or [])
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.errors:
            error = self.errors.pop(0)
            if error is not None:
                raise error
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, models):
        self.models = models


def response(text=None, function_calls=None):
    parts = []
    if text is not None:
        parts.append(types.Part.from_text(text=text))
    parts.extend(
        types.Part.from_function_call(name=call.name, args=call.args or {})
        for call in function_calls or []
    )
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(content=types.Content(role="model", parts=parts))
        ],
    )


class FakeQueryJob:
    def __init__(self, rows):
        self.rows = rows

    def result(self):
        return iter(self.rows)


class FakeBigQueryClient:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.queries = []

    def query(self, sql_query):
        self.queries.append(sql_query)
        if self.error:
            raise self.error
        return FakeQueryJob(self.rows)


def decode(result):
    return json.loads(result)