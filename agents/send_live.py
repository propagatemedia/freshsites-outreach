#!/usr/bin/env python3
"""Send a single live prospect email from FreshSites.

Usage: send_live.py <slug>
Reads the lead from the DB, generates the email, and sends via SMTP relay.
From: freshsites@sites.propagate.media (set in email body by emailer.py)
Reply-To: freshsites@sites.propagate.media
"""
from __future__ import annotations

import json
import re
import smtplib
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "leads" / "freshsites.db"
SENDER = "freshsites@sites.propagate.media"
SMTP_HOST = "c1100730.sgvps.net"
SMTP_LOGIN = "freshsites@sites.propagate.media"
REVIEW_FALLBACK = "tyrone@propagate.media"  # only used if lead email is empty


def get_password():
    r = subprocess.run(
        [str(Path.home() / ".config/himalaya/get-password.sh"), SMTP_LOGIN],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("could not read SMTP relay password")
    return r.stdout.strip()


def get_lead(slug: str) -> dict:
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM leads WHERE demo_url LIKE ?", (f"%/{slug}.html",)).fetchone()
    conn.close()
    if not row:
        raise SystemExit(f"no lead found for slug {slug}")
    return dict(row)


def send(slug: str) -> bool:
    sys.path.insert(0, str(REPO / "agents"))
    from emailer import generate_email

    lead = get_lead(slug)
    to_email = lead.get("email") or ""
    if not to_email:
        print(f"BLOCKED: no email for {slug}")
        return False

    raw, _original_to = generate_email(lead)

    # Now sending directly from the real freshsites@sites.propagate.media mailbox
    # (credentials fixed 2026-09) - no relay workaround needed. From: is already
    # correct in the generated body. Ensure Reply-To is set explicitly.
    header, body = raw.split("\n\n", 1)
    if "Reply-To:" not in header:
        header = header.rstrip() + f"\nReply-To: {SENDER}"
    raw = header + "\n\n" + body

    # Rewrite To: to the real prospect (emailer may have used a guess)
    raw = re.sub(r"^To:.*$", f"To: {to_email}", raw, count=1, flags=re.M)

    pw = get_password()
    with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=45) as smtp:
        smtp.login(SMTP_LOGIN, pw)
        smtp.sendmail(SMTP_LOGIN, [to_email], raw.encode("utf-8"))

    subj = re.search(r"^Subject:\s*(.+)$", raw, re.M)
    print(f"SENT LIVE {slug} -> {to_email} | {subj.group(1).strip() if subj else ''}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send_live.py <slug>")
        sys.exit(1)
    ok = send(sys.argv[1])
    sys.exit(0 if ok else 1)