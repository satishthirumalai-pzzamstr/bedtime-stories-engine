import os
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
TABLE = "subscribers"


def _headers() -> dict:
    return {
        "apikey": os.environ["SUPABASE_KEY"],
        "Authorization": f"Bearer {os.environ['SUPABASE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url() -> str:
    return f"{os.environ['SUPABASE_URL']}/rest/v1/{TABLE}"


def get_active_subscribers() -> list[dict]:
    resp = requests.get(
        f"{_rest_url()}?status=in.(trial,active)",
        headers=_headers(),
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Supabase error {resp.status_code}: {resp.text}")
    rows = resp.json()
    return [{"id": r["id"], "fields": r} for r in rows]


def update_subscriber(record_id: str, fields: dict) -> None:
    resp = requests.patch(
        f"{_rest_url()}?id=eq.{record_id}",
        headers=_headers(),
        json=fields,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Supabase error {resp.status_code}: {resp.text}")
