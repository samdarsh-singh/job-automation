"""
Daily Job Pipeline for Samdarsh Singh
- Scrapes 20 tech jobs + 20 sales/BD jobs from LinkedIn via Apify
- Scores each against resume using Claude AI
- Generates cover letters for top matches
- Sends a beautiful HTML email digest
"""

import os
import json
import time
import smtplib
import subprocess
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ── Config ────────────────────────────────────────────────────────────────────
APIFY_TOKEN     = os.environ["APIFY_TOKEN"]
ANTHROPIC_KEY   = os.environ["ANTHROPIC_API_KEY"]
EMAIL_FROM      = os.environ["EMAIL_FROM"]        # Gmail address
EMAIL_PASSWORD  = os.environ["EMAIL_APP_PASSWORD"] # Gmail App Password
EMAIL_TO        = os.environ["EMAIL_TO"]           # samdarshs033@gmail.com
TOP_N           = 8   # generate cover letters for top N jobs per category

RESUME = """
Samdarsh Singh — Dubai, UAE
7 years Python/backend engineering. MSc AI (De Montfort Dubai, 2025-26).
Forward Deployed Engineer at Bluethink IT (Feb 2021 – Jan 2026):
- Cut POC-to-production cycle 35% across 3 enterprise AI projects
- 40% API latency reduction via FastAPI + Redis async rebuild
- LLM-integrated CMS deployment, zero critical post-launch incidents
- PostgreSQL/MongoDB query optimization 30-50% improvement
- Celery/RabbitMQ resilient pipelines at millions-of-tasks scale
- 100% on-time milestone delivery with government/enterprise clients
Skills: Python, FastAPI, Django, Flask, LLM deployment, OpenAI API, NLP,
        PostgreSQL, MongoDB, Redis, Elasticsearch, Docker, Kubernetes, AWS,
        Microservices, Event-Driven Architecture, Multi-Tenant Platforms
Projects: LLM Semantic Search Engine, Real-Time AI Scoring Engine (10k users),
          Multi-Tenant AI Logistics Platform
"""

TECH_SEARCHES = [
    "AI developer Dubai",
    "Python developer Dubai",
    "forward deployed engineer Dubai",
    "LLM engineer Dubai",
    "backend engineer AI Dubai",
]
BD_SEARCHES = [
    "business development AI technology Dubai",
    "sales engineer SaaS Dubai",
    "solutions engineer enterprise Dubai",
    "account executive technology Dubai",
    "technical sales AI Dubai",
]

# ── Apify Scraper ─────────────────────────────────────────────────────────────
def scrape_linkedin(queries: list[str], count_per_query: int = 6) -> list[dict]:
    """Scrape LinkedIn jobs for a list of search queries."""
    urls = [
        f"https://www.linkedin.com/jobs/search/?keywords={q.replace(' ', '%20')}"
        f"&location=Dubai%2C%20United%20Arab%20Emirates&f_TPR=r86400&position=1&pageNum=0"
        for q in queries
    ]

    payload = {
        "urls": urls,
        "count": count_per_query * len(queries),
        "scrapeCompany": False,
    }

    # Start run
    run_url = "https://api.apify.com/v2/acts/curious_coder~linkedin-jobs-scraper/runs"
    r = requests.post(
        run_url,
        params={"token": APIFY_TOKEN},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    run_id = r.json()["data"]["id"]
    print(f"  Apify run started: {run_id}")

    # Poll until finished
    for _ in range(40):
        time.sleep(15)
        status_r = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            params={"token": APIFY_TOKEN},
            timeout=15,
        )
        status = status_r.json()["data"]["status"]
        print(f"  Status: {status}")
        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Apify run {run_id} failed: {status}")

    # Fetch dataset
    dataset_id = status_r.json()["data"]["defaultDatasetId"]
    items_r = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        params={"token": APIFY_TOKEN, "limit": count_per_query * len(queries)},
        timeout=30,
    )
    items_r.raise_for_status()
    return items_r.json()

def deduplicate(jobs: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for j in jobs:
        if j.get("id") not in seen:
            seen.add(j.get("id"))
            out.append(j)
    return out

# ── Claude AI Scoring & Cover Letters ────────────────────────────────────────
def claude(prompt: str, system: str = "", max_tokens: int = 1500) -> str:
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["content"][0]["text"]

def score_batch(jobs: list[dict], category: str, offset: int = 0) -> list[dict]:
    """Score a batch of up to 10 jobs in one Claude call."""
    job_list = "\n".join(
        f"{offset+i+1}. [{j.get('title','')}] at [{j.get('companyName','')}] — {j.get('descriptionText','')[:150]}"
        for i, j in enumerate(jobs)
    )
    prompt = f"""Evaluate these {category} jobs for this candidate (Dubai-based, 7yr Python/AI backend engineer, LLM deployment, FastAPI, forward deployed enterprise AI):

Rate each job 1-10 on fit. Reply ONLY with valid JSON array, no markdown:
[{{"score": 9, "reason": "one sentence"}}, ...]
One object per job in order.

JOBS:
{job_list}"""

    raw = claude(prompt, max_tokens=1000)
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)

def score_jobs(jobs: list[dict], category: str) -> list[dict]:
    """Score all jobs in batches of 10 and return sorted list."""
    all_scores = []
    for i in range(0, len(jobs), 10):
        batch = jobs[i:i+10]
        print(f"  Scoring batch {i//10 + 1}...")
        scores = score_batch(batch, category, offset=i)
        all_scores.extend(scores)
        time.sleep(2)

    for i, j in enumerate(jobs):
        j["score"] = all_scores[i].get("score", 5) if i < len(all_scores) else 5
        j["reason"] = all_scores[i].get("reason", "") if i < len(all_scores) else ""

    return sorted(jobs, key=lambda x: x["score"], reverse=True)

def generate_cover_letter(job: dict) -> str:
    prompt = f"""Write a punchy, specific 3-paragraph cover letter for Samdarsh Singh applying to:

Role: {job.get('title')}
Company: {job.get('companyName')}
Job description excerpt: {job.get('descriptionText','')[:600]}

Candidate background:
{RESUME}

Rules:
- Open with the single most relevant achievement from his background
- Paragraph 2: connect 2-3 specific skills to the role requirements
- Paragraph 3: brief closing, express genuine interest, no fluff
- Tone: confident, direct, not sycophantic
- Max 200 words total
- No "Dear Hiring Manager" — start with a strong hook sentence"""

    return claude(prompt, max_tokens=600)

# ── Email Builder ─────────────────────────────────────────────────────────────
def score_color(score: int) -> str:
    if score >= 8: return "#16a34a"   # green
    if score >= 6: return "#d97706"   # amber
    return "#dc2626"                  # red

def score_badge(score: int) -> str:
    color = score_color(score)
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:700">{score}/10</span>'

def job_card(job: dict, idx: int, cover: str | None = None) -> str:
    url = job.get("link", "#")
    applicants = job.get("applicantsCount", "?")
    emp_type = job.get("employmentType", "")
    seniority = job.get("seniorityLevel", "")
    cover_html = ""
    if cover:
        cover_html = f"""
        <div style="margin-top:14px;padding:14px;background:#f8fafc;border-left:3px solid #2563eb;border-radius:0 6px 6px 0">
          <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#2563eb;text-transform:uppercase;letter-spacing:.5px">✉ Cover Letter</p>
          <p style="margin:0;font-size:13px;color:#374151;line-height:1.6;white-space:pre-wrap">{cover}</p>
        </div>"""

    return f"""
    <div style="border:1px solid #e5e7eb;border-radius:8px;padding:18px;margin-bottom:14px;background:#fff">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
        <div>
          <p style="margin:0 0 4px;font-size:16px;font-weight:700;color:#111827">{idx}. {job.get('title','')}</p>
          <p style="margin:0;font-size:14px;color:#4b5563">🏢 {job.get('companyName','')} &nbsp;·&nbsp; 📍 Dubai, UAE</p>
        </div>
        {score_badge(job.get('score', 5))}
      </div>
      <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:8px">
        <span style="background:#eff6ff;color:#1d4ed8;padding:3px 10px;border-radius:20px;font-size:12px">{emp_type}</span>
        <span style="background:#f0fdf4;color:#15803d;padding:3px 10px;border-radius:20px;font-size:12px">{seniority}</span>
        <span style="background:#fef9c3;color:#854d0e;padding:3px 10px;border-radius:20px;font-size:12px">👥 {applicants} applicants</span>
      </div>
      <p style="margin:10px 0 0;font-size:13px;color:#6b7280;font-style:italic">{job.get('reason','')}</p>
      {cover_html}
      <div style="margin-top:14px">
        <a href="{url}" style="background:#2563eb;color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600">Apply on LinkedIn →</a>
      </div>
    </div>"""

def build_email(tech_jobs: list[dict], bd_jobs: list[dict], date_str: str) -> str:
    total = len(tech_jobs) + len(bd_jobs)
    top_tech = [j for j in tech_jobs if j.get("score", 0) >= 7]
    top_bd   = [j for j in bd_jobs   if j.get("score", 0) >= 7]

    tech_cards = "".join(job_card(j, i+1, j.get("cover_letter")) for i, j in enumerate(tech_jobs))
    bd_cards   = "".join(job_card(j, i+1, j.get("cover_letter")) for i, j in enumerate(bd_jobs))

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif">
<div style="max-width:680px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:32px 28px;text-align:center">
    <p style="margin:0 0 4px;color:#93c5fd;font-size:12px;letter-spacing:2px;text-transform:uppercase">Daily Job Digest</p>
    <h1 style="margin:0;color:#fff;font-size:26px;font-weight:800">Samdarsh's Job Pipeline</h1>
    <p style="margin:8px 0 0;color:#bfdbfe;font-size:14px">{date_str} &nbsp;·&nbsp; Dubai, UAE &nbsp;·&nbsp; {total} fresh listings</p>
  </div>

  <!-- Stats bar -->
  <div style="background:#eff6ff;padding:16px 28px;display:flex;justify-content:center;gap:32px;text-align:center">
    <div><p style="margin:0;font-size:22px;font-weight:800;color:#1d4ed8">{len(tech_jobs)}</p><p style="margin:0;font-size:12px;color:#6b7280">Tech / AI Roles</p></div>
    <div style="border-left:1px solid #dbeafe"></div>
    <div><p style="margin:0;font-size:22px;font-weight:800;color:#1d4ed8">{len(bd_jobs)}</p><p style="margin:0;font-size:12px;color:#6b7280">Sales / BD Roles</p></div>
    <div style="border-left:1px solid #dbeafe"></div>
    <div><p style="margin:0;font-size:22px;font-weight:800;color:#16a34a">{len(top_tech)+len(top_bd)}</p><p style="margin:0;font-size:12px;color:#6b7280">Strong Matches (7+)</p></div>
  </div>

  <div style="padding:28px">

    <!-- Tech section -->
    <h2 style="margin:0 0 18px;font-size:18px;color:#111827;border-bottom:2px solid #2563eb;padding-bottom:8px">
      🤖 Tech / AI / Python Roles
    </h2>
    {tech_cards}

    <!-- BD section -->
    <h2 style="margin:28px 0 18px;font-size:18px;color:#111827;border-bottom:2px solid #16a34a;padding-bottom:8px">
      💼 Sales / Business Development Roles
    </h2>
    {bd_cards}

    <!-- Footer tip -->
    <div style="margin-top:28px;padding:16px;background:#f8fafc;border-radius:8px;text-align:center">
      <p style="margin:0;font-size:13px;color:#6b7280">💡 <strong>Pro tip:</strong> Apply to the 7+ scored jobs first — the cover letters above are ready to paste. Aim for 5-8 quality applications today.</p>
    </div>
  </div>

  <div style="background:#f9fafb;padding:16px;text-align:center;border-top:1px solid #e5e7eb">
    <p style="margin:0;font-size:12px;color:#9ca3af">Generated by Samdarsh's Job Pipeline · LinkedIn scrape via Apify · Scoring by Claude AI</p>
  </div>
</div>
</body></html>"""

# ── Resume Generator ──────────────────────────────────────────────────────────
def generate_resume() -> str | None:
    """Run the Node.js resume generator and return the output file path."""
    script = os.path.join(os.path.dirname(__file__), "generate_resume.js")
    out_path = os.path.join(os.path.dirname(__file__), "resume_output.docx")
    try:
        subprocess.run(["node", script], check=True, cwd=os.path.dirname(__file__))
        print(f"  Resume generated: {out_path}")
        return out_path
    except Exception as e:
        print(f"  Resume generation failed: {e}")
        return None

# ── Send Email ────────────────────────────────────────────────────────────────
def send_email(html: str, date_str: str, resume_path: str | None = None):
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"🎯 Daily Job Digest — {date_str} | 40 fresh Dubai listings"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO

    # HTML body
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    # Attach resume if generated
    if resume_path and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            part = MIMEBase("application", "vnd.openxmlformats-officedocument.wordprocessingml.document")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=f"Samdarsh_Singh_Resume_{date_str.replace(' ', '_')}.docx")
        msg.attach(part)
        print(f"  Resume attached to email")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    print(f"  Email sent to {EMAIL_TO}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    date_str = datetime.now().strftime("%B %d, %Y")
    print(f"\n=== Job Pipeline — {date_str} ===\n")

    # 1. Scrape
    print("Scraping tech jobs...")
    raw_tech = scrape_linkedin(TECH_SEARCHES, count_per_query=5)
    tech_jobs = deduplicate(raw_tech)[:20]
    print(f"  Got {len(tech_jobs)} unique tech jobs")

    print("Scraping sales/BD jobs...")
    raw_bd = scrape_linkedin(BD_SEARCHES, count_per_query=5)
    bd_jobs = deduplicate(raw_bd)[:20]
    print(f"  Got {len(bd_jobs)} unique BD jobs")

    # 2. Score
    print("Scoring tech jobs with Claude...")
    tech_jobs = score_jobs(tech_jobs, "tech/AI/Python developer")

    print("Scoring sales/BD jobs with Claude...")
    bd_jobs = score_jobs(bd_jobs, "sales/business development in tech/AI")

    # 3. Cover letters for top matches
    print(f"Generating cover letters for top {TOP_N} tech matches...")
    for job in tech_jobs[:TOP_N]:
        if job.get("score", 0) >= 6:
            job["cover_letter"] = generate_cover_letter(job)
            time.sleep(1)

    print(f"Generating cover letters for top {TOP_N} BD matches...")
    for job in bd_jobs[:TOP_N]:
        if job.get("score", 0) >= 6:
            job["cover_letter"] = generate_cover_letter(job)
            time.sleep(1)

    # 4. Generate resume
    print("Generating ATS resume...")
    resume_path = generate_resume()

    # 5. Build & send email
    print("Sending email digest...")
    html = build_email(tech_jobs, bd_jobs, date_str)
    send_email(html, date_str, resume_path)

    print("\n✅ Pipeline complete!")

if __name__ == "__main__":
    main()
