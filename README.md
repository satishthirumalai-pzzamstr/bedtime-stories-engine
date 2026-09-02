# Bedtime Stories Engine

Nightly Python script that generates personalized AI bedtime stories per child, emails them via Brevo, and enforces a 7-night free trial with Stripe paywall.

## Architecture

```
Landing page (Vercel static) → Supabase (subscribers table)
                                        ↓
                          Windows Task Scheduler (11pm CT nightly)
                                        ↓
                          main.py orchestrator
                            ├── airtable_client.py  → Supabase REST API
                            ├── story_generator.py  → Claude API (claude-sonnet-5)
                            └── brevo_client.py     → Brevo transactional email
```

## Tech Stack

| Component | Service |
|---|---|
| Story generation | Claude API — `claude-sonnet-5` |
| Subscriber database | Supabase (PostgreSQL via REST) |
| Email delivery | Brevo transactional email |
| Landing page | Vercel static (index.html) |
| Scheduler | Windows Task Scheduler (local) |
| Payments | Stripe Payment Links |

## File Map

| File | Purpose |
|---|---|
| `main.py` | Nightly orchestrator |
| `airtable_client.py` | Supabase REST client (get subscribers, update records) |
| `story_generator.py` | Claude API call, JSON parse, word-count validation, retry |
| `brevo_client.py` | Story email + paywall email via Brevo |
| `prompt.py` | `SYSTEM_PROMPT` — full bedtime story spec |
| `email_template.html` | HTML template for story emails |
| `index.html` | Landing page (deployed to Vercel) |
| `requirements.txt` | Python dependencies |
| `railway.toml` | Railway config (not currently used — kept for future cloud deploy) |
| `vercel.json` | Vercel static site config |
| `run_stories.ps1` | Local runner with env vars — **not committed, contains secrets** |

## Supabase Schema

```sql
CREATE TABLE subscribers (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email       text NOT NULL UNIQUE,
  child_name  text,
  age         int,
  pronouns    text DEFAULT 'they/them',
  interests   text,
  avoid_topics text,
  comfort_object text,
  life_theme  text,
  status      text DEFAULT 'trial',   -- trial | active | paused
  days_active int DEFAULT 0,
  story_history text DEFAULT '[]',    -- JSON array, last 14 entries
  signup_date date
);
ALTER TABLE subscribers DISABLE ROW LEVEL SECURITY;
```

## Environment Variables

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → Workspaces → API Keys (use workspace key, not identity-linked) |
| `SUPABASE_URL` | Supabase project → Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase project → Settings → API → `anon` public key |
| `BREVO_API_KEY` | Brevo → SMTP & API → API Keys |
| `STRIPE_LINK` | Stripe Dashboard → Payment Links |

All set in `run_stories.ps1` (local) — never hardcoded or committed.

## Local Run

```powershell
.\run_stories.ps1
```

Logs append to `run.log`.

## Task Scheduler

Registered at 11pm CT nightly. To verify:

```powershell
Get-ScheduledTask -TaskName "BedtimeStories"
```

To re-register (run PowerShell as Administrator):

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"C:\AI\Expirements\bedtime-stories-engine\run_stories.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At "11:00PM"
Register-ScheduledTask -TaskName "BedtimeStories" -Action $action -Trigger $trigger -RunLevel Highest -Force
```

## Trial + Paywall Logic

- New signup → `status = trial`, `days_active = 0`
- Each nightly run: story sent, `story_history` updated (last 14 kept)
- Night 7 (`days_active >= 7`, `status == trial`): story sent + paywall email sent, `status → paused`
- After Stripe payment: manually set `status = active` in Supabase (Zapier automation TBD)
- `active` subscribers: no trial limit, stories continue indefinitely

## Landing Page

Deployed at `bedtime-stories-engine.vercel.app`. Collects:
- Parent email (required)
- Child name, age, pronouns (required)
- Interests (required)
- Avoid topics, comfort object, life theme (optional)

Writes directly to Supabase `subscribers` table via REST.

## Known Limitations (see PRODUCTION.md)

- `days_active` is not auto-incremented — currently set to `0` on signup and not updated nightly (stories still send; paywall triggers on `days_active` field)
- Stripe → Supabase status update is manual (no Zapier yet)
- Brevo IP allowlisting is tied to current ISP IP — will break if IP changes
- Scheduler runs on a local Windows machine — requires machine to be on at 11pm CT
