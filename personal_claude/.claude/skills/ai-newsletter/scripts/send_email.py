#!/usr/bin/env python3
"""Send an HTML email via Gmail SMTP. Reads credentials from .env in cwd or parent dirs."""

import argparse
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def load_env(start_dir: Path) -> dict:
    """Walk up from start_dir looking for a .env file and parse it."""
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


def send(html_path: str, subject: str, to: str) -> None:
    env = load_env(Path.cwd())

    sender = env.get("GMAIL_SENDER", "").strip()
    password = env.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()

    if not sender:
        print("ERROR: GMAIL_SENDER not found in .env", file=sys.stderr)
        sys.exit(1)
    if not password:
        print("ERROR: GMAIL_APP_PASSWORD not found in .env", file=sys.stderr)
        sys.exit(1)

    html_content = Path(html_path).read_text(encoding="utf-8")

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

    print(f"Email sent to {to}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True, help="Path to HTML file")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--to", required=True, help="Recipient email")
    args = parser.parse_args()
    send(args.html, args.subject, args.to)
