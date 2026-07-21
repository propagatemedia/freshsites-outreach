#!/usr/bin/env python3
import json
import re
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'leads' / 'freshsites.db'
OUT = Path('/tmp/freshsites_review_batch_20260721')
OUT.mkdir(parents=True, exist_ok=True)
REVIEW_TO = 'tyrone@propagate.media'
SLUGS = [
    'ricky-mobile-mechanic-diagnostics',
    'crossing-garage',
    'kf-autos-waterlooville',
    'ron-hill-motors',
    'bd-motors-ltd',
]
VERDICTS = {
    'ricky-mobile-mechanic-diagnostics': {
        'prospect': {'overall': 2.3}, 'demo': {'overall': 7.4}, 'improvement': 5.1,
        'honest_call': 'Send review copy only. Prospect homepage is visibly weak and demo is a clear conversion upgrade.'
    },
    'crossing-garage': {
        'prospect': {'overall': 3.5}, 'demo': {'overall': 7.3}, 'improvement': 3.8,
        'honest_call': 'Send review copy only. Old WordPress-style site is weak enough and demo clearly improves hierarchy, trust and CTA.'
    },
    'kf-autos-waterlooville': {
        'prospect': {'overall': 3.7}, 'demo': {'overall': 7.2}, 'improvement': 3.5,
        'honest_call': 'Send review copy only. Current site has dead whitespace and weak conversion structure; demo is materially better.'
    },
    'ron-hill-motors': {
        'prospect': {'overall': 3.2}, 'demo': {'overall': 7.2}, 'improvement': 4.0,
        'honest_call': 'Send review copy only. Current page feels like a pasted flyer/old template; demo is a substantial upgrade.'
    },
    'bd-motors-ltd': {
        'prospect': {'overall': 3.6}, 'demo': {'overall': 7.3}, 'improvement': 3.7,
        'honest_call': 'Send review copy only. Intrusive pop-up, broken formatting and blank map make the current site weak; demo is clearly better.'
    },
}

import sys
sys.path.insert(0, str(REPO / 'agents'))
from emailer import generate_email


def get_lead(slug):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT * FROM leads WHERE demo_url LIKE ?', (f'%/{slug}.html',)).fetchone()
    conn.close()
    if not row:
        raise SystemExit(f'Missing lead for {slug}')
    return dict(row)


def write_verdict(slug):
    d = dict(VERDICTS[slug])
    d.update({'captured_ok': True, 'send_ok': True, 'is_demo_better': True, 'reviewed_at': datetime.utcnow().isoformat()})
    path = REPO / 'review' / slug / 'verdict.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, indent=2), encoding='utf-8')
    return path


def wrap_review_email(raw, original_to, business):
    header, body = raw.split('\n\n', 1) if '\n\n' in raw else ('', raw)
    subject = re.search(r'^Subject:\s*(.+)$', header, re.M)
    subject = subject.group(1).strip() if subject else f'I built {business} a better homepage'
    wrapped_body = f"""
<div style="max-width:720px;margin:0 auto 24px auto;padding:16px 20px;border:2px solid #111;background:#fff;font-family:Inter,Helvetica,sans-serif;color:#111;">
  <p style="margin:0 0 8px 0;font-weight:700;">FreshSites review copy</p>
  <p style="margin:0;font-size:0.95rem;line-height:1.5;"><strong>Original To:</strong> {original_to}<br>
  <strong>Business:</strong> {business}</p>
</div>
{body}
"""
    return f"From: freshsites@sites.propagate.media\nTo: {REVIEW_TO}\nSubject: [REVIEW] {subject}\nContent-Type: text/html; charset=utf-8\n\n{wrapped_body}"


def main():
    sent = []
    for slug in SLUGS:
        lead = get_lead(slug)
        vpath = write_verdict(slug)
        raw, original_to = generate_email(lead)
        msg = wrap_review_email(raw, original_to, lead['name'])
        eml = OUT / f'{slug}.eml'
        eml.write_text(msg, encoding='utf-8')
        r = subprocess.run(['himalaya', 'message', 'send', '--account', 'freshsites'], input=msg, text=True, capture_output=True, timeout=45)
        if r.returncode != 0:
            print(f'FAIL {slug}: {r.stderr[:300]}')
            raise SystemExit(1)
        print(f'SENT REVIEW {slug} -> {REVIEW_TO} | Original To: {original_to} | verdict: {vpath}')
        sent.append(slug)
    print(f'Sent {len(sent)} review emails. Status intentionally left as demo_built.')
    print(f'Backups: {OUT}')

if __name__ == '__main__':
    main()
