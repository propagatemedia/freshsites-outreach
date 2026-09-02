#!/usr/bin/env python3
"""SMS lead tracker for Google-Maps businesses with NO website at all.

These leads can't get a demo (nothing to audit/rebuild against), so they get routed
to SMS outreach instead of email. This script:
1. Stores no-website leads in leads/sms_leads.db (separate table, same DB file as freshsites.db)
2. Sends a short qualifying SMS via Twilio (credentials from ~/propagate-media/.env)
3. Tracks status: new -> sms_sent -> replied / no_reply / opted_out

SAFETY: This sends REAL SMS to REAL phone numbers. Never run send without explicit
approval for that specific batch. Always dry-run first (--dry-run).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "leads" / "freshsites.db"
ENV_FILE = Path.home() / "propagate-media" / ".env"

SMS_TEMPLATE = (
    "Hi, this is Propagate Media - we help local {trade} businesses in Wales get "
    "found online. Noticed {name} doesn't have a website listed on Google. "
    "Would a simple, affordable one-page site help you get more enquiries? "
    "Reply YES for a quick example, or STOP to opt out."
)


def init_db():
    DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sms_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            trade TEXT,
            phone TEXT NOT NULL,
            address TEXT,
            town TEXT,
            category_raw TEXT,
            rating REAL,
            reviews_count INTEGER,
            source TEXT DEFAULT 'google_maps',
            status TEXT DEFAULT 'new',
            sms_body TEXT,
            sms_sid TEXT,
            sent_at TEXT,
            reply_text TEXT,
            reply_at TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(phone, name)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_sms_status ON sms_leads(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sms_town ON sms_leads(town)")
    conn.commit()
    conn.close()


def normalize_uk_phone(raw: str) -> str:
    """Convert +44 7xxx / 07xxx / 01xxx formats to clean E.164."""
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits.startswith("+44"):
        return digits
    if digits.startswith("44"):
        return "+" + digits
    if digits.startswith("0"):
        return "+44" + digits[1:]
    return digits


from typing import Optional

def add_lead(name: str, trade: str, phone: str, address: str = "", town: str = "",
             category_raw: str = "", rating: Optional[float] = None, reviews_count: Optional[int] = None) -> int:
    init_db()
    phone_norm = normalize_uk_phone(phone)
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO sms_leads (name, trade, phone, address, town, category_raw, rating, reviews_count, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
        """, (name, trade, phone_norm, address, town, category_raw, rating, reviews_count, now, now))
        conn.commit()
        lead_id = c.lastrowid
        print(f"Added: {name} ({trade}) {phone_norm}")
    except sqlite3.IntegrityError:
        print(f"Skipped (duplicate): {name} {phone_norm}")
        lead_id = -1
    conn.close()
    return lead_id


def add_leads_from_json(path: str):
    """Bulk-add from a JSON file: list of {name, trade, phone, address, town, category_raw, rating, reviews_count}."""
    data = json.loads(Path(path).read_text())
    added = 0
    for item in data:
        if not item.get("phone"):
            print(f"SKIP (no phone): {item.get('name')}")
            continue
        lid = add_lead(
            name=item.get("name", ""),
            trade=item.get("trade", item.get("category_raw", "")),
            phone=item["phone"],
            address=item.get("address", ""),
            town=item.get("town", ""),
            category_raw=item.get("category_raw", ""),
            rating=item.get("rating"),
            reviews_count=item.get("reviews_count"),
        )
        if lid != -1:
            added += 1
    print(f"\nAdded {added} new leads from {path}")


def list_leads(status: Optional[str] = None, town: Optional[str] = None):
    init_db()
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    q = "SELECT * FROM sms_leads WHERE 1=1"
    params = []
    if status:
        q += " AND status=?"
        params.append(status)
    if town:
        q += " AND town=?"
        params.append(town)
    q += " ORDER BY created_at DESC"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


def load_twilio_env():
    if not ENV_FILE.exists():
        raise RuntimeError(f"Twilio env file not found: {ENV_FILE}")
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    required = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"]
    missing = [k for k in required if not env.get(k)]
    if missing:
        raise RuntimeError(f"Missing Twilio env vars: {missing}")
    return env


def send_sms(to_number: str, body: str, from_number: Optional[str] = None) -> dict:
    """Send one SMS via Twilio REST API using curl (no extra deps)."""
    env = load_twilio_env()
    sid = env["TWILIO_ACCOUNT_SID"]
    token = env["TWILIO_AUTH_TOKEN"]
    frm = from_number or env.get("TWILIO_PHONE_NUMBER")
    if not frm:
        raise RuntimeError("No from_number given and TWILIO_PHONE_NUMBER not set")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    cmd = [
        "curl", "-s", "-u", f"{sid}:{token}", url,
        "--data-urlencode", f"To={to_number}",
        "--data-urlencode", f"From={frm}",
        "--data-urlencode", f"Body={body}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        data = json.loads(r.stdout)
    except Exception:
        data = {"error": r.stdout or r.stderr}
    return data


def send_batch(lead_ids: list[int], dry_run: bool = True, from_number: Optional[str] = None):
    init_db()
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    for lid in lead_ids:
        row = conn.execute("SELECT * FROM sms_leads WHERE id=?", (lid,)).fetchone()
        if not row:
            print(f"Lead {lid} not found")
            continue
        lead = dict(row)
        if lead["status"] not in ("new",):
            print(f"SKIP {lead['name']}: status is '{lead['status']}', not 'new'")
            continue
        body = SMS_TEMPLATE.format(trade=lead.get("trade") or "trade", name=lead["name"])
        if dry_run:
            print(f"[DRY RUN] Would SMS {lead['name']} ({lead['phone']}):\n  {body}\n")
            continue
        result = send_sms(lead["phone"], body, from_number=from_number)
        now = datetime.utcnow().isoformat()
        if result.get("sid"):
            conn.execute(
                "UPDATE sms_leads SET status='sms_sent', sms_body=?, sms_sid=?, sent_at=?, updated_at=? WHERE id=?",
                (body, result["sid"], now, now, lid),
            )
            conn.commit()
            print(f"SENT to {lead['name']} ({lead['phone']}) sid={result['sid']}")
        else:
            print(f"FAILED for {lead['name']} ({lead['phone']}): {result}")
    conn.close()


def main():
    ap = argparse.ArgumentParser(description="SMS lead tracker for no-website Google Maps businesses")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add-json", help="Bulk-add leads from a JSON file")
    p_add.add_argument("path")

    p_list = sub.add_parser("list", help="List leads")
    p_list.add_argument("--status")
    p_list.add_argument("--town")

    p_send = sub.add_parser("send", help="Send SMS to specific lead IDs")
    p_send.add_argument("ids", nargs="+", type=int)
    p_send.add_argument("--live", action="store_true", help="Actually send (default is dry-run)")
    p_send.add_argument("--from-number")

    args = ap.parse_args()

    if args.cmd == "add-json":
        add_leads_from_json(args.path)
    elif args.cmd == "list":
        rows = list_leads(status=args.status, town=args.town)
        for r in rows:
            print(f"[{r['id']}] {r['name']:35} {r['trade'] or '-':20} {r['phone']:15} status={r['status']} town={r['town']}")
        print(f"\nTotal: {len(rows)}")
    elif args.cmd == "send":
        send_batch(args.ids, dry_run=not args.live, from_number=args.from_number)


if __name__ == "__main__":
    main()
