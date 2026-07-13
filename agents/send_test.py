#!/usr/bin/env python3
"""Send test emails WITH reviewer gate. Blocks send if demo fails QA."""
import sys, subprocess, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from emailer import generate_email, send_via_himalaya

DB_PATH = Path(__file__).parent.parent / "leads" / "freshsites.db"
TEST_EMAIL = "tyrone@propagate.media"

def review_demo(demo_url, score, name):
    """Run reviewer.py on the live demo. Return True if PASS."""
    result = subprocess.run(
        ["python3", str(Path(__file__).parent / "reviewer.py"), demo_url, str(score), name],
        capture_output=True, text=True, timeout=60
    )
    return result.returncode == 0, result.stdout + result.stderr

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT name, email, website, score, score_breakdown, demo_url FROM leads WHERE status='demo_built' ORDER BY score")
leads = [dict(r) for r in c.fetchall()]
conn.close()

sent = 0
blocked = 0
for lead in leads:
    # REVIEWER GATE
    passed, output = review_demo(lead["demo_url"], lead["score"], lead["name"])
    if not passed:
        print(f"[BLOCKED] {lead['name']} — {lead['demo_url']}")
        print(output)
        blocked += 1
        continue
    
    lead_data = {
        "name": lead["name"],
        "email": TEST_EMAIL,
        "website": lead["website"],
        "score": lead["score"],
        "score_breakdown": lead["score_breakdown"] or '{}',
        "demo_url": lead["demo_url"],
    }
    email_html, _ = generate_email(lead_data)
    ok = send_via_himalaya(email_html, TEST_EMAIL)
    if ok:
        print(f"[SENT] {lead['name']} ({lead['score']}/10)")
        sent += 1
    else:
        print(f"[FAILED] {lead['name']} — email send error")

print(f"\nDone. Sent: {sent}, Blocked: {blocked}, Total: {len(leads)}")
