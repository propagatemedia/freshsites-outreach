#!/usr/bin/env python3
"""
Test script: Send FreshSites outreach emails to test leads.
Emails go to tyrone@propagate.media for review.

Usage:
    PYTHONPATH="" ./.venv/bin/python3.11 agents/test_outreach.py
"""

import sqlite3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.emailer import generate_email, send_via_himalaya, preview_email

DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
TEST_EMAIL = "tyrone@propagate.media"


def get_test_leads():
    """Get the 3 test leads with their data."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """
        SELECT id, name, email, website, score, score_breakdown, demo_url, status
        FROM leads
        WHERE status = 'demo_built'
        ORDER BY score
        LIMIT 3
        """
    )
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return leads


def send_test_email(lead: dict):
    """Generate and send test email for a lead."""
    print(f"\n{'='*60}")
    print(f"TEST EMAIL: {lead['name']} (score: {lead['score']}/10)")
    print(f"{'='*60}")

    # Build lead dict
    lead_data = {
        "name": lead["name"],
        "email": TEST_EMAIL,
        "website": lead["website"],
        "score_breakdown": json.loads(lead["score_breakdown"]) if lead["score_breakdown"] else {},
        "demo_url": lead["demo_url"],
    }

    # Generate email
    email_html, recipient = generate_email(lead_data)

    # Show preview
    print(f"\nTo: {TEST_EMAIL}")
    print(f"Subject: I built {lead['name']} a better homepage")
    print(f"Length: {len(email_html)} chars")

    # Send
    sent = send_via_himalaya(email_html, TEST_EMAIL)
    if sent:
        print(f"Sent to {TEST_EMAIL}")
    else:
        print("Failed to send")

    return sent


def main():
    print("FreshSites Test Outreach")
    print("=" * 60)
    print("Sending test emails to tyrone@propagate.media")
    print("=" * 60)

    leads = get_test_leads()
    print(f"\nFound {len(leads)} test leads:\n")
    for lead in leads:
        print(f"  - {lead['name']} ({lead['score']}/10) - {lead['website']}")

    # Send emails
    for lead in leads:
        send_test_email(lead)

    print(f"\n{'='*60}")
    print("Done. Check tyrone@propagate.media inbox.")
    print("=" * 60)


if __name__ == "__main__":
    main()
