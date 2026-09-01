import os
import requests
from pathlib import Path

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
SENDER = {"name": "Bedtime Stories", "email": "stories@yourdomain.com"}
STRIPE_LINK = "https://buy.stripe.com/YOUR_LINK_HERE"  # replace after Stripe setup

def _headers() -> dict:
    return {
        "accept": "application/json",
        "api-key": os.environ["BREVO_API_KEY"],
        "content-type": "application/json",
    }

def _render_template(story: dict) -> str:
    template = Path("email_template.html").read_text()
    for key in ("title", "preheader", "story", "closing_line",
                "parent_note", "reading_time_minutes"):
        template = template.replace(f"{{{{{key}}}}}", str(story.get(key, "")))
    template = template.replace("{{unsubscribe_url}}", "mailto:stories@yourdomain.com?subject=Unsubscribe")
    return template

def _post(payload: dict) -> None:
    response = requests.post(BREVO_API_URL, headers=_headers(), json=payload)
    if response.status_code not in (200, 201):
        raise RuntimeError(f"Brevo error {response.status_code}: {response.text}")

def send_story_email(to_email: str, child_name: str, story: dict) -> None:
    _post({
        "sender": SENDER,
        "to": [{"email": to_email}],
        "subject": story["subject"],
        "htmlContent": _render_template(story),
    })

def send_paywall_email(to_email: str, child_name: str, stripe_link: str) -> None:
    html = f"""
    <html><body style="font-family:Georgia,serif;font-size:18px;line-height:1.8;
                       color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px 16px;">
    <p>Hi — {child_name}'s 7 free stories are complete.</p>
    <p>To keep the stories coming every night, continue for <strong>$8/month</strong>:</p>
    <p><a href="{stripe_link}" style="background:#2d6a4f;color:white;padding:12px 24px;
           text-decoration:none;border-radius:4px;display:inline-block;">
       Continue {child_name}'s stories →</a></p>
    <p style="color:#888;font-size:14px;">Stories pause until payment is confirmed.
       Questions? Reply to this email.</p>
    </body></html>
    """
    _post({
        "sender": SENDER,
        "to": [{"email": to_email}],
        "subject": f"Last free story + keep the magic going ($8/mo)",
        "htmlContent": html,
    })
