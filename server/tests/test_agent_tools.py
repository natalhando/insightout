from app.agent.tools import (
    MAX_RESULT_ROWS,
    BigQueryRepository,
    _execute_sql_query,
    execute_sql_query,
    get_ga4_schema,
)
from fixtures import FakeBigQueryClient, decode


def test_rejects_non_read_queries_and_multiple_statements_without_calling_bigquery():
    client = FakeBigQueryClient()
    repository = BigQueryRepository(client)

    assert decode(repository.execute_read_query("UPDATE users SET name = 'x'")) == {
        "error": "Only SELECT queries are allowed."
    }
    assert decode(repository.execute_read_query("SELECT 1; DROP TABLE users")) == {
        "error": "Only SELECT queries are allowed."
    }
    assert client.queries == []


def test_allows_write_words_inside_quoted_sql_text():
    client = FakeBigQueryClient(rows=[{"value": 1}])
    repository = BigQueryRepository(client)

    result = decode(repository.execute_read_query("SELECT 'update' AS value;"))

    assert result == {"data": [{"value": 1}], "row_count": 1}
    assert client.queries == ["SELECT 'update' AS value;"]


def test_accepts_with_queries_and_caps_result_rows():
    client = FakeBigQueryClient(rows=[{"id": index} for index in range(MAX_RESULT_ROWS + 10)])
    repository = BigQueryRepository(client)

    result = decode(repository.execute_read_query("  WITH rows AS (SELECT 1) SELECT * FROM rows  "))

    assert result["row_count"] == MAX_RESULT_ROWS
    assert len(result["data"]) == MAX_RESULT_ROWS
    assert client.queries == ["WITH rows AS (SELECT 1) SELECT * FROM rows"]


def test_returns_expected_errors_for_client_failures():
    type_error_result = decode(BigQueryRepository(FakeBigQueryClient(error=TypeError("bad query"))).execute_read_query("SELECT 1"))
    runtime_error_result = decode(
        BigQueryRepository(FakeBigQueryClient(error=RuntimeError("service down"))).execute_read_query("SELECT 1")
    )

    assert type_error_result == {"error": "bad query"}
    assert runtime_error_result == {"error": "BigQuery query failed."}


def test_schema_and_tool_wrappers_return_json_and_forward_repository():
    schema = decode(get_ga4_schema())
    client = FakeBigQueryClient(rows=[{"count": 2}])
    repository = BigQueryRepository(client)

    assert schema["dataset"] == "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*"
    assert decode(_execute_sql_query("SELECT COUNT(*) AS count", repository)) == {
        "data": [{"count": 2}],
        "row_count": 1,
    }
    assert callable(execute_sql_query)