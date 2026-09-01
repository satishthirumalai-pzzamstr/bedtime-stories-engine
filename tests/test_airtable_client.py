import pytest
from unittest.mock import patch, MagicMock
from airtable_client import get_active_subscribers, update_subscriber

ENV = {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}

ROWS = [
    {"id": "uuid-1", "email": "a@a.com", "status": "trial", "days_active": 3},
    {"id": "uuid-2", "email": "b@b.com", "status": "active", "days_active": 20},
    {"id": "uuid-3", "email": "c@c.com", "status": "paused", "days_active": 8},
]

@patch.dict("os.environ", ENV)
@patch("airtable_client.requests.get")
def test_get_active_subscribers_returns_trial_and_active(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [ROWS[0], ROWS[1]]
    result = get_active_subscribers()
    assert len(result) == 2
    assert all(r["fields"]["status"] in ("trial", "active") for r in result)
    assert result[0]["id"] == "uuid-1"

@patch.dict("os.environ", ENV)
@patch("airtable_client.requests.patch")
def test_update_subscriber_calls_patch(mock_patch):
    mock_patch.return_value.status_code = 204
    update_subscriber("uuid-1", {"status": "paused"})
    mock_patch.assert_called_once()
    call_kwargs = mock_patch.call_args
    assert "uuid-1" in call_kwargs[0][0]
    assert call_kwargs[1]["json"] == {"status": "paused"}

@patch.dict("os.environ", ENV)
@patch("airtable_client.requests.get")
def test_get_active_subscribers_raises_on_error(mock_get):
    mock_get.return_value.status_code = 401
    mock_get.return_value.text = "Unauthorized"
    with pytest.raises(RuntimeError, match="Supabase error"):
        get_active_subscribers()
