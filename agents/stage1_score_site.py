#!/usr/bin/env python3
"""
Stage 1: Load real business site, let it hydrate, screenshot + score.
Writes screenshot path and score to DB. Does NOT decide accept/reject —
that's Gate 1 (subagent QA).
"""

import sqlite3
import subprocess
import time
import json
import os
from datetime import datetime

SCREENSHOT_DIR = "/Users/tyronemacmini/git/freshsites-outreach/tmp/screenshots/real_sites"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def score_site(html: str, http_status: int, load_time_s: float) -> dict:
    """Cheap heuristic score 0-10 (0=broken, 10=perfect). Lower = better rebuild candidate."""
    score = 5.0
    reasons = []

    if http_status == 0 or http_status >= 400:
        score -= 3.0
        reasons.append(f"http_status={http_status}")
    elif http_status == 200:
        score += 1.0

    if load_time_s > 5:
        score -= 1.0
        reasons.append(f"slow load {load_time_s:.1f}s")

    if len(html) < 500:
        score -= 2.0
        reasons.append("near-empty page (parked/broken)")

    if 'domain for sale' in html.lower() or 'this domain is parked' in html.lower():
        score -= 3.0
        reasons.append("parking page")

    dead_site_markers = [
        'sorry this website is now closed',   # it'seeze
        'account suspended',                    # cPanel
        'domain parked free',                   # GoDaddy
        'this account has been suspended',
        'website coming soon',
        'default web page',
    ]
    is_dead_site = any(marker in html.lower() for marker in dead_site_markers) or http_status == 0
    if is_dead_site:
        score -= 5.0
        reasons.append("DEAD SITE (not a rebuild candidate - route to no-website/SMS list, not email+demo track)")

    if '<meta name="viewport"' not in html:
        score -= 1.0
        reasons.append("no mobile viewport meta (not responsive)")

    if not any(x in html.lower() for x in ['tel:', 'contact', 'phone']):
        score -= 0.5
        reasons.append("no visible contact method")

    score = max(0.0, min(10.0, score))
    return {'score': round(score, 1), 'reasons': reasons, 'is_dead_site': is_dead_site,
            'needs_browser_verify': not is_dead_site and len(html) < 2000}


def process_lead(lead_id: int, name: str, website: str):
    print(f"[{name}] Loading {website} ...")

    start = time.time()
    result = subprocess.run(
        ['curl', '-s', '-L', '-o', '/dev/null', '-w', '%{http_code}', '-m', '15', website],
        capture_output=True, text=True
    )
    http_status = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    load_time = time.time() - start

    html_result = subprocess.run(['curl', '-s', '-L', '-m', '15', website], capture_output=True, text=True)
    html = html_result.stdout

    scoring = score_site(html, http_status, load_time)

    screenshot_path = f"{SCREENSHOT_DIR}/lead_{lead_id}.png"
    # Screenshot capture happens via browser_exec in the orchestrator (needs real browser tool)
    # This script only does the scoring pass; orchestrator calls browser separately.

    return {
        'lead_id': lead_id,
        'score': scoring['score'],
        'reasons': scoring['reasons'],
        'is_dead_site': scoring['is_dead_site'],
        'needs_browser_verify': scoring['needs_browser_verify'],
        'http_status': http_status,
        'load_time_s': round(load_time, 2),
        'screenshot_path': screenshot_path,
        'html_snippet': html[:3000],
    }


def run_batch(lead_ids=None):
    conn = sqlite3.connect('/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db')
    c = conn.cursor()

    if lead_ids:
        placeholders = ','.join('?' * len(lead_ids))
        c.execute(f"SELECT id, name, website FROM leads WHERE id IN ({placeholders}) AND website IS NOT NULL", lead_ids)
    else:
        c.execute("SELECT id, name, website FROM leads WHERE pipeline_stage = 'discovered' AND website IS NOT NULL")

    leads = c.fetchall()
    results = []

    for lead_id, name, website in leads:
        r = process_lead(lead_id, name, website)
        results.append(r)

        now = datetime.now().isoformat()

        if r['is_dead_site']:
            # Dead sites never reach Gate 1 - they're not rebuild candidates,
            # they're "no working website" leads. Route straight to SMS list.
            c.execute(
                "UPDATE leads SET score = ?, pipeline_stage = 'reclassify_no_website', status = 'no_website_sms_candidate', updated_at = ? WHERE id = ?",
                (r['score'], now, lead_id)
            )
            c.execute(
                "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (lead_id, 'stage1_score', 'stage1_score_site.py', 'DEAD_SITE_AUTO_REJECT',
                 f"Auto-routed to SMS list, skipped Gate 1 entirely: {json.dumps(r['reasons'])}", now)
            )
        else:
            c.execute(
                "UPDATE leads SET score = ?, pipeline_stage = 'screenshotted', updated_at = ? WHERE id = ?",
                (r['score'], now, lead_id)
            )
            c.execute(
                "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (lead_id, 'stage1_score', 'stage1_score_site.py', 'SCORED', json.dumps(r['reasons']), now)
            )

    conn.commit()
    conn.close()
    return results


if __name__ == '__main__':
    import sys
    ids = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    results = run_batch(ids)
    for r in results:
        print(f"Lead {r['lead_id']}: score={r['score']} reasons={r['reasons']}")
