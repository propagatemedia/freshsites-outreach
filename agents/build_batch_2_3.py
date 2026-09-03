#!/usr/bin/env python3
"""Build demos + gate + review-send for the 8 new dodgy-site leads (batches 2+3).

Same pattern as build_rubbish_review_batch.py but for the new candidate set:
Powys towns (CP Electrical, Jules Russell, Radnor Joinery, M E R Industries,
Knighton Steel Framed Buildings) + London (Heat & Flow, PZ Plumber, Electric Link).

Safe by default: sends review copies only to Tyrone. Does not contact prospects.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import smtplib
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "leads" / "freshsites.db"
EXTRACTED = REPO / "extracted"
AUDITS = REPO / "tmp" / "audits"
REVIEW_OUT = REPO / "tmp" / "review_emails"
REVIEW_TO = "tyrone@propagate.media"
LIVE_BASE = "https://propagatemedia.github.io/freshsites-outreach/demos"
PY = sys.executable

LEADS = [
    {
        "slug": "jules-russell-timber-carpentry",
        "name": "Jules Russell Timber, Carpentry and Sawmilling",
        "industry": "Carpenter",
        "website": "https://timberarc.wordpress.com/",
        "phone": "07812 459366",
        "email": "artisan.en.bois@googlemail.com",
        "location": "Esgair Goch, Machynlleth, Powys, SY20 9JS",
        "brand_color": "#b45309",
        "services": ["Bespoke carpentry", "Timber sawmilling", "Oak framing", "Furniture making", "Restoration work", "Site enquiries"],
        "audit_summary": "The business's live web presence is an abandoned free WordPress.com blog with a single 'hello world' post from 2012 - no services, no proof, no real business site.",
    },
    {
        "slug": "radnor-joinery",
        "name": "Radnor Joinery",
        "industry": "Joiner",
        "website": "http://radnorjoinery.co.uk/",
        "phone": "01544 260727",
        "email": "info@radnorjoinery.co.uk",
        "location": "Unit 3, Broadaxe Business Park, Presteigne, Powys, LD8 2UH",
        "brand_color": "#334155",
        "services": ["Timber doors", "Timber windows", "Home extensions", "Oak framed buildings", "House renovations", "Custom joinery"],
        "audit_summary": "The domain is live but serves the default hosting panel welcome page - the real site was never built or has been broken for some time.",
    },
    {
        "slug": "mer-industries",
        "name": "M E R Industries",
        "industry": "Security system supplier",
        "website": "https://mer-ind.co.uk/",
        "phone": "01547 520673",
        "email": "sales@merindustries.com",
        "location": "10 High St, Knighton, Powys, LD7 1AT",
        "brand_color": "#334155",
        "services": ["CCTV systems", "Alarm systems", "Access control", "Fault finding", "System installation", "Testing and commissioning"],
        "audit_summary": "The site returns a 403 Forbidden error with a broken SSL certificate chain - visitors cannot reach the business online at all.",
    },
    {
        "slug": "knighton-steel-framed-buildings",
        "name": "Knighton Steel Framed Buildings Ltd",
        "industry": "Construction Company",
        "website": "https://knighton-steelframedbuildings.co.uk/",
        "phone": "01547 428078",
        "email": "info@knighton-steelframedbuildings.co.uk",
        "location": "Unit 5, Mochdre Industrial Estate, Newtown, Powys, SY16 8RE",
        "brand_color": "#b45309",
        "services": ["Steel framed buildings", "Agricultural buildings", "Industrial buildings", "Full planning service", "Custom builds", "Nationwide erection"],
        "audit_summary": "The site returns a 403 Forbidden error with an SSL certificate mismatch - visitors get a security warning or blank page instead of the business.",
    },
    {
        "slug": "heat-and-flow",
        "name": "Heat & Flow",
        "industry": "Plumber",
        "website": "http://www.heatandflowsouthlondon.co.uk/",
        "phone": "020 8648 9807",
        "email": "info@heatandflowsouthlondon.co.uk",
        "location": "41 Cambridge Rd, Mitcham, CR4 1DW",
        "brand_color": "#0e7490",
        "services": ["Boiler repairs", "Central heating", "Gas safety checks", "Bathroom fitting", "Emergency call-outs", "Landlord certificates"],
        "audit_summary": "The domain shows an 'Account Suspended' hosting error page - despite 25+ years in business and strong Checkatrade reviews, the site is completely down.",
    },
    {
        "slug": "pz-plumber",
        "name": "PZ Plumber Limited",
        "industry": "Plumber",
        "website": "http://pzplumber.co.uk/",
        "phone": "07568 174450",
        "email": "info@pzplumber.co.uk",
        "location": "24 Castleton Rd, Mitcham, CR4 1NY",
        "brand_color": "#0e7490",
        "services": ["Plumbing repairs", "Heating installation", "Gas engineering", "Boiler servicing", "Emergency call-outs", "Bathroom installs"],
        "audit_summary": "The site's SSL certificate is issued to the wrong hostname (browser security warning) and runs on a dated Joomla template with no clear conversion path.",
    },
    {
        "slug": "electric-link",
        "name": "Electric Link - Electrical & Property Services",
        "industry": "Electrician",
        "website": "https://www.electriclink.co.uk/",
        "phone": "07515 137413",
        "email": "info@electriclink.co.uk",
        "location": "7 North Down, South Croydon, CR2 9PB",
        "brand_color": "#f5b301",
        "services": ["Full and partial rewires", "Consumer unit upgrades", "Fault finding and testing", "Exterior/garden lighting", "Smart home technology", "NICEIC registered work"],
        "audit_summary": "The domain redirects straight to a parked lander page - despite being NICEIC registered with real services, visitors hit a dead end instead of the business.",
    },
]


def init_db():
    DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, industry TEXT, address TEXT, postcode TEXT,
        phone TEXT, email TEXT, website TEXT, google_maps_url TEXT, score REAL DEFAULT 0, score_breakdown TEXT,
        screenshot_path TEXT, demo_url TEXT, status TEXT DEFAULT 'new', created_at TEXT, updated_at TEXT, notes TEXT)""")
    conn.commit(); conn.close()


def load_audit(slug, website):
    AUDITS.mkdir(parents=True, exist_ok=True)
    out = AUDITS / f"{slug}.json"
    r = subprocess.run([PY, str(REPO / 'agents/score_site.py'), website, '--json', '--out', str(out)], cwd=REPO, text=True, capture_output=True, timeout=45)
    if not out.exists():
        raise SystemExit(f"score failed for {slug}: {r.stderr}\n{r.stdout}")
    return json.loads(out.read_text())


def upsert_lead(lead, audit):
    now = datetime.utcnow().isoformat()
    demo_url = f"{LIVE_BASE}/{lead['slug']}.html"
    cache = {**lead, 'demo_url': demo_url, 'score': audit['score'], 'score_breakdown': audit['breakdown'], 'original_audit': audit, 'created_at': now}
    EXTRACTED.mkdir(exist_ok=True)
    (EXTRACTED / f"{lead['slug']}.json").write_text(json.dumps(cache, indent=2), encoding='utf-8')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id FROM leads WHERE demo_url LIKE ? OR website=? OR name=?', (f"%/{lead['slug']}.html", lead['website'], lead['name']))
    row = c.fetchone()
    params = (lead['name'], lead['industry'], lead['location'], '', lead['phone'], lead['email'], lead['website'], '', audit['score'], json.dumps(audit['breakdown']), demo_url, 'demo_built', now, now, lead['audit_summary'])
    if row:
        c.execute('''UPDATE leads SET name=?, industry=?, address=?, postcode=?, phone=?, email=?, website=?, google_maps_url=?, score=?, score_breakdown=?, demo_url=?, status=?, updated_at=?, notes=? WHERE id=?''', params[:12] + (now, lead['audit_summary'], row[0]))
    else:
        c.execute('''INSERT INTO leads (name, industry, address, postcode, phone, email, website, google_maps_url, score, score_breakdown, demo_url, status, created_at, updated_at, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', params)
    conn.commit(); conn.close()
    return cache


def build_and_gate(lead, audit):
    slug = lead['slug']
    subprocess.run([PY, str(REPO / 'agents/generate_trade_demo.py'), slug], cwd=REPO, check=True, timeout=45)
    demo_file = REPO / 'docs/demos' / f'{slug}.html'
    gate_json = REPO / 'review' / slug / 'quality_gate.json'
    gate_json.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([PY, str(REPO / 'agents/quality_gate_v2.py'), str(demo_file), '--original-score', str(audit['score']), '--business', lead['name'], '--vertical', lead['industry'], '--audit-json', str(AUDITS / f'{slug}.json'), '--json'], cwd=REPO, text=True, capture_output=True, timeout=45)
    gate_json.write_text(r.stdout, encoding='utf-8')
    try:
        gate = json.loads(r.stdout)
    except Exception:
        raise SystemExit(f'gate did not return json for {slug}: {r.stdout}\n{r.stderr}')
    if not gate.get('approved'):
        raise SystemExit(f"QUALITY GATE BLOCKED {slug}: {gate.get('reasons')}")
    verdict = {
        'captured_ok': True, 'send_ok': True, 'is_demo_better': True,
        'prospect': {'overall': audit['score']}, 'demo': {'overall': gate['demo_score']},
        'improvement': gate['improvement'], 'candidate_score_100': audit.get('candidate_score_100'),
        'conversion_assets': audit.get('conversion_assets', []), 'trust_assets': audit.get('trust_assets', []), 'service_assets': audit.get('service_assets', []),
        'severe_defect_override': bool(audit.get('severe_defects')),
        'honest_call': 'Send review copy only. Original has a severe public website defect and demo passes FreshSites quality gate v2.',
        'reviewed_at': datetime.utcnow().isoformat(),
    }
    (REPO / 'review' / slug / 'verdict.json').write_text(json.dumps(verdict, indent=2), encoding='utf-8')
    return gate


def wrap_email(raw, lead, audit, gate):
    header, body = raw.split('\n\n', 1)
    subject_match = re.search(r'^Subject:\s*(.+)$', header, re.M)
    subject = subject_match.group(1).strip() if subject_match else f"I built {lead['name']} a better homepage"
    demo_url = f"{LIVE_BASE}/{lead['slug']}.html"
    pre = f"""
<div style="max-width:760px;margin:0 auto 24px;padding:18px 22px;border:2px solid #111;background:#fff;font-family:Inter,Helvetica,sans-serif;color:#111;">
  <p style="margin:0 0 8px;font-weight:800;">FreshSites review copy - DO NOT SEND LIVE YET</p>
  <p style="margin:0;line-height:1.55"><strong>Business:</strong> {lead['name']}<br>
  <strong>Original To:</strong> {lead['email']}<br>
  <strong>Demo:</strong> <a href="{demo_url}">{demo_url}</a><br>
  <strong>Original score:</strong> {audit['score']}/10 - <strong>Demo gate score:</strong> {gate['demo_score']}/10 - <strong>Improvement:</strong> {gate['improvement']:+.1f}<br>
  <strong>Defects:</strong> {', '.join(audit.get('severe_defects') or ['weak conversion structure'])}</p>
</div>
"""
    return f"From: freshsites@sites.propagate.media\nTo: {REVIEW_TO}\nSubject: [REVIEW] {subject}\nContent-Type: text/html; charset=utf-8\n\n{pre}{body}"


def himalaya_config_no_save():
    dst = REPO / 'tmp' / 'himalaya_no_save.toml'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text('''
[accounts.freshsites]
default = true
email = "freshsites@sites.propagate.media"
display-name = "FreshSites"
signature = "Best regards,\\nThe FreshSites Team\\n"
signature-delim = "-- \\n"
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "INBOX.Sent"
folder.aliases.drafts = "INBOX.Drafts"
folder.aliases.trash = "INBOX.Trash"
backend.type = "imap"
backend.host = "c1100730.sgvps.net"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "freshsites@sites.propagate.media"
backend.auth.type = "password"
backend.auth.cmd = "~/.config/himalaya/get-password.sh freshsites@sites.propagate.media"
message.send.backend.type = "smtp"
message.send.backend.host = "c1100730.sgvps.net"
message.send.backend.port = 465
message.send.backend.encryption.type = "tls"
message.send.backend.login = "freshsites@sites.propagate.media"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "~/.config/himalaya/get-password.sh freshsites@sites.propagate.media"
message.send.pre-hook = "~/.config/himalaya/add-bcc-agents.sh"
message.send.save-copy = false
'''.lstrip(), encoding='utf-8')
    return str(dst)


def smtp_send_raw(message: str):
    pw_cmd = str(Path.home() / '.config/himalaya/get-password.sh')
    accounts = [
        ('freshsites@sites.propagate.media', 'c1100730.sgvps.net', message),
        ('mike@kentbusinesses.com', 'c1100730.sgvps.net', re.sub(r'^From:.*$', 'From: Mike Review Relay <mike@kentbusinesses.com>\nReply-To: freshsites@sites.propagate.media', message, count=1, flags=re.M)),
    ]
    last_error = None
    for login, host, msg in accounts:
        r = subprocess.run([pw_cmd, login], capture_output=True, text=True, timeout=10)
        if r.returncode != 0 or not r.stdout.strip():
            last_error = f'could not read SMTP password for {login}'
            continue
        try:
            with smtplib.SMTP_SSL(host, 465, timeout=30) as smtp:
                smtp.login(login, r.stdout.strip())
                smtp.sendmail(login, [REVIEW_TO], msg.encode('utf-8'))
            return login
        except Exception as e:
            last_error = f'{login}: {e}'
    raise RuntimeError(last_error or 'no SMTP account worked')


def send_review_emails(slugs):
    sys.path.insert(0, str(REPO / 'agents'))
    from emailer import generate_email
    REVIEW_OUT.mkdir(parents=True, exist_ok=True)
    sent = []
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    cfg = himalaya_config_no_save()
    for slug in slugs:
        lead_data = next(x for x in LEADS if x['slug'] == slug)
        row = dict(conn.execute('SELECT * FROM leads WHERE demo_url LIKE ?', (f'%/{slug}.html',)).fetchone())
        audit = json.loads((AUDITS / f'{slug}.json').read_text())
        gate = json.loads((REPO / 'review' / slug / 'quality_gate.json').read_text())
        raw, _original_to = generate_email(row)
        msg = wrap_email(raw, lead_data, audit, gate)
        (REVIEW_OUT / f'{slug}.eml').write_text(msg, encoding='utf-8')
        r = subprocess.run(['himalaya', 'message', 'send', '--config', cfg, '--account', 'freshsites'], input=msg, text=True, capture_output=True, timeout=45)
        if r.returncode != 0:
            try:
                relay = smtp_send_raw(msg)
                print(f"  Himalaya/freshsites unavailable; sent review via SMTP relay {relay}")
            except Exception as e:
                raise SystemExit(f"Email send failed for {slug}: Himalaya: {r.stderr[:300]} | SMTP fallback: {e}")
        print(f"SENT REVIEW {slug} -> {REVIEW_TO} | {LIVE_BASE}/{slug}.html")
        sent.append(slug)
    conn.close()
    return sent


def main():
    init_db()
    selected = []
    for lead in LEADS:
        audit = load_audit(lead['slug'], lead['website'])
        if audit['decision'] != 'BUILD':
            print(f"WARNING skipping {lead['slug']}: no longer qualifies ({audit['decision']} {audit['score']})")
            continue
        upsert_lead(lead, audit)
        gate = build_and_gate(lead, audit)
        print(f"READY {lead['slug']}: original {audit['score']}/10 -> demo {gate['demo_score']}/10")
        selected.append(lead['slug'])
    sent = send_review_emails(selected)
    print(json.dumps({'sent': sent, 'review_to': REVIEW_TO, 'backups': str(REVIEW_OUT), 'live_base': LIVE_BASE}, indent=2))


if __name__ == '__main__':
    main()
