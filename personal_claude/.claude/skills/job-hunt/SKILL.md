# Skill: job-hunt

Search for Machine Learning Engineer and AI Engineer new grad / entry-level roles in Canada and USA posted within the last 3 days, score them against the user's resume, generate tailored resume content, and write structured entries into the Notion "Job Leads" database via the Notion MCP connector. The user reviews leads each morning and applies manually.

## Trigger

Use this skill when the user asks to: run a job search, find ML/AI roles, populate the job leads database, or "run the job hunt pipeline".

Run this skill locally with `/job-hunt`. CCR scheduling is not used — Notion writes require local MCP access.

## Prerequisites

- Notion MCP connector must be active (cloud connector, no local setup needed)
- Job Leads database ID: `3499719ac5f4800da543c5b965c4003b`
- Applied Jobs database ID: `78350949d774433298f637436df32623`
- Resume PDF: `.claude/skills/job-hunt/resume/base/Resume.pdf`
- Resume LaTeX source: `.claude/skills/job-hunt/resume/base/Resume.tex`

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

Read `.claude/skills/job-hunt/resume/base/Resume.pdf` with the Read tool.

Extract and note:
- Skills (languages, frameworks, tools)
- Degrees (field, institution, graduation year)
- Work experience (company, role, dates, bullet points)
- Projects (name, description, technologies, impact)

If the file is missing, stop and print: `ERROR: Resume.pdf not found at .claude/skills/job-hunt/resume/base/Resume.pdf`

---

### Step 2 — Search (8 parallel WebSearch queries)

Run all 8 queries in a single parallel batch. Today's date can be obtained via Bash: `date +%Y-%m-%d`.

1. `"Machine Learning Engineer" "new grad" OR "entry level" Canada 2026 site:linkedin.com/jobs OR site:greenhouse.io`
2. `"AI Engineer" "new grad" OR "entry level" Canada 2026 site:linkedin.com/jobs OR site:lever.co`
3. `"Machine Learning Engineer" "new grad" OR "entry level" "United States" 2026 site:greenhouse.io OR site:workday.com`
4. `"AI Engineer" "new grad" OR "entry level" "United States" 2026 site:linkedin.com/jobs OR site:lever.co`
5. `"ML Engineer" "new grad" OR "entry level" Canada OR "United States" -senior -staff -principal -lead site:jobs.lever.co`
6. `site:boards.greenhouse.io "machine learning engineer" OR "AI engineer" "new grad" OR "entry level" 2026`
7. `"New Grad Machine Learning Engineer" OR "New Grad AI Engineer" Canada OR USA 2026`
8. `"ML Engineer" OR "AI Engineer" "0-1 years" OR "0-2 years" Canada OR "United States" site:linkedin.com/jobs OR site:ashbyhq.com`

Collect raw results. Deduplicate by URL. **Discard postings older than 3 days.** Target 10–20 raw leads.

---

### Step 2.5 — Duplicate Check Against Notion (sequential)

Before scoring, check both Notion databases to avoid re-processing roles already tracked.

For each raw lead, run:
```bash
cd ".claude/skills/job-hunt"
python scripts/notion_client.py check-duplicate --title "{Role} @ {Company}"
```

The script searches both the Job Leads DB and Applied Jobs DB. Output is `duplicate` or `new`.

**If output is `duplicate`**, discard that lead and note: `SKIP (already tracked): {Role} @ {Company}`.

Continue with only the leads that are not already in either database.

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
- Reorder `Technical Skills` bullet categories so the most JD-relevant ones appear first
- Rewrite up to 3 work experience bullets per role to mirror JD language
- Reorder projects so the 1–2 most relevant appear first; rewrite their bullets to mirror JD keywords
- Keep education unchanged

**4b. Generate a tailored `.tex` file** — copy `base/Resume.tex` and apply the changes above.

Output directory: `.claude/skills/job-hunt/resume/tailored/YYYY-MM-DD/`  
File name: `{Company}_{Role}.tex` (spaces → underscores, e.g. `Atlassian_ML_Engineer_2026_Graduate.tex`)

**Template structure** (matches `base/Resume.tex` — preserve exactly):
- Preamble: `geometry`, `titlesec`, `tabularx`, `xcolor`, `enumitem`, `fontawesome5`, `amsmath`, `hyperref`, `fontenc`, `inputenc`, `lmodern`, `setspace` (`\setstretch{0.94}`)
- Header: two `minipage` blocks — name left, contact info right with `\raggedleft`
- Section titles: `\section*{Name}` (starred, no numbering), rendered with `\titlerule`
- Job/project headers: `\begin{tabularx}{\linewidth}{@{}l X r@{}}` with role+company bold left, date `\textsc{}` right
- Skills line (projects): `\text{Skills: ...}\\` on its own line after the tabular, before `\begin{itemize}`
- Bullet lists: `\begin{itemize}[leftmargin=2em, itemsep=0pt]` with `\item`
- Project titles: wrapped in `\href{https://github.com/WoodyChang21/...}{\textbf{...}}`

**LaTeX escaping rules** (apply whenever inserting any text into `.tex`):
- `&` → `\&`
- `%` → `\%`
- `#` → `\#`
- `_` → `\_` (unless inside a URL argument)
- `$` → `\$`
- `{` / `}` → `\{` / `\}`
- `~` → `\textasciitilde{}`
- `^` → `\textasciicircum{}`
- `\` → `\textbackslash{}`
- Smart quotes / en-dashes / em-dashes from JD copy: replace with `''`, `--`, `---`

**4c. Compile to PDF** using Bash:
```bash
cd ".claude/skills/job-hunt/resume/tailored/YYYY-MM-DD"
pdflatex -interaction=nonstopmode "{Company}_{Role}.tex"
```

Check output says `(1 page,` — if 2 pages, tighten `\setstretch` (try `0.90`) or shorten a bullet, then recompile.

If WebFetch fails for a URL, note "Resume tailoring skipped — could not fetch JD" and skip 4b/4c for that lead.

---

### Step 5 — Write to Notion via Python script (sequential)

Use `scripts/notion_client.py` with the Notion REST API. Credentials are read automatically from `.env`.

Job Leads database ID: `3499719ac5f4800da543c5b965c4003b`

For each lead, do the following in order:

**5a. Create a job JSON file** at `/tmp/{company}_{role}_lead.json`:
```json
{
  "role": "{role}",
  "company": "{company}",
  "location": "{location}",
  "url": "{url}",
  "date_found": "YYYY-MM-DD",
  "score": {score},
  "source": "{source, e.g. Greenhouse / LinkedIn}"
}
```

**5b. Create the job lead page:**
```bash
cd ".claude/skills/job-hunt"
python scripts/notion_client.py create-page --job-json /tmp/{company}_{role}_lead.json
```
Save the returned page ID.

**5c. Create a note JSON file** at `/tmp/{company}_{role}_note.json`:
```json
{
  "note": "2–3 sentences: why this candidate is a strong match, referencing specific JD requirements.",
  "changes": [
    "Change 1: what was rewritten and why it mirrors the JD",
    "Change 2: ...",
    "Change 3: ..."
  ]
}
```

**5d. Append the tailoring note:**
```bash
python scripts/notion_client.py add-body-note \
  --page-id "{page_id from 5b}" \
  --note-json /tmp/{company}_{role}_note.json
```

Sleep 0.5s between leads to respect Notion rate limits.

---

### Step 6 — Print Summary

```
Job Hunt Run — YYYY-MM-DD
Filters: ML/AI Engineer | New Grad/Entry Level | Canada + USA | Posted ≤ 3 days
Raw leads found: N | Already tracked (skipped): N | Qualified (score ≥ 5): N | Written to Notion: N | PDFs saved: N

Top leads:
1. ML Engineer @ Cohere — Toronto, ON — Score 8 — https://...
   PDF: .claude/skills/job-hunt/resume/tailored/YYYY-MM-DD/Cohere_ML_Engineer.pdf
2. AI Engineer @ Waabi — Remote, Canada — Score 7 — https://...
   PDF: .claude/skills/job-hunt/resume/tailored/YYYY-MM-DD/Waabi_AI_Engineer.pdf
...

Skipped (already tracked): ML Engineer @ Atlassian, AI Engineer @ Google, ...
```

---

## Error Handling

- If a Notion write fails (non-zero exit or HTTP error), log the error and continue with remaining leads.
- If a PDF compilation fails, log the error and continue — do not skip the Notion write for that lead.
- If `check-duplicate` fails, log a warning and treat the lead as `new` — better to write a duplicate than miss a fresh lead.
- If fewer than 3 leads are found after filtering, print: `WARNING: Only N leads found. Filters: ML/AI Engineer title + New Grad/Entry Level + Canada/USA + posted ≤ 3 days. Consider running again tomorrow.`
- Never use the Notion MCP tools — always use `scripts/notion_client.py` directly via Bash.
- Compiled PDFs and `.tex` source files in `tailored/` are local only — never commit them.
