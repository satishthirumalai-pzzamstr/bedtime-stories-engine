import json
import pytest
from unittest.mock import patch, MagicMock
from story_generator import generate_story, _validate

VALID_STORY = {
    "title": "The Lighthouse Keeper's Lantern",
    "subject": "Tonight's story for Maya: The Lighthouse Keeper's Lantern",
    "preheader": "A small snail finds her light.",
    "reading_time_minutes": 3,
    "story": " ".join(["word"] * 450),  # 450 words — valid for age 6
    "closing_line": "Sleep well, Maya.",
    "parent_note": "About finding your place in a new room.",
    "archetype_used": "The Quiet Invitation",
    "setting_used": "lighthouse",
    "character_type": "snail",
    "interests_used": ["trains"],
}

def test_validate_passes_for_valid_story():
    assert _validate(VALID_STORY, age=6) is True

def test_validate_fails_for_missing_story_field():
    bad = {**VALID_STORY, "story": ""}
    assert _validate(bad, age=6) is False

def test_validate_fails_for_word_count_out_of_band():
    bad = {**VALID_STORY, "story": "too short"}
    assert _validate(bad, age=6) is False

@patch("story_generator.anthropic.Anthropic")
def test_generate_story_returns_parsed_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value.content = [
        MagicMock(text=json.dumps(VALID_STORY))
    ]
    profile = {"child_name": "Maya", "age": 6, "recent_stories": []}
    result = generate_story(profile)
    assert result["title"] == VALID_STORY["title"]
    assert mock_client.messages.create.call_args.kwargs["model"] == "claude-sonnet-5"

@patch("story_generator.anthropic.Anthropic")
def test_generate_story_retries_once_on_invalid(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    bad_response = MagicMock(text="not json at all")
    good_response = MagicMock(text=json.dumps(VALID_STORY))
    mock_client.messages.create.side_effect = [
        MagicMock(content=[bad_response]),
        MagicMock(content=[good_response]),
    ]
    profile = {"child_name": "Maya", "age": 6, "recent_stories": []}
    result = generate_story(profile)
    assert mock_client.messages.create.call_count == 2
    assert result["title"] == VALID_STORY["title"]

@patch("story_generator.anthropic.Anthropic")
def test_generate_story_retry_includes_validation_feedback(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    short_story = {**VALID_STORY, "story": " ".join(["word"] * 50)}  # too short for age 6
    bad_response = MagicMock(text=json.dumps(short_story))
    good_response = MagicMock(text=json.dumps(VALID_STORY))
    mock_client.messages.create.side_effect = [
        MagicMock(content=[bad_response]),
        MagicMock(content=[good_response]),
    ]
    profile = {"child_name": "Maya", "age": 6, "recent_stories": []}
    result = generate_story(profile)
    assert result["title"] == VALID_STORY["title"]
    second_call_messages = mock_client.messages.create.call_args_list[1].kwargs["messages"]
    feedback = second_call_messages[-1]["content"]
    assert "50 words" in feedback
    assert "400" in feedback and "600" in feedback

@patch("story_generator.anthropic.Anthropic")
def test_generate_story_raises_after_two_failures(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value.content = [
        MagicMock(text="not json")
    ]
    profile = {"child_name": "Maya", "age": 6, "recent_stories": []}
    with pytest.raises(RuntimeError, match="Story generation failed"):
        generate_story(profile)
    assert mock_client.messages.create.call_count == 2
