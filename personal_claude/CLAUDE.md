# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## What This Workspace Is

A personal Claude Code workspace containing skills, agents, MCP servers, and automation workflows.

## GitHub Repository

**Repo:** https://github.com/WoodyChang21/Personal_Claude
**Local path:** `C:\Users\User\Desktop\Claude\personal_claude`
**Git root:** one level up at `C:\Users\User\Desktop\Claude\`

### When to Push to GitHub

Push to GitHub whenever any of the following occur:
- A new skill is added or significantly updated (`\.claude/skills/`)
- A new agent definition is added or changed (`agents/`)
- A new MCP server is added or configured (`.mcp.json`, `.mcp-servers/`)
- A new scheduled trigger is created or updated
- Any infrastructure change that a remote agent would depend on

**Push command (run from the git root):**
```bash
cd "/c/Users/User/Desktop/Claude"
git add .
git commit -m "your message"
git push
```

Always exclude `.env`, `.venv/`, `__pycache__/`, `.mcp-servers/`, and `.claude/settings.local.json` — these are in `.gitignore` and must never be committed.

---

## Skills

Skills live in `.claude/skills/<skill-name>/SKILL.md`. Claude Code loads and executes them on demand.

### ai-newsletter

**Location:** `.claude/skills/ai-newsletter/`
**Purpose:** Searches for the latest AI news, summarizes it, generates an HTML email newsletter, and sends it to `woodychang891121@gmail.com`.

**How it works:**
1. Runs parallel web searches for trending AI topics
2. Summarizes 8–12 stories into plain-English headlines + why-it-matters blurbs
3. Generates a self-contained HTML email using the template in `SKILL.md`
4. Sends via Gmail API (OAuth2), falls back to Gmail SMTP

**Send script:**
```bash
python .claude/skills/ai-newsletter/scripts/send_email.py \
  --html /tmp/ai_newsletter_YYYYMMDD.html \
  --subject "⚡ AI Weekly Digest — YYYY-MM-DD" \
  --to woodychang891121@gmail.com
```

**Required `.env` keys:**
```
GMAIL_SENDER=woodychang891121@gmail.com
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
GMAIL_APP_PASSWORD=<16-char Google app password — local SMTP fallback only>
```

**Scheduled trigger:**
- ID: `trig_019Dkp8WBdZ3ZPen7YaUb861`
- Runs every Monday at 9:00 AM America/Toronto (1:00 PM UTC)
- Managed at: https://claude.ai/code/scheduled/trig_019Dkp8WBdZ3ZPen7YaUb861
- Clones this GitHub repo, creates `.env` from embedded credentials, runs the skill

### job-hunt

**Location:** `.claude/skills/job-hunt/`
**Purpose:** Daily pipeline that searches for ML/AI new grad roles in Canada + USA, scores them against the user's resume, generates tailored resume content per role, and writes structured entries into the Notion "Job Leads" database. User reviews leads and applies manually.

**Job filters (strictly enforced):**
- Title: "Machine Learning Engineer" OR "ML Engineer" OR "AI Engineer" only
- Seniority: New Grad / Entry Level / Junior / 0–2 years only
- Location: Canada OR United States only
- Recency: Posted within the last 3 days only

**How it works:**
1. Reads `Resume.pdf` and extracts skills, experience, projects, education
2. Runs 8 parallel WebSearch queries targeting LinkedIn, Greenhouse, Lever, Workday, Ashby
3. Hard-filters by title + seniority + location + recency; scores survivors (1–10); keeps top 10 with score ≥ 5
4. WebFetches each job URL, generates tailored resume content per JD
5. Writes each lead as a Notion page + child "Tailored Resume" page via **Notion MCP tools** (`notion-create-pages`)
6. Prints a ranked summary

**Resume:** `.claude/skills/job-hunt/resume/Resume.pdf` (gitignored — local only)

**Notion MCP connector:**
- Connector UUID: `69f3a300-cc60-48c4-b237-dfac56530dbf`
- URL: `https://mcp.notion.com/mcp`
- Job Leads DB ID: `3499719ac5f4800da543c5b965c4003b`
- Applied Jobs DB ID: `78350949d774433298f637436df32623`

**How to run:** Trigger locally with `/job-hunt`. CCR scheduled trigger is disabled — `api.notion.com` is blocked in Anthropic's CCR egress allowlist, so Notion writes only work locally.

### skill-creator

**Location:** `.claude/skills/skill-creator/`
**Purpose:** Scaffolds new skills — creates the `SKILL.md`, `scripts/`, and `evals/` structure.

---

## Agents

Agent definitions live in `agents/<name>.md`. These are subagent personas Claude can adopt.

| Agent | Purpose |
|---|---|
| `code-reviewer.md` | Reviews code for quality, security, and correctness |
| `email-classifier.md` | Classifies and prioritises incoming emails |
| `qa.md` | QA testing and bug reporting |
| `research.md` | Deep research and summarisation |

---

## MCP Servers

### Local MCP servers (`.mcp-servers/`)

These run as subprocesses on the local machine only. Not available to remote scheduled agents.

**chrome-devtools-mcp** — Bridges Claude to Chrome DevTools Protocol (CDP) on `localhost:9222`.

Setup:
```bash
cd .mcp-servers/chrome-devtools-mcp
uv sync   # or: pip install -r requirements.txt
```

Chrome must be launched with `--remote-debugging-port=9222` before connecting.

Dev commands:
```bash
uv run ruff format .
uv run ruff check .
uv run mypy src/
uv run pytest
```

**gmail-mcp** — Local Gmail MCP server with `send_email` capability. Configured in `.mcp.json`.

### Cloud MCP connectors (claude.ai)

These are available to remote scheduled agents via `mcp_connections` in trigger config.

| Connector | UUID | URL | Capability |
|---|---|---|---|
| Gmail | `d3cfd847-88a5-4e59-9787-ad367362ac2f` | `https://gmailmcp.googleapis.com/mcp/v1` | Draft, label, search |

> Note: The cloud Gmail connector can only create drafts — it cannot send. `send_email.py` handles actual sending via Gmail API (OAuth2), which works from both local and remote CCR environments.

---

## Environment Variables

**Local `.env`** (never commit):
```
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
GMAIL_SENDER=woodychang891121@gmail.com
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
GMAIL_APP_PASSWORD=...
```

**`.env.example`** — committed template showing required keys without values.

---

## Scheduled Remote Agents

Remote agents run in Anthropic's cloud (CCR). They clone this GitHub repo and cannot access local files, local MCP servers, or `.env`.

| Trigger | Schedule | What it does |
|---|---|---|
| AI Newsletter | Every Monday 9am Toronto | Searches AI news, sends HTML email to woodychang891121@gmail.com |

**Important for remote agents:**
- Always clone from `https://github.com/WoodyChang21/Personal_Claude`
- Credentials must be embedded in the trigger prompt (not sourced from `.env`)
- Use `send_email.py` for sending — it uses Gmail API (OAuth2), which works in CCR
- Keep this repo up to date — remote agents pull the latest code at runtime
