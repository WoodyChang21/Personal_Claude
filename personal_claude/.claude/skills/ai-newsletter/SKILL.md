---
name: ai-newsletter
description: >
  Searches for the latest AI technology news, summarizes it in plain language, generates a
  visually appealing HTML email newsletter, and sends it to woodychang891121@gmail.com.

  Use this skill whenever the user asks to: send an AI newsletter, generate an AI digest,
  create an AI news email, check what's new in AI, "give me today's AI news", or any similar
  request involving AI news summarized and delivered by email. Also trigger when the user
  says things like "run my newsletter", "send the daily AI update", or "what's happening in AI today".

  This is the user's daily AI digest workflow — invoke it proactively whenever the context
  suggests they want to stay up to date on AI.
---

# AI Newsletter Skill

This skill runs a full pipeline: search → summarize → generate HTML → send email.

## Prerequisites

The `.env` file in the project root must contain:
```
GMAIL_APP_PASSWORD=<16-char app password from Google>
GMAIL_SENDER=woodychang891121@gmail.com
```

If `GMAIL_APP_PASSWORD` is missing, stop and ask the user to add it before proceeding.
See the "Gmail App Password Setup" section at the bottom if the user needs help.

## Step 1 — Search for Latest AI News

### Phase A — Discovery (run in parallel)

Run these 3 broad queries first to surface what's actually trending this week:

1. `AI news this week {TODAY_DATE}`
2. `artificial intelligence announcements {TODAY_DATE}`
3. `AI model release research breakthrough {TODAY_DATE}`

Scan the results and extract 5–8 **specific trending topics** (e.g. "GPT-5 release", "Llama 4 benchmark", "MCP tool ecosystem", "AI chip shortage", "Claude 4 pricing"). These are the actual stories dominating coverage right now.

### Phase B — Targeted deep-dives (run in parallel)

For each trending topic you identified, run one focused query:
- `"{TOPIC}" site:techcrunch.com OR site:theverge.com OR site:venturebeat.com OR site:wired.com OR site:huggingface.co OR site:arxiv.org`

Add 2–3 evergreen catch-all queries to fill any gaps:
- `"AI developer tools" OR "AI APIs" released {THIS_WEEK}`
- `"AI research paper" OR "AI open source" {THIS_WEEK}`

This ensures coverage adapts to what's actually happening rather than searching fixed categories.

### Collecting stories

Collect 8–12 stories total. For each story, note:
- Title
- Source / publication
- URL
- A 1–2 sentence raw summary of what happened

Discard duplicates and anything older than 7 days.

## Step 2 — Summarize and Explain

For each story, write:
- **Headline**: a punchy 1-line title (rewrite if the original is jargon-heavy)
- **Summary**: 2–3 sentences in plain English — what happened, no acronym soup
- **Why it matters**: 1 sentence explaining the real-world significance for someone who
  follows AI but isn't a researcher

Group stories into 2–4 of these categories (only use categories you have content for):
- Anthropic & Claude
- Tools & Infrastructure (MCP, agents, SDKs)
- Big Lab News (OpenAI, Google, Meta, Mistral…)
- Research & Breakthroughs
- Industry & Business

## Step 3 — Generate the HTML Newsletter

Build a complete, self-contained HTML file using the template below.
Replace all `{{PLACEHOLDER}}` tokens with real content.

Key design rules:
- Inline all CSS (many email clients strip `<style>` tags)
- Keep width ≤ 600px for email client compatibility
- Do not use JavaScript or external fonts
- Images are optional — skip them if no URL is available

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Daily Digest — {{DATE}}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

<!-- Wrapper -->
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);padding:36px 40px;border-radius:12px 12px 0 0;text-align:center;">
      <p style="margin:0 0 8px 0;font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#7c83fd;">DAILY DIGEST</p>
      <h1 style="margin:0;font-size:28px;font-weight:700;color:#ffffff;line-height:1.2;">⚡ AI Newsletter</h1>
      <p style="margin:10px 0 0 0;font-size:14px;color:#a0a8c8;">{{DATE}} &nbsp;·&nbsp; {{STORY_COUNT}} stories</p>
    </td>
  </tr>

  <!-- Intro bar -->
  <tr>
    <td style="background:#7c83fd;padding:12px 40px;text-align:center;">
      <p style="margin:0;font-size:13px;color:#ffffff;font-weight:500;">
        Your curated round-up of the latest in AI — from Claude to GPT and everything in between.
      </p>
    </td>
  </tr>

  <!-- Body -->
  <tr>
    <td style="background:#ffffff;padding:32px 40px;border-radius:0 0 12px 12px;">

      {{SECTIONS}}

      <!-- Footer -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:32px;border-top:1px solid #e8e8f0;">
        <tr>
          <td style="padding-top:20px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#9a9ab0;">
              Generated by Claude Code &nbsp;·&nbsp; {{DATE}}<br>
              To unsubscribe, reply with "unsubscribe".
            </p>
          </td>
        </tr>
      </table>

    </td>
  </tr>

</table>
</td></tr>
</table>

</body>
</html>
```

### Section Template (repeat for each category)

```html
<!-- Section: {{SECTION_TITLE}} -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
  <tr>
    <td>
      <h2 style="margin:0 0 16px 0;font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#7c83fd;border-bottom:2px solid #f0f0f8;padding-bottom:8px;">
        {{SECTION_TITLE}}
      </h2>
      {{STORIES_IN_SECTION}}
    </td>
  </tr>
</table>
```

### Story Template (repeat for each story within a section)

```html
<!-- Story -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;background:#f8f8fc;border-radius:8px;border-left:3px solid #7c83fd;">
  <tr>
    <td style="padding:16px 20px;">
      <h3 style="margin:0 0 8px 0;font-size:16px;font-weight:600;color:#1a1a2e;line-height:1.3;">
        <a href="{{STORY_URL}}" style="color:#1a1a2e;text-decoration:none;">{{STORY_HEADLINE}}</a>
      </h3>
      <p style="margin:0 0 10px 0;font-size:14px;color:#4a4a6a;line-height:1.6;">
        {{STORY_SUMMARY}}
      </p>
      <p style="margin:0;font-size:13px;color:#7c83fd;font-style:italic;line-height:1.4;">
        💡 {{STORY_WHY_IT_MATTERS}}
      </p>
      <p style="margin:8px 0 0 0;font-size:11px;color:#9a9ab0;">
        {{STORY_SOURCE}} &nbsp;·&nbsp; <a href="{{STORY_URL}}" style="color:#7c83fd;">Read more →</a>
      </p>
    </td>
  </tr>
</table>
```

Save the final HTML to a temp file: `/tmp/ai_newsletter_{{DATE_NODASH}}.html`

## Step 4 — Send the Email

Load `.env` from the project root. Then run the bundled send script:

```bash
python .claude/skills/ai-newsletter/scripts/send_email.py \
  --html /tmp/ai_newsletter_{{DATE_NODASH}}.html \
  --subject "⚡ AI Daily Digest — {{DATE}}" \
  --to woodychang891121@gmail.com
```

The script reads `GMAIL_SENDER` and `GMAIL_APP_PASSWORD` from the `.env` file automatically.

If the script exits with a non-zero code, show the error to the user and suggest checking their app password.

## Step 5 — Confirm

Tell the user:
- How many stories were included
- Which categories were covered
- That the email was sent to woodychang891121@gmail.com
- The subject line

---

## Gmail App Password Setup

The user needs this if `GMAIL_APP_PASSWORD` is not set:

1. Go to myaccount.google.com → Security
2. Enable **2-Step Verification** (required)
3. Go to Security → **App passwords**
4. Choose "Mail" + "Windows Computer", click Generate
5. Copy the 16-character password (no spaces)
6. Add to `.env`:
   ```
   GMAIL_APP_PASSWORD=xxxxxxxxxxxx xxxx
   GMAIL_SENDER=woodychang891121@gmail.com
   ```
