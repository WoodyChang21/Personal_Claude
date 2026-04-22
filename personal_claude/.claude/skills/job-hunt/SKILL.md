# Skill: job-hunt

Search for Machine Learning Engineer and AI Engineer new grad / entry-level roles in Canada and USA posted within the last 3 days, score them against the user's resume, generate tailored resume content, and write structured entries into the Notion "Job Leads" database via the Notion MCP connector. The user reviews leads each morning and applies manually.

## Trigger

Use this skill when the user asks to: run a job search, find ML/AI roles, populate the job leads database, or "run the job hunt pipeline".

Run this skill locally with `/job-hunt`. CCR scheduling is not used — Notion writes require local MCP access.

## Prerequisites

- Notion MCP connector must be active (cloud connector, no local setup needed)
- Job Leads database ID: `3499719ac5f4800da543c5b965c4003b`
- Resume: `.claude/skills/job-hunt/resume/Resume.pdf`

**IMPORTANT: Do NOT commit, push, or run any git commands during this pipeline.**

---

## Job Filters (strictly enforced)

| Filter | Value |
|---|---|
| Title | "Machine Learning Engineer" OR "ML Engineer" OR "AI Engineer" — exact match only |
| Seniority | New Grad OR Entry Level OR Junior OR 0–2 years experience |
| Location | Canada OR United States only |
| Recency | Posted within the last **3 days** — discard anything older |

Roles that do not match ALL four filters are discarded before scoring.

---

## Pipeline

### Step 1 — Load Resume

Read `.claude/skills/job-hunt/resume/Resume.pdf` with the Read tool.

Extract and note:
- Skills (languages, frameworks, tools)
- Degrees (field, institution, graduation year)
- Work experience (company, role, dates, bullet points)
- Projects (name, description, technologies, impact)
- Publications or research (if any)

If the file is missing, stop and print: `ERROR: Resume.pdf not found at .claude/skills/job-hunt/resume/Resume.pdf`

---

### Step 2 — Search (8 parallel WebSearch queries)

Run all 8 queries in a single parallel batch. Today's date can be obtained via Bash: `date +%Y-%m-%d`.

1. `"Machine Learning Engineer" "new grad" OR "entry level" Canada 2025 site:linkedin.com/jobs OR site:greenhouse.io`
2. `"AI Engineer" "new grad" OR "entry level" Canada 2025 site:linkedin.com/jobs OR site:lever.co`
3. `"Machine Learning Engineer" "new grad" OR "entry level" "United States" 2025 site:greenhouse.io OR site:workday.com`
4. `"AI Engineer" "new grad" OR "entry level" "United States" 2025 site:linkedin.com/jobs OR site:lever.co`
5. `"ML Engineer" "new grad" OR "entry level" Canada OR "United States" -senior -staff -principal -lead site:jobs.lever.co`
6. `site:boards.greenhouse.io "machine learning engineer" OR "AI engineer" "new grad" OR "entry level" 2025`
7. `"New Grad Machine Learning Engineer" OR "New Grad AI Engineer" Canada OR USA 2025`
8. `"ML Engineer" OR "AI Engineer" "0-1 years" OR "0-2 years" Canada OR "United States" site:linkedin.com/jobs OR site:ashbyhq.com`

Collect raw results. Deduplicate by URL. **Discard postings older than 3 days.** Target 10–20 raw leads.

---

### Step 3 — Filter and Score Each Lead (1–10)

**Hard disqualifiers — skip entirely if ANY of these apply:**
- Title is not "Machine Learning Engineer", "ML Engineer", or "AI Engineer" (e.g. Data Scientist, Data Engineer, Software Engineer without AI-specific focus — discard)
- No explicit new grad / entry level / junior / 0–2 years signal in the posting
- Location is outside Canada and USA
- Posted more than 3 days ago
- URL returns 404 or is inaccessible

**Scoring rubric (only for leads that pass all disqualifiers):**
| Condition | Points |
|---|---|
| Title is exactly "ML Engineer" or "AI Engineer" at new grad level | +3 |
| Tech stack overlaps with resume skills | +2 |
| Known AI-forward company (OpenAI, Google DeepMind, Cohere, Vector Institute, Waabi, Anthropic, etc.) | +2 |
| Canadian company or Canadian office listed | +1 |
| Posted within 24 hours | +1 |
| Vague posting, no technical details | -1 |
| Domain experience user clearly lacks | -2 |

Keep top 10 leads with score ≥ 5. If fewer than 5 qualify, keep all that score ≥ 4.

---

### Step 4 — Tailor Resume Per Lead + Generate PDF

For each kept lead, `WebFetch` the job URL to get the full job description.

**4a. Plan the tailoring** — decide which parts of the resume to change:

Rules:
- Mirror JD keywords exactly where the resume already demonstrates the skill
- Never fabricate experience, credentials, or skills
- Quantify wherever possible
- Reorder `Technical Skills` categories/items so the most JD-relevant ones appear first
- Rewrite up to 3 work experience bullets per role to mirror JD language
- Reorder projects so the 1–2 most relevant appear first; rewrite their bullets to mirror JD keywords
- Keep education unchanged

**4b. Generate a tailored `.tex` file** — copy `Resume.tex` and apply the changes above.

Output directory: `.claude/skills/job-hunt/resume/tailored/YYYY-MM-DD/`  
File name: `{Company}_{Role}.tex` (spaces → underscores, lowercase)

LaTeX escaping rules (apply whenever inserting any text into `.tex`):
- `&` → `\&`
- `%` → `\%`
- `#` → `\#`
- `_` → `\_`
- `$` → `\$`
- `{` / `}` → `\{` / `\}`
- `~` → `\textasciitilde{}`
- `^` → `\textasciicircum{}`
- `\` → `\textbackslash{}`
- Smart quotes / em-dashes from JD copy: replace with `''`, `--`, `---` as appropriate

**4c. Compile to PDF** using Bash:
```bash
cd ".claude/skills/job-hunt/resume/tailored/YYYY-MM-DD"
pdflatex -interaction=nonstopmode "{Company}_{Role}.tex"
```

Run twice if needed (for cross-references). Check output says `(1 page,` — if 2 pages, reduce `\vspace` amounts in the file and recompile.

If WebFetch fails for a URL, note "Resume tailoring skipped — could not fetch JD" and skip 4b/4c for that lead.

---

### Step 5 — Write to Notion via MCP (sequential)

Use the **Notion MCP tools** to write each lead. Do NOT use `notion_client.py` or make direct API calls.

Job Leads database ID: `3499719ac5f4800da543c5b965c4003b`

For each lead, do the following in order:

**5a. Create the job lead page** using `notion-create-pages`:
- Parent: database `3499719ac5f4800da543c5b965c4003b`
- Properties to set:
  - Name (title): `"{Role} @ {Company}"`
  - Company: `{company}`
  - Role: `{role}`
  - Location: `{location}`
  - Job URL: `{url}`
  - Status: `New`
  - Date Found: `{today's date, YYYY-MM-DD}`
  - Match Score: `{score}`
  - Source: `{source, e.g. Greenhouse / LinkedIn}`
  - Resume PDF: local path `.claude/skills/job-hunt/resume/tailored/YYYY-MM-DD/{Company}_{Role}.pdf` (as a text property or page body note)

**5b. Add a brief tailoring note** as page body content (plain paragraph, no child page needed):
- 2–3 sentences explaining why this candidate is a strong match, referencing specific JD requirements
- List the 3 most impactful resume changes made for this JD

Wait briefly between each lead to respect Notion rate limits.

---

### Step 6 — Print Summary

```
Job Hunt Run — YYYY-MM-DD
Filters: ML/AI Engineer | New Grad/Entry Level | Canada + USA | Posted ≤ 3 days
Raw leads found: N | Qualified (score ≥ 5): N | Written to Notion: N | PDFs saved: N

Top leads:
1. ML Engineer @ Cohere — Toronto, ON — Score 8 — https://...
   PDF: .claude/skills/job-hunt/resume/tailored/YYYY-MM-DD/Cohere_ML_Engineer.pdf
2. AI Engineer @ Waabi — Remote, Canada — Score 7 — https://...
   PDF: .claude/skills/job-hunt/resume/tailored/YYYY-MM-DD/Waabi_AI_Engineer.pdf
...
```

---

## Error Handling

- If a Notion write fails, log the error and continue with remaining leads.
- If a PDF compilation fails, log the error and continue — do not skip the Notion write for that lead.
- If fewer than 3 leads are found after filtering, print: `WARNING: Only N leads found. Filters: ML/AI Engineer title + New Grad/Entry Level + Canada/USA + posted ≤ 3 days. Consider running again tomorrow.`
- Never fall back to git as a substitute for Notion writes.
- Compiled PDFs and `.tex` source files in `tailored/` are local only — never commit them.
