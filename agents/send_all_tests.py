#!/usr/bin/env python3
"""Send all 10 test emails."""
import sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.emailer import generate_email, send_via_himalaya

DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
TEST_EMAIL = "tyrone@propagate.media"

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT name, email, website, score, score_breakdown, demo_url FROM leads WHERE status='demo_built' ORDER BY score")
leads = [dict(r) for r in c.fetchall()]
conn.close()

print(f"Sending {len(leads)} test emails to {TEST_EMAIL}")
for lead in leads:
    lead_data = {
        "name": lead["name"],
        "email": TEST_EMAIL,
        "website": lead["website"],
        "score": lead["score"],
        "score_breakdown": lead["score_breakdown"] or '{}',
        "demo_url": lead["demo_url"],
    }
    email_html, _ = generate_email(lead_data)
    sent = send_via_himalaya(email_html, TEST_EMAIL)
    status = "SENT" if sent else "FAILED"
    print(f"  [{status}] {lead['name']} ({lead['score']}/10)")

print("\nDone. Check tyrone@propagate.media inbox.")
