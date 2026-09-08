#!/usr/bin/env python3
"""
Gate 1: Candidate QA.
Given a lead's real-site screenshot + score + extracted text, this script
prepares the review package. The actual "two independent subagents" review
is done by the ORCHESTRATOR (Hermes agent) calling delegate_task twice per
lead and comparing verdicts — this script just records the outcome.

Usage: called by orchestrator with verdicts already decided.
"""

import sqlite3
import json
from datetime import datetime

DB = '/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db'


def record_gate1(lead_id: int, agent_a_verdict: str, agent_a_notes: str,
                  agent_b_verdict: str, agent_b_notes: str,
                  brand_size_reject: bool = False, brand_size_reasons=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate1_candidate', 'agent_a', agent_a_verdict, agent_a_notes, now)
    )
    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate1_candidate', 'agent_b', agent_b_verdict, agent_b_notes, now)
    )

    if brand_size_reject:
        final_verdict = 'REJECT'
        stage = 'gate1_reject'
        notes = f"brand_size_filter auto-reject: {json.dumps(brand_size_reasons or [])}"
    elif agent_a_verdict == 'PASS' and agent_b_verdict == 'PASS':
        final_verdict = 'PASS'
        stage = 'gate1_pass'
        notes = 'both agents agreed: candidate'
    else:
        final_verdict = 'REJECT'
        stage = 'gate1_reject'
        notes = f"disagreement or reject: A={agent_a_verdict}, B={agent_b_verdict}"

    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate1_final', 'orchestrator', final_verdict, notes, now)
    )
    c.execute(
        "UPDATE leads SET pipeline_stage = ?, updated_at = ? WHERE id = ?",
        (stage, now, lead_id)
    )

    conn.commit()
    conn.close()
    return final_verdict


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 5:
        print("Usage: gate1_candidate_qa.py <lead_id> <agent_a_verdict> <agent_b_verdict> <notes>")
        sys.exit(1)
    lead_id, a, b, notes = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    verdict = record_gate1(lead_id, a, notes, b, notes)
    print(f"Gate 1 final verdict for lead {lead_id}: {verdict}")
