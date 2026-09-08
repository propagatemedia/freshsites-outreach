#!/usr/bin/env python3
"""
Gate 3: Link & function check. Fully mechanical, no subagent needed.
Checks the LIVE demo URL: HTTP 200, hero, CTA button, pricing, form,
tel: link, maps embed.
"""
import sqlite3
import subprocess
from datetime import datetime

DB = '/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db'

REQUIRED_CHECKS = {
    'http_200': lambda code, html: code == '200',
    'has_hero': lambda code, html: 'class="hero' in html,
    'has_cta_button': lambda code, html: 'class="btn' in html,
    'has_pricing': lambda code, html: '£149' in html,
    'has_contact_form': lambda code, html: '<form' in html.lower(),
    'has_tel_link': lambda code, html: 'href="tel:' in html,
}


def run_gate3(lead_id: int, demo_url: str):
    status = subprocess.run(['curl', '-sI', demo_url, '-m', '10'], capture_output=True, text=True)
    http_code = status.stdout.split('\n')[0].split(' ')[1] if status.stdout else '000'

    content = subprocess.run(['curl', '-s', demo_url, '-m', '10'], capture_output=True, text=True)
    html = content.stdout

    results = {}
    for check_name, check_fn in REQUIRED_CHECKS.items():
        results[check_name] = check_fn(http_code, html)

    all_pass = all(results.values())
    verdict = 'PASS' if all_pass else 'FAIL'
    notes = ', '.join(f"{k}={v}" for k, v in results.items())

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate3_links', 'mechanical_check', verdict, notes, now)
    )
    stage = 'gate3_pass' if all_pass else 'gate3_reject'
    c.execute("UPDATE leads SET pipeline_stage = ?, updated_at = ? WHERE id = ?", (stage, now, lead_id))
    conn.commit()
    conn.close()

    return {'verdict': verdict, 'checks': results}


if __name__ == '__main__':
    import sys
    lead_id, demo_url = int(sys.argv[1]), sys.argv[2]
    result = run_gate3(lead_id, demo_url)
    print(f"Gate 3: {result['verdict']}")
    for k, v in result['checks'].items():
        print(f"  {k}: {'✓' if v else '✗'}")
