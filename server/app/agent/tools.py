# server/app/agent/tools.py
import os
import json
from google.cloud import bigquery

# Force Python to point to the key inside the server directory
KEY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "gcp-key.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(KEY_PATH)

# Initialize public BigQuery client
bq_client = bigquery.Client()

GA4_TABLE = "`bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`"

def get_ga4_schema() -> str:
    """Returns the main schema fields and description for the BigQuery GA4 e-commerce dataset.
    Call this first to understand how to write SQL queries for the user.
    """
    schema_info = {
        "dataset": "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*",
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
            "items (RECORD array containing item_id, item_name, price, quantity, item_revenue)"
        ],
        "date_range": "2020-11-01 to 2021-01-31"
    }
    return json.dumps(schema_info)


def execute_sql_query(sql_query: str) -> str:
    """Executes a Read-Only SQL query against BigQuery and returns up to 50 rows of results as JSON.
    Args:
        sql_query: A valid BigQuery SQL SELECT statement querying bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*.
    """
    try:
        # Enforce safety limits
        if not sql_query.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "Only SELECT queries are allowed."})

        query_job = bq_client.query(sql_query)
        results = query_job.result()

        # Convert rows to serializable dicts (limit to 50 rows)
        rows = [dict(row) for row in list(results)[:50]]
        return json.dumps({"data": rows, "row_count": len(rows)})
    except Exception as e:
        return json.dumps({"error": str(e)})


# List of tools to pass to Gemini
TOOLS = [get_ga4_schema, execute_sql_query]
# Dictionary map for string execution lookup
TOOL_MAP = {
    "get_ga4_schema": get_ga4_schema,
    "execute_sql_query": execute_sql_query
}