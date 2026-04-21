#!/usr/bin/env python3
"""Send an HTML email. Tries Gmail API first, then Gmail SMTP fallback."""

import argparse
import base64
import json
import smtplib
import sys
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


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


def _get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["access_token"]


def send_via_gmail_api(html_content: str, subject: str, to: str, sender: str,
                       client_id: str, client_secret: str, refresh_token: str) -> None:
    access_token = _get_access_token(client_id, client_secret, refresh_token)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode(),
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"Gmail API returned HTTP {resp.status}")
    print(f"Email sent to {to} via Gmail API")


def send_via_smtp(html_content: str, subject: str, to: str, sender: str, password: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, password)
        smtp.sendmail(sender, [to], msg.as_string())
    print(f"Email sent to {to} via Gmail SMTP")


def send(html_path: str, subject: str, to: str) -> None:
    env = load_env(Path.cwd())
    html_content = Path(html_path).read_text(encoding="utf-8")
    sender = env.get("GMAIL_SENDER", "").strip()

    client_id = env.get("GMAIL_CLIENT_ID", "").strip()
    client_secret = env.get("GMAIL_CLIENT_SECRET", "").strip()
    refresh_token = env.get("GMAIL_REFRESH_TOKEN", "").strip()

    if client_id and client_secret and refresh_token and sender:
        try:
            send_via_gmail_api(html_content, subject, to, sender, client_id, client_secret, refresh_token)
            return
        except Exception as e:
            print(f"Gmail API failed ({e}), falling back to SMTP...", file=sys.stderr)

    password = env.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    if not sender or not password:
        print("ERROR: No valid credentials found. Set GMAIL_CLIENT_ID/SECRET/REFRESH_TOKEN or GMAIL_SENDER+GMAIL_APP_PASSWORD in .env", file=sys.stderr)
        sys.exit(1)

    send_via_smtp(html_content, subject, to, sender, password)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--to", required=True)
    args = parser.parse_args()
    send(args.html, args.subject, args.to)
