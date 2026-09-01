import pytest
from unittest.mock import patch, MagicMock
from brevo_client import send_story_email, send_paywall_email

STORY = {
    "title": "The Lighthouse Keeper",
    "subject": "Tonight's story for Maya: The Lighthouse Keeper",
    "preheader": "A small snail finds her light.",
    "reading_time_minutes": 3,
    "story": "Once there was a snail.",
    "closing_line": "Sleep well, Maya.",
    "parent_note": "About finding your place.",
}

@patch("brevo_client.requests.post")
@patch.dict("os.environ", {"BREVO_API_KEY": "test-key"})
def test_send_story_email_posts_to_brevo(mock_post):
    mock_post.return_value.status_code = 201
    send_story_email("parent@example.com", "Maya", STORY)
    assert mock_post.called
    call_json = mock_post.call_args.kwargs["json"]
    assert call_json["to"][0]["email"] == "parent@example.com"
    assert "Maya" in call_json["subject"] or "Tonight" in call_json["subject"]

@patch("brevo_client.requests.post")
@patch.dict("os.environ", {"BREVO_API_KEY": "test-key"})
def test_send_paywall_email_posts_to_brevo(mock_post):
    mock_post.return_value.status_code = 201
    send_paywall_email("parent@example.com", "Maya", "https://buy.stripe.com/test")
    assert mock_post.called
    call_json = mock_post.call_args.kwargs["json"]
    assert "stripe" in call_json["htmlContent"].lower() or \
           "buy.stripe.com" in call_json["htmlContent"]

@patch("brevo_client.requests.post")
@patch.dict("os.environ", {"BREVO_API_KEY": "test-key"})
def test_send_story_email_raises_on_error(mock_post):
    mock_post.return_value.status_code = 400
    mock_post.return_value.text = "Bad Request"
    with pytest.raises(RuntimeError, match="Brevo error"):
        send_story_email("parent@example.com", "Maya", STORY)
