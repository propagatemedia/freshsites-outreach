#!/usr/bin/env python3
"""
FreshSites Email Outreach Agent v2
Generates and sends personalized emails to scored leads.
Uses Himalaya CLI for email delivery.

Usage:
    PYTHONPATH="" ./.venv/bin/python3.11 agents/emailer.py
    PYTHONPATH="" ./.venv/bin/python3.11 agents/emailer.py --send
"""

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
HIMALAYA_BIN = Path.home() / ".local" / "bin" / "himalaya"
SENDER_EMAIL = "freshsites@sites.propagate.media"
SENDER_NAME = "FreshSites by Propagate Media"

# Ensure agents/ is on path for imports
sys.path.insert(0, str(Path(__file__).parent))
from scoring_v3 import WEAKNESS_MAP, get_weaknesses_v3


# ── Email Templates ────────────────────────────────────────────────
EMAIL_TEMPLATES = {
    "initial": """From: {sender_name} <{sender_email}>
To: {recipient_name} <{recipient_email}>
Subject: I built {business_name} a better homepage
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Inter,Helvetica,sans-serif;color:#1a1a1a;background:#fff;margin:0;padding:0;">
<div style="max-width:600px;margin:0 auto;padding:40px 24px;">
  <div style="border-bottom:2px solid #c41e3a;padding-bottom:16px;margin-bottom:24px;">
    <strong style="font-size:1.2rem;color:#0A0A0A;">FreshSites</strong>
    <span style="float:right;font-size:0.8rem;color:#888;">by Propagate Media</span>
  </div>

  <p style="font-size:1.05rem;line-height:1.6;">Hi there,</p>

  <p style="font-size:1.05rem;line-height:1.6;">I run <strong>FreshSites</strong> - we build fast, conversion-focused landing pages for local businesses. I came across <strong>{business_name}</strong> and saw the good work you do.</p>

  <p style="font-size:1.05rem;line-height:1.6;">Your current site has room to improve — we rate it <strong>{original_score}/10</strong> on our conversion-readiness checklist. Here is what it is missing that costs you bookings:</p>

  <ul style="font-size:1rem;line-height:1.7;color:#555;padding-left:20px;">
    {gaps_html}
  </ul>

  <p style="font-size:1.05rem;line-height:1.6;">So I built you a demo that fixes all of this - using your brand colours and info, but designed to convert:</p>

  <div style="background:#1a1a1a;border-radius:8px;padding:24px;margin:24px 0;text-align:center;">
    <p style="color:#F1C204;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:8px;">YOUR DEMO PAGE</p>
    <a href="{demo_url}" style="color:#F1C204;font-size:1.1rem;font-weight:700;text-decoration:underline;">View Your Demo</a>
  </div>

  <p style="font-size:1.05rem;line-height:1.6;">To buy this page outright, it is 149, once off, you own it, host it anywhere, tweak it however you like. No monthly fees, no lock-in.</p>

  <p style="font-size:1.05rem;line-height:1.6;">Want changes? We can add your logo, swap photos, or adjust anything. Just reply.</p>

  <div style="margin-top:32px;padding-top:24px;border-top:1px solid #eee;">
    <p style="font-size:0.9rem;color:#555;">Questions? Just reply to this email.</p>
    <p style="font-size:0.85rem;color:#888;margin-top:8px;">- FreshSites by Propagate Media</p>
    <p style="font-size:0.8rem;color:#aaa;margin-top:16px;">FreshSites is a division of Propagate Media. Call us on 07400 33 8941. For more information or to view our portfolio, visit propagate.media/clients</p>
  </div>
</div>
</body>
</html>""",
}


def get_leads_to_email():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, name, email, website, score, score_breakdown, demo_url, status
        FROM leads
        WHERE status IN ('demo_built', 'emailed')
        AND demo_url IS NOT NULL AND demo_url != ''
        ORDER BY score ASC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


GAP_FIXES = {
    "no_h1": "No clear headline telling visitors what you do in 2 seconds",
    "weak_value_prop": "No compelling reason to choose you over the garage down the road",
    "no_cta_above_fold": "No call-to-action button visible without scrolling",
    "phone_hidden": "Phone number buried or missing - mobile visitors have to hunt for it",
    "no_opening_hours": "No opening hours displayed - visitors do not know when to call",
    "no_contact_form": "No contact form - visitors who prefer email have no way to reach you",
    "social_proof": "No reviews or testimonials to build trust",
    "no_personal_touch": "No team names or faces - looks like a faceless operation",
    "no_location": "No address visible - visitors cannot find you",
    "generic_title": "Page title is generic - hurts Google rankings",
    "builder_bloat": "Slow loading due to unnecessary scripts",
    "weak_mobile": "Poor mobile experience - 70% of visitors are on phones",
}

def format_gaps(score_breakdown: str) -> str:
    """Convert score breakdown to specific gap/fix list items."""
    try:
        bd = json.loads(score_breakdown)
    except:
        return "<li>Homepage could convert more visitors into customers</li>"

    significant = [(k, v) for k, v in bd.items() if v > 0.3]
    items = []
    for k, _ in significant[:4]:
        desc = GAP_FIXES.get(k, k.replace("_", " ").title())
        items.append(f"<li>{desc}</li>")

    if not items:
        items = ["<li>Homepage could convert more visitors into customers</li>"]

    return "\n    ".join(items)


def generate_email(lead: dict, template: str = "initial") -> tuple[str, str]:
    """Generate HTML email for a lead."""
    name = lead["name"]
    email = lead["email"] or guess_email(lead["website"], name)
    gaps = format_gaps(lead["score_breakdown"])
    original_score = lead.get("score", 0)

    email_body = EMAIL_TEMPLATES[template].format(
        sender_name=SENDER_NAME,
        sender_email=SENDER_EMAIL,
        recipient_name="there",
        recipient_email=email,
        business_name=name,
        demo_url=lead["demo_url"],
        gaps_html=gaps,
        original_score=original_score,
    )
    return email_body, email


def guess_email(website: str, business_name: str) -> str:
    """Best-guess email from domain."""
    if not website:
        return ""
    domain = re.sub(r"^https?://", "", website).replace("www.", "").rstrip("/")
    domain = domain.split("/")[0]
    if not domain:
        return ""
    guesses = [
        f"info@{domain}",
        f"hello@{domain}",
        f"contact@{domain}",
        f"enquiries@{domain}",
    ]
    return guesses[0]


def send_via_himalaya(email_raw: str, to_email: str) -> bool:
    """Send email using Himalaya CLI."""
    if not HIMALAYA_BIN.exists():
        print(f"  Himalaya not found at {HIMALAYA_BIN}")
        return False

    try:
        tmp = Path("/tmp") / f"freshsites_email_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.eml"
        tmp.write_text(email_raw, encoding="utf-8")

        result = subprocess.run(
            [str(HIMALAYA_BIN), "message", "send", "--account", "freshsites"],
            input=tmp.read_text(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"  Sent to {to_email}")
            return True
        else:
            print(f"  Himalaya failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  Send error: {e}")
        return False


def mark_emailed(lead_id: int):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        "UPDATE leads SET status = 'emailed', updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), lead_id),
    )
    conn.commit()
    conn.close()


def preview_email(lead_id: int = None):
    """Preview what the email will look like."""
    leads = get_leads_to_email()
    if not leads:
        print("No leads ready for email.")
        return

    target = None
    if lead_id:
        for l in leads:
            if l["id"] == lead_id:
                target = l
                break
    else:
        target = leads[0]

    if not target:
        print(f"Lead {lead_id} not found.")
        return

    email, to = generate_email(target)
    print(f"\n{'='*60}")
    print(f"PREVIEW: Email to {to}")
    print(f"Business: {target['name']}")
    print(f"Score: {target['score']}/10")
    print(f"Demo: {target['demo_url']}")
    print(f"{'='*60}\n")
    print(email)
    print(f"\n{'='*60}")
    print(f"To send: add --send flag")


def run_emailer():
    """Main entry point."""
    send_mode = "--send" in sys.argv or "SEND" in sys.argv

    leads = get_leads_to_email()
    if not leads:
        print("No leads with demos ready for email.")
        return

    print(f"{'='*60}")
    print(f"FreshSites Email Outreach")
    print(f"Mode: {'SEND' if send_mode else 'PREVIEW'}")
    print(f"Leads ready: {len(leads)}")
    print(f"{'='*60}\n")

    for lead in leads:
        if lead["status"] == "emailed":
            print(f"SKIP: {lead['name']} (already emailed)")
            continue

        print(f"Processing: {lead['name']} (score: {lead['score']}/10)")
        email, to = generate_email(lead)

        if not send_mode:
            print(f"  PREVIEW: Would email {to}")
            print(f"  Subject: I built {lead['name']} a better homepage")
            continue

        if send_via_himalaya(email, to):
            mark_emailed(lead["id"])
            print(f"  Marked as emailed")
        else:
            print(f"  Failed to send")

        print()


if __name__ == "__main__":
    if "--preview" in sys.argv:
        # Find lead_id if specified
        lead_id = None
        for i, arg in enumerate(sys.argv):
            if arg.isdigit():
                lead_id = int(arg)
                break
        preview_email(lead_id)
    else:
        run_emailer()
