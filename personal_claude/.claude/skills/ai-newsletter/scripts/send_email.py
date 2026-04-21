#!/usr/bin/env python3
"""Send an HTML email. Tries SendGrid API first (HTTPS), falls back to Gmail SMTP."""

import argparse
import json
import smtplib
import sys
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


def send_via_sendgrid(html_content: str, subject: str, to: str, sender: str, api_key: str) -> None:
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": sender},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}],
    }
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status not in (200, 202):
            raise RuntimeError(f"SendGrid returned HTTP {resp.status}")
    print(f"Email sent to {to} via SendGrid")


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

    sendgrid_key = env.get("SENDGRID_API_KEY", "").strip()
    sender = env.get("GMAIL_SENDER", "").strip()

    if sendgrid_key and sender:
        try:
            send_via_sendgrid(html_content, subject, to, sender, sendgrid_key)
            return
        except Exception as e:
            print(f"SendGrid failed ({e}), falling back to SMTP...", file=sys.stderr)

    password = env.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    if not sender or not password:
        print("ERROR: No valid credentials found. Set SENDGRID_API_KEY or GMAIL_SENDER+GMAIL_APP_PASSWORD in .env", file=sys.stderr)
        sys.exit(1)

    send_via_smtp(html_content, subject, to, sender, password)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--to", required=True)
    args = parser.parse_args()
    send(args.html, args.subject, args.to)
