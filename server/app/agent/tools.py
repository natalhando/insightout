import json
import logging
import os
import re
from itertools import islice

from google.cloud import bigquery

logger = logging.getLogger(__name__)

KEY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "gcp-key.json"))
GA4_DATASET = "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*"
MAX_RESULT_ROWS = 50
READ_QUERY_START = re.compile(r"^(?:SELECT|WITH)\b", re.IGNORECASE)
QUOTED_SQL_TEXT = re.compile(r"'(?:''|\\.|[^'])*'|\"(?:\\.|[^\"])*\"|`[^`]*`")
WRITE_KEYWORDS = re.compile(
    r"\b(?:ALTER|CALL|CREATE|DELETE|DROP|EXPORT|GRANT|INSERT|MERGE|REVOKE|TRUNCATE|UPDATE)\b",
    re.IGNORECASE,
)


def get_bigquery_client() -> bigquery.Client:
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ and os.path.exists(KEY_PATH):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
    project_id = os.environ.get("BIGQUERY_PROJECT_ID")
    return bigquery.Client(project=project_id) if project_id else bigquery.Client()


class BigQueryRepository:
    def __init__(self, client: bigquery.Client | None = None):
        self.client = client or get_bigquery_client()

    def execute_read_query(self, sql_query: str) -> str:
        normalized_query = sql_query.strip()
        query_without_trailing_semicolon = normalized_query[:-1].rstrip() if normalized_query.endswith(";") else normalized_query
        has_multiple_statements = ";" in query_without_trailing_semicolon
        query_without_quoted_text = QUOTED_SQL_TEXT.sub(" ", query_without_trailing_semicolon)

        if (
            not READ_QUERY_START.match(normalized_query)
            or has_multiple_statements
            or WRITE_KEYWORDS.search(query_without_quoted_text)
        ):
            return json.dumps({"error": "Only SELECT queries are allowed."})

        try:
            query_job = self.client.query(normalized_query)
            rows = [dict(row) for row in islice(query_job.result(), MAX_RESULT_ROWS)]
            return json.dumps({"data": rows, "row_count": len(rows)})
        except (TypeError, ValueError) as exc:
            return json.dumps({"error": str(exc)})
        except Exception:
            logger.exception("BigQuery query failed")
            return json.dumps({"error": "BigQuery query failed."})


def get_ga4_schema() -> str:
    schema_info = {
        "dataset": GA4_DATASET,
        "common_fields": [
            "event_date (STRING)",
            "event_name (STRING: page_view, purchase, add_to_cart, etc.)",
            "event_timestamp (INTEGER)",
            "user_pseudo_id (STRING: unique identifier for users)",
            "geo.country (STRING)",
            "traffic_source.medium (STRING)",
            "traffic_source.source (STRING)",
            "device.category (STRING: desktop, mobile, tablet)",
            "event_params (RECORD array with keys and values)",
            "items (RECORD array containing item_id, item_name, price, quantity, item_revenue)",
        ],
        "date_range": "2020-11-01 to 2021-01-31",
    }
    return json.dumps(schema_info)


def _execute_sql_query(sql_query: str, repository: BigQueryRepository | None = None) -> str:
    repo = repository or BigQueryRepository()
    return repo.execute_read_query(sql_query)


def execute_sql_query(sql_query: str) -> str:
    return _execute_sql_query(sql_query)


TOOL_MAP = {
    "get_ga4_schema": get_ga4_schema,
    "execute_sql_query": execute_sql_query,
}
TOOLS = list(TOOL_MAP.values())