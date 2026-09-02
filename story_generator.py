import json
import anthropic
from prompt import SYSTEM_PROMPT

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

def generate_story(profile: dict) -> dict:
    client = anthropic.Anthropic()
    age = profile.get("age", 6)
    for attempt in range(2):
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(profile)}],
        )
        raw = next(b.text for b in response.content if hasattr(b, "text"))
        try:
            story = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if _validate(story, age):
            return story
    raise RuntimeError("Story generation failed after 2 attempts")
