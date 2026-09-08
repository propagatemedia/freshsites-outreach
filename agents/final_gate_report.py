#!/usr/bin/env python3
"""
Final Gate: builds the human approval view. Shows every lead that has
passed Gates 1-4, with screenshot, score, demo link, email draft, and
full gate history. Nothing sends until Tyrone marks final_gate = GREEN.
"""
import sqlite3
import json
from datetime import datetime

DB = '/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db'


def build_approval_report():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, score, website, demo_url, email, phone,
               real_screenshot_path, demo_screenshot_path, pipeline_stage
        FROM leads
        WHERE pipeline_stage = 'gate4_pass'
        ORDER BY score ASC
    """)
    rows = c.fetchall()

    report = []
    for row in rows:
        lead_id = row[0]
        c.execute("SELECT gate_name, agent, verdict, notes, created_at FROM gate_log WHERE lead_id = ? ORDER BY created_at", (lead_id,))
        gates = c.fetchall()
        report.append({
            'lead_id': lead_id,
            'name': row[1],
            'score': row[2],
            'website': row[3],
            'demo_url': row[4],
            'email': row[5],
            'phone': row[6],
            'real_screenshot': row[7],
            'demo_screenshot': row[8],
            'stage': row[9],
            'gate_history': [
                {'gate': g[0], 'agent': g[1], 'verdict': g[2], 'notes': g[3], 'at': g[4]}
                for g in gates
            ]
        })
    conn.close()
    return report


def mark_final_gate(lead_id: int, decision: str, approver: str = 'Tyrone'):
    """decision: GREEN or HOLD"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'final_gate', approver, decision, f"approved by {approver}", now)
    )
    stage = 'final_approved' if decision == 'GREEN' else 'final_hold'
    c.execute(
        "UPDATE leads SET pipeline_stage = ?, final_gate_by = ?, final_gate_at = ?, updated_at = ? WHERE id = ?",
        (stage, approver, now, now, lead_id)
    )
    conn.commit()
    conn.close()
    return stage


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'approve':
        lead_id = int(sys.argv[2])
        decision = sys.argv[3] if len(sys.argv) > 3 else 'GREEN'
        print(mark_final_gate(lead_id, decision))
    else:
        report = build_approval_report()
        print(json.dumps(report, indent=2))
