import json
import logging
import os
from itertools import islice

from google.cloud import bigquery

logger = logging.getLogger(__name__)

# Force Python to point to the key inside the server directory when it is needed.
KEY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "gcp-key.json")
GA4_DATASET = "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*"
GA4_TABLE = f"`{GA4_DATASET}`"
MAX_RESULT_ROWS = 50

_bq_client = None


def get_bigquery_client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", os.path.abspath(KEY_PATH))
        _bq_client = bigquery.Client()
    return _bq_client


bq_client = get_bigquery_client()


class BigQueryRepository:
    def __init__(self, client: bigquery.Client | None = None):
        self.client = client or get_bigquery_client()

    def execute_read_query(self, sql_query: str) -> str:
        if not sql_query.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "Only SELECT queries are allowed."})

        try:
            query_job = self.client.query(sql_query)
            results = query_job.result()
            rows = [dict(row) for row in islice(results, MAX_RESULT_ROWS)]
            return json.dumps({"data": rows, "row_count": len(rows)})
        except (TypeError, ValueError) as exc:
            return json.dumps({"error": str(exc)})
        except Exception as exc:  # pragma: no cover - logging boundary for operational failures
            logger.exception("BigQuery query failed")
            return json.dumps({"error": str(exc)})


def get_ga4_schema() -> str:
    """Returns the main schema fields and description for the BigQuery GA4 e-commerce dataset.
    Call this first to understand how to write SQL queries for the user.
    """
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


def execute_sql_query(sql_query: str, repository: BigQueryRepository | None = None) -> str:
    """Executes a read-only SQL query against BigQuery and returns up to 50 rows of results as JSON."""
    if repository is None:
        repo = BigQueryRepository(client=bq_client)
    else:
        repo = repository
    return repo.execute_read_query(sql_query)


# List of tools to pass to Gemini
TOOLS = [get_ga4_schema, execute_sql_query]
# Dictionary map for string execution lookup
TOOL_MAP = {
    "get_ga4_schema": get_ga4_schema,
    "execute_sql_query": execute_sql_query,
}