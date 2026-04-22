#!/usr/bin/env python3
"""Notion API client for the job-hunt pipeline. Pure stdlib, no third-party deps."""

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def load_env(start_dir: Path) -> dict:
    current = start_dir.resolve()
    for _ in range(6):
        env_file = current / ".env"
        if env_file.exists():
            env = {}
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
            return env
        current = current.parent
    return {}


def _notion_request(method: str, path: str, token: str, body: dict | None = None) -> dict:
    url = f"{NOTION_API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f"Notion API error {e.code} on {method} {path}: {body_text}", file=sys.stderr)
        raise


def create_job_lead_page(token: str, database_id: str, job: dict) -> str:
    """Create a row in the Job Leads database. Returns the new page_id."""
    properties = {
        "Name": {"title": [{"text": {"content": f"{job['role']} @ {job['company']}"}}]},
        "Company": {"rich_text": [{"text": {"content": job.get("company", "")}}]},
        "Role": {"rich_text": [{"text": {"content": job.get("role", "")}}]},
        "Location": {"rich_text": [{"text": {"content": job.get("location", "")}}]},
        "Job URL": {"url": job.get("url", "")},
        "Status": {"select": {"name": "New"}},
        "Date Found": {"date": {"start": job.get("date_found", "")}},
        "Match Score": {"number": job.get("score", 0)},
        "Source": {"rich_text": [{"text": {"content": job.get("source", "")}}]},
    }
    result = _notion_request("POST", "/pages", token, {
        "parent": {"database_id": database_id},
        "properties": properties,
    })
    return result["id"]


def create_tailored_resume_child(token: str, parent_page_id: str, blocks: list) -> str:
    """Create a child page titled 'Tailored Resume' under the job lead page."""
    child_page = _notion_request("POST", "/pages", token, {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {"title": [{"text": {"content": "Tailored Resume"}}]},
        },
    })
    child_id = child_page["id"]

    # Append blocks in batches of 100 (Notion limit)
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i + 100]
        _notion_request("PATCH", f"/blocks/{child_id}/children", token, {"children": batch})
        if i + 100 < len(blocks):
            time.sleep(0.4)

    return child_id


def build_resume_blocks(rationale: str, skills: list[str], experience: list[dict],
                        projects: list[dict], education: str, role: str, company: str) -> list:
    """Convert structured resume data into Notion block JSON."""
    blocks = []

    blocks.append({"object": "block", "type": "heading_1", "heading_1": {
        "rich_text": [{"type": "text", "text": {"content": f"Tailored Resume — {role} @ {company}"}}]
    }})

    blocks.append({"object": "block", "type": "paragraph", "paragraph": {
        "rich_text": [{"type": "text", "text": {"content": rationale}}]
    }})

    if skills:
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "Relevant Skills"}}]
        }})
        for skill in skills:
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": skill}}]
            }})

    if experience:
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "Work Experience"}}]
        }})
        for exp in experience:
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {
                    "content": f"{exp.get('role', '')} at {exp.get('company', '')} ({exp.get('dates', '')})"
                }, "annotations": {"bold": True}}]
            }})
            for bullet in exp.get("bullets", []):
                blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": bullet}}]
                }})

    if projects:
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "Projects"}}]
        }})
        for proj in projects:
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {
                    "content": proj.get("name", "")
                }, "annotations": {"bold": True}}]
            }})
            if proj.get("description"):
                blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": proj["description"]}}]
                }})

    if education:
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "Education"}}]
        }})
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": education}}]
        }})

    return blocks


def check_duplicate(token: str, job_leads_db: str, applied_jobs_db: str, title: str) -> bool:
    """Return True if title already exists in either database."""
    payload = {"query": title, "filter": {"value": "page", "property": "object"}}
    result = _notion_request("POST", "/search", token, payload)
    for page in result.get("results", []):
        parent = page.get("parent", {})
        parent_id = parent.get("database_id", "").replace("-", "")
        if parent_id in (job_leads_db.replace("-", ""), applied_jobs_db.replace("-", "")):
            page_title = ""
            props = page.get("properties", {})
            for prop in props.values():
                if prop.get("type") == "title":
                    parts = prop.get("title", [])
                    if parts:
                        page_title = parts[0].get("plain_text", "")
                    break
            if page_title.lower() == title.lower():
                return True
    return False


def append_body_note(token: str, page_id: str, note: str, changes: list[str]) -> None:
    """Append a tailoring rationale note directly to an existing page."""
    blocks = [
        {"object": "block", "type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": note}}]
        }},
        {"object": "block", "type": "heading_3", "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": "Key Resume Changes"}}]
        }},
    ]
    for change in changes:
        blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": change}}]
        }})
    _notion_request("PATCH", f"/blocks/{page_id}/children", token, {"children": blocks})


def cmd_check_duplicate(args):
    env = load_env(Path.cwd())
    token = args.token or env.get("NOTION_TOKEN", "")
    job_leads_db = args.job_leads_db or env.get("JOB_LEADS_DB_ID", "")
    applied_db = args.applied_db or env.get("APPLIED_JOBS_DB_ID", "")
    found = check_duplicate(token, job_leads_db, applied_db, args.title)
    print("duplicate" if found else "new")


def cmd_add_body_note(args):
    env = load_env(Path.cwd())
    token = args.token or env.get("NOTION_TOKEN", "")
    data = json.loads(Path(args.note_json).read_text(encoding="utf-8"))
    append_body_note(token, args.page_id, data["note"], data.get("changes", []))
    print("ok")


def cmd_create_page(args):
    env = load_env(Path.cwd())
    token = args.token or env.get("NOTION_TOKEN", "")
    db_id = args.db_id or env.get("JOB_LEADS_DB_ID", "")
    job = json.loads(Path(args.job_json).read_text(encoding="utf-8"))
    page_id = create_job_lead_page(token, db_id, job)
    print(page_id)


def cmd_append_resume(args):
    env = load_env(Path.cwd())
    token = args.token or env.get("NOTION_TOKEN", "")
    blocks = json.loads(Path(args.blocks_json).read_text(encoding="utf-8"))
    child_id = create_tailored_resume_child(token, args.page_id, blocks)
    print(child_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create-page")
    p_create.add_argument("--token", default="")
    p_create.add_argument("--db-id", default="")
    p_create.add_argument("--job-json", required=True)

    p_resume = sub.add_parser("append-resume")
    p_resume.add_argument("--token", default="")
    p_resume.add_argument("--page-id", required=True)
    p_resume.add_argument("--blocks-json", required=True)

    p_dup = sub.add_parser("check-duplicate")
    p_dup.add_argument("--token", default="")
    p_dup.add_argument("--job-leads-db", default="")
    p_dup.add_argument("--applied-db", default="")
    p_dup.add_argument("--title", required=True)

    p_note = sub.add_parser("add-body-note")
    p_note.add_argument("--token", default="")
    p_note.add_argument("--page-id", required=True)
    p_note.add_argument("--note-json", required=True)

    args = parser.parse_args()
    if args.command == "create-page":
        cmd_create_page(args)
    elif args.command == "append-resume":
        cmd_append_resume(args)
    elif args.command == "check-duplicate":
        cmd_check_duplicate(args)
    elif args.command == "add-body-note":
        cmd_add_body_note(args)
