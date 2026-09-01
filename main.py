import json
import logging
from datetime import date
from airtable_client import get_active_subscribers, update_subscriber
from story_generator import generate_story
from brevo_client import send_story_email, send_paywall_email, STRIPE_LINK

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

TRIAL_DAYS = 7

def _build_profile(subscriber: dict) -> dict:
    f = subscriber["fields"]
    history = json.loads(f.get("story_history") or "[]")
    interests = [i.strip() for i in f.get("interests", "").split(",") if i.strip()]
    avoid = [a.strip() for a in f.get("avoid_topics", "").split(",") if a.strip()]
    return {
        "child_name": f.get("child_name", ""),
        "age": f.get("age", 6),
        "pronouns": f.get("pronouns", "they/them"),
        "child_is_protagonist": True,
        "interests": interests,
        "avoid_topics": avoid,
        "comfort_object": f.get("comfort_object", ""),
        "life_theme": f.get("life_theme", ""),
        "recent_stories": history,
    }

def run() -> None:
    subscribers = get_active_subscribers()
    log.info(f"Processing {len(subscribers)} subscribers")

    for sub in subscribers:
        f = sub["fields"]
        child = f.get("child_name", "unknown")
        record_id = sub["id"]

        try:
            profile = _build_profile(sub)
            story = generate_story(profile)
        except Exception as e:
            log.error(f"Story generation failed for {child}: {e}")
            continue

        try:
            send_story_email(f["email"], child, story)
            log.info(f"Story sent to {child}")
        except Exception as e:
            log.error(f"Email failed for {child}: {e}")
            continue

        # Update story history
        try:
            history = json.loads(f.get("story_history") or "[]")
            history.append({
                "date": date.today().isoformat(),
                "archetype": story.get("archetype_used", ""),
                "setting": story.get("setting_used", ""),
                "character_type": story.get("character_type", ""),
            })
            update_subscriber(record_id, {"story_history": json.dumps(history[-14:])})
        except Exception as e:
            log.error(f"History update failed for {child}: {e}")

        # Paywall check
        if f.get("status") == "trial" and f.get("days_active", 0) >= TRIAL_DAYS:
            try:
                send_paywall_email(f["email"], child, STRIPE_LINK)
                log.info(f"Paywall email sent to {child}")
                update_subscriber(record_id, {"status": "paused"})
            except Exception as e:
                log.error(f"Paywall email failed for {child}: {e}")

if __name__ == "__main__":
    run()
