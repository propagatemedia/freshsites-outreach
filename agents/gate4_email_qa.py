#!/usr/bin/env python3
"""
Gate 4: Email content QA. Records subagent verdict on drafted email —
checks correct name/link, no typos, no template leftovers, tone,
link click-through.
"""
import sqlite3
from datetime import datetime

DB = '/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db'


def record_gate4(lead_id: int, verdict: str, notes: str):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate4_email', 'email_qa_agent', verdict, notes, now)
    )
    stage = 'gate4_pass' if verdict == 'PASS' else 'gate4_reject'
    c.execute("UPDATE leads SET pipeline_stage = ?, updated_at = ? WHERE id = ?", (stage, now, lead_id))
    conn.commit()
    conn.close()
    return verdict


if __name__ == '__main__':
    import sys
    lead_id, verdict, notes = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    print(record_gate4(lead_id, verdict, notes))
