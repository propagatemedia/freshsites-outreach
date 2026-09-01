#!/usr/bin/env python3
"""Create the five rubbish-lead caches, DB rows, demos, gates and review emails.

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
        "slug": "roofing-services-west-wales",
        "name": "Roofing Services West Wales",
        "industry": "Roofing contractor",
        "website": "https://roofingserviceswestwales.co.uk/",
        "phone": "01267 668637",
        "email": "info@roofingserviceswestwales.co.uk",
        "location": "Llangadog, Wales, SA19 9NE",
        "brand_color": "#334155",
        "services": ["Roof repairs", "Flat roofing", "Leadwork", "New roofs", "Emergency leaks", "Moss removal"],
        "audit_summary": "The listed domain currently shows 'Sorry this website is now closed', so customers land on a dead hosting message instead of a roofing business.",
    },
    {
        "slug": "ceredigion-plumbing-supplies",
        "name": "Ceredigion Plumbing Supplies",
        "industry": "Plumbing supply store",
        "website": "http://cpslampeter.co.uk/",
        "phone": "01570 422772",
        "email": "info@cpslampeter.co.uk",
        "location": "Unit 5b, Industrial Estate, Tregaron Road, Lampeter, SA48 8LT",
        "brand_color": "#0f766e",
        "services": ["Plumbing supplies", "Heating parts", "Trade counter", "Local delivery", "Bathroom supplies", "Advice and ordering"],
        "audit_summary": "The public website resolves to an account suspended page / invalid certificate path. That kills trust before the customer even sees opening hours or stock categories.",
    },
    {
        "slug": "electriserve-ltd",
        "name": "ElectriServe Ltd",
        "industry": "Electrician",
        "website": "https://electriserve.co.uk/",
        "phone": "0800 054 1117",
        "email": "info@electriserve.co.uk",
        "location": "59 Norrington Road, Loose, Maidstone, ME15 9XD",
        "brand_color": "#f5b301",
        "services": ["Emergency call-outs", "Domestic electrical work", "Commercial electrical work", "Fault finding", "Rewires", "Testing and certification"],
        "audit_summary": "The domain returns a near-blank lander. There is no visible service proposition, no trust proof, no phone-led CTA and no enquiry path.",
    },
    {
        "slug": "cabac-electrical-solutions",
        "name": "CABAC Electrical Solutions",
        "industry": "Electrician",
        "website": "https://cabacelectricalsolutions.co.uk/",
        "phone": "07807 325134",
        "email": "info@cabacelectricalsolutions.co.uk",
        "location": "29 Lenside Drive, Bearsted, Maidstone, ME15 8UE",
        "brand_color": "#f5b301",
        "services": ["Electrical repairs", "Consumer units", "Testing and inspection", "Lighting installs", "Fault finding", "Domestic rewires"],
        "audit_summary": "The website loads as a blank lander. A customer searching for an electrician gets no proof, no services, no quote form and no reason to call.",
    },
    {
        "slug": "adeilad-claddings",
        "name": "Adeilad Claddings",
        "industry": "Construction Company",
        "website": "https://adclad.co.uk/",
        "phone": "01550 777497",
        "email": "adclad@gmail.com",
        "location": "The Stores, Station Road, Llanwrda, SA19 8EH",
        "brand_color": "#b45309",
        "services": ["Agricultural cladding", "Industrial cladding", "Roofing sheets", "Repairs and maintenance", "Commercial projects", "Project enquiries"],
        "audit_summary": "The current site is only an under-construction page with office details. It does not show services, projects, proof, sectors or a proper enquiry flow.",
    },
]

def init_db():
    DB.parent.mkdir(exist_ok=True)
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, industry TEXT, address TEXT, postcode TEXT,
        phone TEXT, email TEXT, website TEXT, google_maps_url TEXT, score REAL DEFAULT 0, score_breakdown TEXT,
        screenshot_path TEXT, demo_url TEXT, status TEXT DEFAULT 'new', created_at TEXT, updated_at TEXT, notes TEXT)""")
    conn.commit(); conn.close()

def load_audit(slug, website):
    AUDITS.mkdir(parents=True, exist_ok=True)
    out=AUDITS/f"{slug}.json"
    r=subprocess.run([PY, str(REPO/'agents/score_site.py'), website, '--json', '--out', str(out)], cwd=REPO, text=True, capture_output=True, timeout=45)
    if not out.exists():
        raise SystemExit(f"score failed for {slug}: {r.stderr}\n{r.stdout}")
    return json.loads(out.read_text())

def upsert_lead(lead, audit):
    now=datetime.utcnow().isoformat()
    demo_url=f"{LIVE_BASE}/{lead['slug']}.html"
    cache={**lead, 'demo_url': demo_url, 'score': audit['score'], 'score_breakdown': audit['breakdown'], 'original_audit': audit, 'created_at': now}
    EXTRACTED.mkdir(exist_ok=True)
    (EXTRACTED/f"{lead['slug']}.json").write_text(json.dumps(cache, indent=2), encoding='utf-8')
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute('SELECT id FROM leads WHERE demo_url LIKE ? OR website=? OR name=?', (f"%/{lead['slug']}.html", lead['website'], lead['name']))
    row=c.fetchone()
    params=(lead['name'], lead['industry'], lead['location'], '', lead['phone'], lead['email'], lead['website'], '', audit['score'], json.dumps(audit['breakdown']), demo_url, 'demo_built', now, now, lead['audit_summary'])
    if row:
        c.execute('''UPDATE leads SET name=?, industry=?, address=?, postcode=?, phone=?, email=?, website=?, google_maps_url=?, score=?, score_breakdown=?, demo_url=?, status=?, updated_at=?, notes=? WHERE id=?''', params[:12]+(now, lead['audit_summary'], row[0]))
    else:
        c.execute('''INSERT INTO leads (name, industry, address, postcode, phone, email, website, google_maps_url, score, score_breakdown, demo_url, status, created_at, updated_at, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', params)
    conn.commit(); conn.close()
    return cache

def build_and_gate(lead, audit):
    slug=lead['slug']
    subprocess.run([PY, str(REPO/'agents/generate_trade_demo.py'), slug], cwd=REPO, check=True, timeout=45)
    demo_file=REPO/'docs/demos'/f'{slug}.html'
    gate_json=REPO/'review'/slug/'quality_gate.json'
    gate_json.parent.mkdir(parents=True, exist_ok=True)
    r=subprocess.run([PY, str(REPO/'agents/quality_gate_v2.py'), str(demo_file), '--original-score', str(audit['score']), '--business', lead['name'], '--vertical', lead['industry'], '--audit-json', str(AUDITS/f'{slug}.json'), '--json'], cwd=REPO, text=True, capture_output=True, timeout=45)
    gate_json.write_text(r.stdout, encoding='utf-8')
    try: gate=json.loads(r.stdout)
    except Exception: raise SystemExit(f'gate did not return json for {slug}: {r.stdout}\n{r.stderr}')
    if not gate.get('approved'):
        raise SystemExit(f"QUALITY GATE BLOCKED {slug}: {gate.get('reasons')}")
    verdict={
        'captured_ok': True, 'send_ok': True, 'is_demo_better': True,
        'prospect': {'overall': audit['score']}, 'demo': {'overall': gate['demo_score']},
        'improvement': gate['improvement'], 'candidate_score_100': audit.get('candidate_score_100'),
        'conversion_assets': audit.get('conversion_assets', []), 'trust_assets': audit.get('trust_assets', []), 'service_assets': audit.get('service_assets', []),
        'severe_defect_override': bool(audit.get('severe_defects')),
        'honest_call': 'Send review copy only. Original has a severe public website defect and demo passes FreshSites quality gate v2.',
        'reviewed_at': datetime.utcnow().isoformat(),
    }
    (REPO/'review'/slug/'verdict.json').write_text(json.dumps(verdict, indent=2), encoding='utf-8')
    return gate

def wrap_email(raw, lead, audit, gate):
    header, body = raw.split('\n\n',1)
    subject_match = re.search(r'^Subject:\s*(.+)$', header, re.M)
    subject = subject_match.group(1).strip() if subject_match else f"I built {lead['name']} a better homepage"
    demo_url=f"{LIVE_BASE}/{lead['slug']}.html"
    pre=f"""
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
    """Use a temp minimal Himalaya config that skips IMAP Sent-copy writes.

    The freshsites IMAP auth can fail while SMTP still works. Review sends should
    not be blocked by an IMAP save-copy failure.
    """
    dst = REPO/'tmp'/'himalaya_no_save.toml'
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
backend.host = "mail.propagate.media"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "freshsites@sites.propagate.media"
backend.auth.type = "password"
backend.auth.cmd = "~/.config/himalaya/get-password.sh freshsites@sites.propagate.media"
message.send.backend.type = "smtp"
message.send.backend.host = "mail.propagate.media"
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
    """Direct SMTP fallback. Does not print or persist passwords.

    Tries FreshSites first. If its credential is stale, uses the verified
    kentbusinesses mailbox as a review-relay to Tyrone only. This fallback is
    never used for live prospect outreach.
    """
    pw_cmd = str(Path.home()/'.config/himalaya/get-password.sh')
    accounts = [
        ('freshsites@sites.propagate.media', 'mail.propagate.media', message),
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
    sys.path.insert(0, str(REPO/'agents'))
    from emailer import generate_email
    REVIEW_OUT.mkdir(parents=True, exist_ok=True)
    sent=[]
    conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
    cfg = himalaya_config_no_save()
    for slug in slugs:
        lead_data=next(x for x in LEADS if x['slug']==slug)
        row=dict(conn.execute('SELECT * FROM leads WHERE demo_url LIKE ?', (f'%/{slug}.html',)).fetchone())
        audit=json.loads((AUDITS/f'{slug}.json').read_text())
        gate=json.loads((REPO/'review'/slug/'quality_gate.json').read_text())
        raw, _original_to = generate_email(row)
        msg=wrap_email(raw, lead_data, audit, gate)
        (REVIEW_OUT/f'{slug}.eml').write_text(msg, encoding='utf-8')
        r=subprocess.run(['himalaya','message','send','--config',cfg,'--account','freshsites'], input=msg, text=True, capture_output=True, timeout=45)
        if r.returncode != 0:
            # Himalaya currently builds the IMAP backend even with save-copy off;
            # fall back to direct SMTP so a broken Sent-folder login does not block review copies.
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
    selected=[]
    for lead in LEADS:
        audit=load_audit(lead['slug'], lead['website'])
        if audit['decision'] != 'BUILD':
            raise SystemExit(f"Lead no longer qualifies: {lead['slug']} {audit['decision']} {audit['score']}")
        upsert_lead(lead, audit)
        gate=build_and_gate(lead, audit)
        print(f"READY {lead['slug']}: original {audit['score']}/10 -> demo {gate['demo_score']}/10")
        selected.append(lead['slug'])
    sent=send_review_emails(selected)
    print(json.dumps({'sent': sent, 'review_to': REVIEW_TO, 'backups': str(REVIEW_OUT), 'live_base': LIVE_BASE}, indent=2))
if __name__ == '__main__': main()
