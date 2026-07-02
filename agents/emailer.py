#!/usr/bin/env python3
"""
FreshSites Email Outreach Agent
Generates and sends personalized emails to scored leads with demo pages.
Uses Himalaya CLI for email delivery.

Usage:
    PYTHONPATH="" ./.venv/bin/python3.11 agents/emailer.py
"""

import json
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
HIMALAYA_BIN = Path.home() / ".local" / "bin" / "himalaya"
SENDER_EMAIL = "freshsites@sites.propagate.media"
SENDER_NAME = "FreshSites by Propagate Media"

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
  <div style="border-bottom:2px solid #F1C204;padding-bottom:16px;margin-bottom:24px;">
    <strong style="font-size:1.2rem;color:#0A0A0A;">FreshSites</strong>
    <span style="float:right;font-size:0.8rem;color:#888;">by Propagate Media</span>
  </div>

  <p style="font-size:1.05rem;line-height:1.6;">Hi there,</p>

  <p style="font-size:1.05rem;line-height:1.6;">I run <strong>FreshSites</strong> — we build fast, conversion-focused landing pages for local businesses. I came across <strong>{business_name}</strong> and noticed a few things your current homepage is missing:</p>

  <ul style="font-size:1rem;line-height:1.7;color:#555;padding-left:20px;">
    {weaknesses_html}
  </ul>

  <p style="font-size:1.05rem;line-height:1.6;">So I built you a demo. Same brand colours, same services — but designed to turn visitors into bookings:</p>

  <div style="background:#0A0A0A;border-radius:8px;padding:24px;margin:24px 0;text-align:center;">
    <p style="color:#F1C204;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:8px;">YOUR DEMO PAGE</p>
    <a href="{demo_url}" style="color:#fff;font-size:1.1rem;font-weight:600;text-decoration:underline;">{demo_url}</a>
  </div>

  <p style="font-size:1.05rem;line-height:1.6;">The page is <strong>£149 outright</strong> — you own it, host it anywhere, tweak it however you like. No monthly fees, no lock-in.</p>

  <p style="font-size:1.05rem;line-height:1.6;">Want custom changes (different photos, extra sections, your logo)? We can do that too — just reply and tell me what you need.</p>

  <div style="margin-top:32px;padding-top:24px;border-top:1px solid #eee;">
    <p style="font-size:0.9rem;color:#555;">Questions? Just reply to this email.</p>
    <p style="font-size:0.85rem;color:#888;margin-top:8px;">— {sender_name}</p>
  </div>
</div>
</body>
</html>
""",
    "followup": """From: {sender_name} <{sender_email}>
To: {recipient_name} <{recipient_email}>
Subject: Re: {business_name} homepage — still interested?
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Inter,Helvetica,sans-serif;color:#1a1a1a;background:#fff;margin:0;padding:0;">
<div style="max-width:600px;margin:0 auto;padding:40px 24px;">
  <p style="font-size:1.05rem;">Hi {recipient_name},</p>
  <p style="font-size:1.05rem;line-height:1.6;">Quick follow-up — I built that demo page for <strong>{business_name}</strong> last week. Wanted to check if you had a chance to look at it:</p>
  <p style="text-align:center;margin:24px 0;"><a href="{demo_url}" style="background:#0A0A0A;color:#F1C204;padding:14px 28px;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;">View Your Demo</a></p>
  <p style="font-size:1.05rem;line-height:1.6;">Still £149 flat. Still no strings. Reply if you want it or if you have questions.</p>
  <p style="font-size:0.85rem;color:#888;">— {sender_name}</p>
</div>
</body>
</html>
"""
}

# ── Functions ────────────────────────────────────────────────────

def get_leads_to_email() -> list[dict]:
    """Get leads with demos but not yet emailed."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT * FROM leads
        WHERE status IN ('demo_built', 'emailed')
        AND demo_url IS NOT NULL AND demo_url != ''
        ORDER BY score ASC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def format_weaknesses(score_breakdown: str) -> str:
    """Convert score breakdown JSON to HTML list items."""
    try:
        bd = json.loads(score_breakdown)
    except:
        return "<li>Homepage could convert more visitors into customers</li>"

    weakness_map = {
        "mobile_responsive": "No mobile-responsive design (over 60% of visitors are on phones)",
        "cta_present": "No clear call-to-action — visitors don't know what to do next",
        "phone_visible": "Phone number hidden or missing — callers can't find you",
        "social_proof": "No customer reviews or testimonials — missing trust signals",
        "title_quality": "Weak page title — Google doesn't know what you do",
        "h1_present": "No headline on the page — visitors can't tell what you offer",
        "contact_form": "No contact form — visitors have to call or email manually",
        "social_links": "No social media links — missing another trust signal",
        "images": "Too few images — looks sparse and low-effort",
        "meta_description": "No meta description — looks bad in Google search results",
        "clean_urls": "Messy page links — hurts SEO and looks unprofessional",
    }

    zero_items = [k for k, v in bd.items() if v == 0 and k in weakness_map]
    if not zero_items:
        zero_items = [k for k, v in bd.items() if v < 1 and k in weakness_map]

    items = []
    for k in zero_items[:3]:
        items.append(f"<li>{weakness_map.get(k, k)}</li>")

    if not items:
        items = ["<li>Homepage could convert more visitors into customers</li>"]

    return "\n".join(items)


def generate_email(lead: dict, template: str = "initial") -> str:
    """Generate HTML email for a lead."""
    name = lead["name"]
    # Guess email from domain if not known
    email = lead["email"] or guess_email(lead["website"], name)

    weaknesses = format_weaknesses(lead["score_breakdown"])

    email_body = EMAIL_TEMPLATES[template].format(
        sender_name=SENDER_NAME,
        sender_email=SENDER_EMAIL,
        recipient_name="there",  # We don't know their name usually
        recipient_email=email,
        business_name=name,
        demo_url=lead["demo_url"],
        weaknesses_html=weaknesses,
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
    # Common patterns
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
        print(f"  ❌ Himalaya not found at {HIMALAYA_BIN}")
        return False

    try:
        # Write email to temp file
        tmp = Path("/tmp") / f"freshsites_email_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.eml"
        tmp.write_text(email_raw, encoding="utf-8")

        result = subprocess.run(
            [str(HIMALAYA_BIN), "message", "send", "--account", "gravityaddiction"],
            input=tmp.read_text(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"  ✅ Sent to {to_email}")
            return True
        else:
            print(f"  ❌ Himalaya failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Send error: {e}")
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
    print(email[:1500])
    print("\n... [truncated for preview] ...")
    print(f"\nTo send: set SEND=true and run again")


def run_emailer():
    """Main entry point."""
    send_mode = "SEND" in sys.argv or "--send" in sys.argv

    leads = get_leads_to_email()
    if not leads:
        print("No leads with demos ready for email.")
        return

    print(f"{'='*60}")
    print(f"FreshSites Email Outreach — {len(leads)} leads ready")
    print(f"{'='*60}\n")

    sent = 0
    for lead in leads:
        print(f"📧 {lead['name']} (score: {lead['score']}/10)")
        email, to = generate_email(lead)

        if not to:
            print(f"   ⚠️  No email address — skipping")
            continue

        if not send_mode:
            print(f"   ⏸️  PREVIEW mode (add --send to send)")
            print(f"   → Would send to: {to}")
            continue

        success = send_via_himalaya(email, to)
        if success:
            mark_emailed(lead["id"])
            sent += 1
        else:
            print(f"   ⚠️  Failed — will retry next run")

    print(f"\n{'='*60}")
    if send_mode:
        print(f"Sent {sent}/{len(leads)} emails")
    else:
        print(f"Previewed {len(leads)} leads. Use --send to dispatch.")
    print(f"{'='*60}")


if __name__ == "__main__":
    if "--preview" in sys.argv or "--id" in sys.argv:
        lead_id = None
        for i, arg in enumerate(sys.argv):
            if arg == "--id" and i + 1 < len(sys.argv):
                lead_id = int(sys.argv[i + 1])
        preview_email(lead_id)
    else:
        run_emailer()
