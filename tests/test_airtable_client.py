import os
import pytest
from unittest.mock import patch, MagicMock
from airtable_client import get_active_subscribers, update_subscriber

@patch.dict("os.environ", {"AIRTABLE_API_KEY": "test_key", "AIRTABLE_BASE_ID": "test_base"})
@patch("airtable_client.Table")
def test_get_active_subscribers_returns_trial_and_active(mock_table_cls):
    mock_table = MagicMock()
    mock_table_cls.return_value = mock_table
    mock_table.all.return_value = [
        {"id": "rec1", "fields": {"email": "a@a.com", "status": "trial", "days_active": 3}},
        {"id": "rec2", "fields": {"email": "b@b.com", "status": "active", "days_active": 20}},
        {"id": "rec3", "fields": {"email": "c@c.com", "status": "paused", "days_active": 8}},
    ]
    result = get_active_subscribers()
    assert len(result) == 2
    assert all(r["fields"]["status"] in ("trial", "active") for r in result)

@patch.dict("os.environ", {"AIRTABLE_API_KEY": "test_key", "AIRTABLE_BASE_ID": "test_base"})
@patch("airtable_client.Table")
def test_update_subscriber_calls_update(mock_table_cls):
    mock_table = MagicMock()
    mock_table_cls.return_value = mock_table
    update_subscriber("rec1", {"status": "paused"})
    mock_table.update.assert_called_once_with("rec1", {"status": "paused"})
