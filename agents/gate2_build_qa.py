#!/usr/bin/env python3
"""
Gate 2: Build QA. Records verdict from a fresh subagent reviewing the
BUILT demo screenshot (not the real site). Checks for placeholder/lorem
junk, generic templates, brand mismatch.
"""
import sqlite3
from datetime import datetime

DB = '/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db'


def record_gate2(lead_id: int, verdict: str, notes: str, demo_screenshot_path: str = None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, screenshot_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate2_build', 'build_qa_agent', verdict, notes, demo_screenshot_path, now)
    )

    stage = 'gate2_pass' if verdict == 'PASS' else 'gate2_reject'
    updates = ["pipeline_stage = ?", "updated_at = ?"]
    params = [stage, now]
    if demo_screenshot_path:
        updates.append("demo_screenshot_path = ?")
        params.append(demo_screenshot_path)
    params.append(lead_id)

    c.execute(f"UPDATE leads SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return verdict


if __name__ == '__main__':
    import sys
    lead_id, verdict, notes = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    screenshot = sys.argv[4] if len(sys.argv) > 4 else None
    print(record_gate2(lead_id, verdict, notes, screenshot))
