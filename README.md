# 🎯 Samdarsh's Daily Job Pipeline

Scrapes 40 fresh Dubai jobs every morning, scores them against your resume using Claude AI, generates cover letters for top matches, and emails you a digest — all automatically via GitHub Actions.

---

## What It Does Daily (7 AM Dubai time)

| Step | Details |
|------|---------|
| 🔍 Scrape | 20 Tech/AI/Python jobs + 20 Sales/BD jobs from LinkedIn (past 24h, Dubai) |
| 🤖 Score | Claude AI rates each 1–10 against your resume with a one-line reason |
| ✉️ Cover Letters | Auto-generated for all jobs scoring 6+ |
| 📧 Email | Beautiful HTML digest lands in your inbox |

---

## Setup (one-time, ~10 minutes)

### Step 1 — Create a GitHub repo

1. Go to [github.com/new](https://github.com/new)
2. Name it `job-pipeline` (private recommended)
3. Upload all files from this zip, preserving the folder structure

### Step 2 — Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these 5 secrets:

| Secret Name | Where to get it |
|-------------|----------------|
| `APIFY_TOKEN` | [apify.com/account/integrations](https://console.apify.com/account/integrations) → API tokens |
| `ANTHROPIC_API_KEY` | [console.anthropic.com/keys](https://console.anthropic.com/settings/keys) |
| `EMAIL_FROM` | Your Gmail address (e.g. `samdarshs033@gmail.com`) |
| `EMAIL_APP_PASSWORD` | See Step 3 below |
| `EMAIL_TO` | Where to receive digest (can be same Gmail) |

### Step 3 — Gmail App Password

Gmail requires an App Password (not your regular password) for SMTP:

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already on
3. Search for **"App passwords"** in the search bar
4. Create one → select **Mail** → **Other** → name it `job-pipeline`
5. Copy the 16-character password → paste as `EMAIL_APP_PASSWORD` secret

### Step 4 — Enable GitHub Actions

1. Go to your repo → **Actions** tab
2. Click **"I understand my workflows, go ahead and enable them"**
3. You should see **"Daily Job Pipeline"** listed

### Step 5 — Test it now

1. Go to **Actions → Daily Job Pipeline → Run workflow**
2. Click the green **"Run workflow"** button
3. Watch the logs — should take 5–10 minutes
4. Check your inbox!

---

## Customisation

Edit `scripts/job_pipeline.py` to change:

```python
# Change search terms
TECH_SEARCHES = [
    "AI developer Dubai",
    "Python developer Dubai",
    ...
]

BD_SEARCHES = [
    "business development AI technology Dubai",
    ...
]

# Change how many cover letters to generate (default: top 8)
TOP_N = 8

# Change cron schedule in .github/workflows/daily_jobs.yml
# "0 3 * * *" = 7 AM Dubai (UTC+4). Use crontab.guru to adjust.
```

---

## Costs

| Service | Cost |
|---------|------|
| GitHub Actions | ✅ Free (2,000 mins/month) |
| Apify (LinkedIn scraper) | ~$0.02/day (40 jobs × $0.001 × 2 runs) |
| Anthropic Claude | ~$0.05/day (scoring + cover letters) |
| **Total** | **~$2/month** |

---

## Troubleshooting

**Email not arriving?**
- Check spam folder
- Verify `EMAIL_APP_PASSWORD` is the 16-char app password, not your Gmail password
- Make sure 2FA is enabled on Gmail

**Apify run failing?**
- Check your Apify token at console.apify.com
- Ensure you have billing set up (free tier includes $5 credit)

**Claude errors?**
- Verify `ANTHROPIC_API_KEY` is correct at console.anthropic.com
- Check you have API credits

**No jobs returned?**
- LinkedIn occasionally blocks scrapers; re-run the workflow the next day
- You can also add more search URLs in `TECH_SEARCHES`
