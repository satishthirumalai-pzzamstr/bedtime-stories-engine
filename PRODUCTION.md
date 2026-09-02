# Production Checklist

Current state: **working locally**, stories sending nightly to real subscribers. Below is what's needed to make this production-grade.

---

## Critical — Fix Before Scaling

### 1. `days_active` not incrementing
**Problem:** `days_active` stays at `0` forever. Paywall never fires automatically.  
**Fix:** In `main.py`, after updating story history, increment `days_active`:

```python
update_subscriber(record_id, {
    "story_history": json.dumps(history[-14:]),
    "days_active": f.get("days_active", 0) + 1,
})
```

**Impact:** Without this, trial subscribers never hit day 7 and never get paywalled.

---

### 2. Stripe → Supabase status update is manual
**Problem:** After someone pays via Stripe, their `status` stays `paused`. Stories don't resume until manually set to `active` in Supabase.  
**Fix (Zapier):**
1. zapier.com → Create Zap
2. Trigger: Stripe → **Payment Intent Succeeded** (or Subscription Created)
3. Action: Supabase → find row by `email` (from Stripe metadata) → update `status = active`

**Stripe metadata:** add `email` to the Payment Link prefill so Zapier can match it:
- Stripe Dashboard → Payment Link → Edit → **Collect customers' billing details** → enable Email

---

### 3. Brevo IP allowlisting breaks on IP change
**Problem:** Brevo blocks API calls from unrecognized IPs. Your home IP is dynamic — it will change.  
**Fix options (pick one):**
- **A (easiest):** Remove IP restriction in Brevo. Settings → Security → Authorised IPs → delete the entry. Relies on API key secrecy alone.
- **B (better):** Move email sending to a static IP (cloud VM, Railway Pro, Render).
- **C (best):** Use Brevo SMTP instead of REST API — SMTP isn't IP-restricted.

---

### 4. Scheduler tied to local machine
**Problem:** If your PC is off or asleep at 11pm CT, no stories go out.  
**Fix:** Move to cloud. Options:

| Option | Cost | Effort |
|---|---|---|
| Railway (worker + cron) | ~$5/mo | Low — `railway.toml` already exists; blocked by free tier egress, need paid plan |
| Render (cron job) | Free tier available | Low |
| GitHub Actions (scheduled workflow) | Free | Medium — add `ANTHROPIC_API_KEY` etc. as GitHub secrets |
| VPS (DigitalOcean/Linode) | ~$4/mo | Medium |

**GitHub Actions approach** (recommended — zero infrastructure):

```yaml
# .github/workflows/nightly.yml
name: Nightly Stories
on:
  schedule:
    - cron: '0 5 * * *'  # 5am UTC = 11pm CT
  workflow_dispatch:      # manual trigger
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          BREVO_API_KEY: ${{ secrets.BREVO_API_KEY }}
          STRIPE_LINK: ${{ secrets.STRIPE_LINK }}
```

Add secrets: GitHub repo → Settings → Secrets and variables → Actions.

---

## Important — Before Taking Money

### 5. Stripe Payment Link configured
- [ ] Create product: "Bedtime Stories" — $8/month recurring
- [ ] Copy link URL → add to `run_stories.ps1` as `STRIPE_LINK`
- [ ] Enable email collection on the payment form (needed for Zapier matching)
- [ ] Test payment in Stripe test mode first

### 6. Unsubscribe actually works
**Current state:** Unsubscribe link opens a mailto. No automation.  
**Fix:** Add a Supabase Edge Function or simple endpoint that sets `status = unsubscribed` when hit. Or use Brevo's built-in unsubscribe management (requires Brevo domain verification).

### 7. Domain verification for email
**Current state:** Sending from `satish.thirumalai@gmail.com` via Brevo.  
**For deliverability:** Set up a sender domain (e.g. `stories.yourdomain.com`) with SPF/DKIM records in Brevo. Gmail addresses as sender via third-party ESP often land in spam.

---

## Nice to Have — After Launch

### 8. Welcome email on signup
Currently: no email sent when someone signs up. First contact is the first story (next night).  
**Add:** trigger a welcome email from the landing page JS immediately after successful Supabase insert.

### 9. Subscriber management UI
Currently: manage via Supabase SQL editor.  
**Options:** Supabase Table Editor (already works), or a simple admin page.

### 10. Error alerting
Currently: errors log to `run.log` locally. No alerts if nightly run fails.  
**Fix:** Add email alert on exception in `main.py`, or use GitHub Actions email notifications.

### 11. Duplicate email handling on landing page
Currently: Supabase returns 409 on duplicate — landing page shows an error message. Fine for now.  
**Better:** check for duplicate before insert, show "you're already signed up" with next steps.

---

## Production Launch Order

1. Fix `days_active` increment (30 min — code change)
2. Set up GitHub Actions nightly workflow (1 hour)
3. Configure Stripe Payment Link + test payment (30 min)
4. Set up Zapier: Stripe paid → Supabase `status = active` (1 hour)
5. Verify Brevo domain / sender reputation (1-2 hours)
6. Remove Brevo IP restriction OR move to static IP (30 min)
7. Test full 7-night cycle with a test subscriber

Total: ~1 day of work to be fully production-ready.
