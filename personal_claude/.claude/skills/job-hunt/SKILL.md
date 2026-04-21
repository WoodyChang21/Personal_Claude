# Skill: job-hunt

Search for ML/AI new grad roles in Canada and USA, score them against the user's resume, generate tailored resume content, and write structured entries into the Notion "Job Leads" database. The user reviews leads each morning and applies manually.

## Trigger

Use this skill when the user asks to: run a job search, find ML/AI roles, populate the job leads database, or "run the job hunt pipeline".

This skill also runs as a scheduled remote CCR agent every weekday at 9am America/Toronto.

## Prerequisites

Required env vars (walk up dirs to find `.env`):
- `NOTION_TOKEN` — Notion integration secret
- `JOB_LEADS_DB_ID` — ID of the "Job Leads" Notion database
- `APPLIED_JOBS_DB_ID` — ID of the "Applied Jobs" Notion database

Script: `.claude/skills/job-hunt/scripts/notion_client.py`
Resume: `.claude/skills/job-hunt/resume/resume.pdf`

---

## Pipeline

### Step 1 — Load Resume

Read `.claude/skills/job-hunt/resume/resume.pdf` with the Read tool.

Extract and note:
- Skills (languages, frameworks, tools)
- Degrees (field, institution, graduation year)
- Work experience (company, role, dates, bullet points)
- Projects (name, description, technologies, impact)
- Publications or research (if any)

If the file is missing, stop and print: `ERROR: resume.pdf not found at .claude/skills/job-hunt/resume/resume.pdf`

---

### Step 2 — Search (8 parallel WebSearch queries)

Run all 8 queries in a single parallel batch:

1. `"ML Engineer new grad 2025 Canada" site:linkedin.com/jobs OR site:indeed.ca`
2. `"AI Engineer entry level Canada" site:linkedin.com/jobs OR site:greenhouse.io`
3. `"Machine Learning Engineer new grad USA" site:linkedin.com/jobs OR site:lever.co`
4. `"AI Engineer new grad 2025 United States" site:greenhouse.io OR site:workday.com`
5. `"Junior ML Engineer OR New Grad ML" Canada USA -senior -staff -principal`
6. `site:jobs.lever.co "machine learning" OR "AI engineer" 2025`
7. `site:boards.greenhouse.io "machine learning engineer" entry level`
8. `"New Grad Software Engineer ML" Google OR Meta OR Amazon OR Microsoft Canada`

Collect raw results. Deduplicate by URL. Discard postings older than 14 days. Target 15–25 raw leads.

---

### Step 3 — Score Each Lead (1–10)

**Hard disqualifiers (skip entirely):**
- Explicit 3+ years of experience requirement
- Title includes Senior, Staff, Principal, Lead, Manager
- Location is outside Canada and USA
- URL returns 404

**Scoring rubric:**
| Condition | Points |
|---|---|
| Title includes "New Grad", "Entry Level", "Junior", or "0–2 years" | +3 |
| Role is specifically ML / AI / MLOps / NLP / CV | +2 |
| Tech stack overlaps with resume skills | +2 |
| Known AI-forward company (OpenAI, Google DeepMind, Cohere, Vector Institute, Waabi, etc.) | +1 |
| Canadian company or Canadian office | +1 |
| Posted within 7 days | +1 |
| Vague posting, no technical details | -1 |
| Domain experience user clearly lacks | -2 |

Keep the top 10 leads with score ≥ 5. If fewer than 5 qualify, keep all that score ≥ 4.

---

### Step 4 — Tailor Resume Per Lead

For each kept lead, `WebFetch` the job URL to get the full job description.

Generate tailored resume as structured data:

```json
{
  "rationale": "2–3 sentences in third person explaining why this candidate is a strong match, referencing specific JD requirements",
  "skills": ["skill1 — why it matches", "skill2 — why it matches"],
  "experience": [
    {
      "company": "...",
      "role": "...",
      "dates": "...",
      "bullets": ["rewritten bullet mirroring JD language", "..."]
    }
  ],
  "projects": [
    {"name": "...", "description": "1–2 sentences, quantified, mirroring JD keywords"}
  ],
  "education": "Degree, Institution, Year. Relevant coursework: ..."
}
```

Rules:
- Mirror JD keywords exactly where the resume already demonstrates the skill
- Never fabricate experience, credentials, or skills
- Quantify wherever possible
- Order skills and experience by relevance to this specific JD
- Include 8–12 skills, 1–3 experience entries, 1–2 projects

Then call `build_resume_blocks()` to convert to Notion block JSON.

---

### Step 5 — Write to Notion (sequential)

Load env vars. For each lead (with 0.4s sleep between leads):

```bash
# Write job properties to temp file
# Create the job lead page
python .claude/skills/job-hunt/scripts/notion_client.py create-page \
  --token "$NOTION_TOKEN" \
  --db-id "$JOB_LEADS_DB_ID" \
  --job-json /tmp/job_N.json

# Capture the returned page_id, write blocks to temp file
python .claude/skills/job-hunt/scripts/notion_client.py append-resume \
  --token "$NOTION_TOKEN" \
  --page-id <returned_page_id> \
  --blocks-json /tmp/blocks_N.json
```

The `job_N.json` shape:
```json
{
  "company": "Cohere",
  "role": "ML Engineer",
  "location": "Toronto, ON",
  "url": "https://...",
  "date_found": "2025-04-21",
  "score": 8,
  "source": "Greenhouse"
}
```

The `blocks_N.json` is the list returned by `build_resume_blocks()`.

---

### Step 6 — Print Summary

```
Job Hunt Run — YYYY-MM-DD
Raw leads found: N | Qualified (score ≥ 5): N | Written to Notion: N

Top leads:
1. ML Engineer @ Cohere — Toronto, ON — Score 8 — https://...
2. AI Engineer @ Waabi — Remote, Canada — Score 7 — https://...
...
```

---

## Error Handling

- If a WebFetch fails for a specific job URL, log a warning and skip the tailoring step — write the lead to Notion without a child resume page, noting "Resume tailoring skipped — could not fetch JD" in a Notion paragraph block.
- If a Notion write fails, log the error and continue with remaining leads.
- If fewer than 3 leads are found after scoring, print a warning: `WARNING: Only N leads found — consider broadening search terms.`
