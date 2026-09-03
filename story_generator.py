import json
import logging
import anthropic
from prompt import SYSTEM_PROMPT

log = logging.getLogger(__name__)

AGE_BAND_WORDS = {
    (3, 4): (250, 350),
    (5, 6): (400, 600),
    (7, 8): (700, 900),
}

def _age_band(age: int) -> tuple[int, int]:
    for (lo, hi), bounds in AGE_BAND_WORDS.items():
        if lo <= age <= hi:
            return bounds
    return (250, 900)  # fallback

def _validate(story: dict, age: int) -> bool:
    text = story.get("story", "")
    if not text:
        return False
    word_count = len(text.split())
    lo, hi = _age_band(age)
    return lo <= word_count <= hi

def _validation_detail(story: dict, age: int) -> str:
    text = story.get("story", "")
    if not text:
        return 'the "story" field was empty'
    word_count = len(text.split())
    lo, hi = _age_band(age)
    return f"the story was {word_count} words; it must be between {lo} and {hi} words for this age"

def generate_story(profile: dict) -> dict:
    client = anthropic.Anthropic()
    age = profile.get("age", 6)
    messages = [{"role": "user", "content": json.dumps(profile)}]
    for attempt in range(2):
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        raw = next(b.text for b in response.content if hasattr(b, "text"))
        try:
            story = json.loads(raw)
        except json.JSONDecodeError:
            log.warning(f"generate_story attempt {attempt + 1}: invalid JSON: {raw[:200]!r}")
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": "That was not valid JSON. Return ONLY the JSON object "
                 "described in the instructions - no markdown fences, no preamble, no trailing text."},
            ]
            continue
        if _validate(story, age):
            return story
        detail = _validation_detail(story, age)
        log.warning(f"generate_story attempt {attempt + 1}: {detail}")
        messages += [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": f"That story didn't meet the requirements: {detail}. "
             "Rewrite the full story to fix this and return the complete JSON object again."},
        ]
    raise RuntimeError("Story generation failed after 2 attempts")
