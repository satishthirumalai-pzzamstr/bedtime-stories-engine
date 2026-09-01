import json
import pytest
from unittest.mock import patch, MagicMock, call
from main import run, _build_profile

SUBSCRIBER_TRIAL_DAY3 = {
    "id": "rec1",
    "fields": {
        "email": "parent@example.com",
        "child_name": "Maya",
        "age": 6,
        "pronouns": "she/her",
        "interests": "trains, sea creatures",
        "avoid_topics": "thunderstorms",
        "comfort_object": "Pip",
        "life_theme": "",
        "status": "trial",
        "days_active": 3,
        "story_history": "[]",
    }
}

SUBSCRIBER_TRIAL_DAY7 = {
    "id": "rec2",
    "fields": {**SUBSCRIBER_TRIAL_DAY3["fields"], "days_active": 7, "status": "trial"},
}

STORY = {
    "title": "T", "subject": "S", "preheader": "P", "reading_time_minutes": 3,
    "story": "story text", "closing_line": "CL", "parent_note": "PN",
    "archetype_used": "The Trade", "setting_used": "library", "character_type": "frog",
    "interests_used": ["trains"],
}

def test_build_profile_maps_fields():
    profile = _build_profile(SUBSCRIBER_TRIAL_DAY3)
    assert profile["child_name"] == "Maya"
    assert profile["age"] == 6
    assert profile["recent_stories"] == []
    assert "trains" in profile["interests"]

@patch("main.update_subscriber")
@patch("main.send_story_email")
@patch("main.generate_story", return_value=STORY)
@patch("main.get_active_subscribers", return_value=[SUBSCRIBER_TRIAL_DAY3])
def test_run_sends_story_for_trial_day3(mock_get, mock_gen, mock_send, mock_update):
    run()
    mock_send.assert_called_once()
    # story_history updated
    update_call = mock_update.call_args
    assert update_call[0][0] == "rec1"
    history = json.loads(update_call[0][1]["story_history"])
    assert len(history) == 1
    assert history[0]["archetype"] == "The Trade"

@patch("main.update_subscriber")
@patch("main.send_paywall_email")
@patch("main.send_story_email")
@patch("main.generate_story", return_value=STORY)
@patch("main.get_active_subscribers", return_value=[SUBSCRIBER_TRIAL_DAY7])
def test_run_sends_paywall_on_day7(mock_get, mock_gen, mock_story, mock_paywall, mock_update):
    run()
    mock_story.assert_called_once()
    mock_paywall.assert_called_once()
    update_calls = mock_update.call_args_list
    status_update = next(
        (c for c in update_calls if c[0][1].get("status") == "paused"), None
    )
    assert status_update is not None

@patch("main.update_subscriber")
@patch("main.send_story_email")
@patch("main.generate_story", side_effect=RuntimeError("failed"))
@patch("main.get_active_subscribers", return_value=[SUBSCRIBER_TRIAL_DAY3])
def test_run_continues_on_generation_failure(mock_get, mock_gen, mock_send, mock_update):
    run()
    mock_send.assert_not_called()
