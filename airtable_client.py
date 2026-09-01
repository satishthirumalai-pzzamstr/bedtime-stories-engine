import os
from pyairtable import Table

def _table() -> Table:
    return Table(
        os.environ["AIRTABLE_API_KEY"],
        os.environ["AIRTABLE_BASE_ID"],
        "Subscribers",
    )

def get_active_subscribers() -> list[dict]:
    rows = _table().all()
    return [r for r in rows if r["fields"].get("status") in ("trial", "active")]

def update_subscriber(record_id: str, fields: dict) -> None:
    _table().update(record_id, fields)
