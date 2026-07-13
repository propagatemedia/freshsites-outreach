#!/usr/bin/env python3
"""Send all 10 test emails - final before real outreach."""
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from emailer import generate_email, send_via_himalaya

conn = sqlite3.connect("leads/freshsites.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT name, email, score, score_breakdown, demo_url FROM leads WHERE status='demo_built' ORDER BY score")

sent = 0
for row in c.fetchall():
    try:
        lead = dict(row)
        email_html, subject = generate_email(lead)
        # Redirect to tyrone for testing
        email_html = email_html.replace(
            "To: " + lead["name"] + " <" + lead["email"] + ">",
            "To: " + lead["name"] + " <tyrone@propagate.media>"
        )
        ok = send_via_himalaya(email_html, "tyrone@propagate.media")
        if ok:
            print("SENT: " + lead["name"] + " (" + str(lead["score"]) + "/10)")
            sent += 1
        else:
            print("FAIL: " + lead["name"])
    except Exception as e:
        print("ERR: " + str(e) + " for " + lead["name"])

conn.close()
print("TOTAL: " + str(sent) + " emails sent")
