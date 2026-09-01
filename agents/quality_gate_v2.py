#!/usr/bin/env python3
"""FreshSites quality gate v2.

Hard gate for demo review emails. It blocks the two embarrassing failure modes:
1. Pitching businesses whose current site is already commercially functional.
2. Sending demos with missing conversion elements, broken assets, wrong vertical copy,
   invisible CTA text, missing buy bar, or dead form action.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIN_DEMO_SCORE = 8.0
MIN_IMPROVEMENT = 3.0
MAX_ORIGINAL_SCORE = 5.0

class DemoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""; self.in_title = False; self.text=[]; self.h1=[]; self.h2=[]
        self.forms=0; self.submit=0; self.tel=0; self.mail=0; self.imgs=[]; self.iframes=[]; self.buttons=[]; self.links=[]
        self.name_fields=set(); self.viewport=False
    def handle_starttag(self, tag, attrs):
        d={k.lower():v or "" for k,v in attrs}
        if tag=='title': self.in_title=True
        if tag=='meta' and d.get('name','').lower()=='viewport': self.viewport=True
        if tag=='form': self.forms+=1; self.form_action=d.get('action','')
        if tag=='input' and d.get('name'): self.name_fields.add(d.get('name'))
        if tag=='textarea' and d.get('name'): self.name_fields.add(d.get('name'))
        if tag=='button': self.buttons.append(d); self.submit += int(d.get('type','').lower()=='submit')
        if tag=='img' and d.get('src'): self.imgs.append(d.get('src'))
        if tag=='iframe' and d.get('src'): self.iframes.append(d.get('src'))
        if tag=='a':
            href=d.get('href',''); self.links.append(href); self.tel += int(href.startswith('tel:')); self.mail += int(href.startswith('mailto:'))
    def handle_endtag(self, tag):
        if tag=='title': self.in_title=False
    def handle_data(self, data):
        s=re.sub(r'\s+',' ',data).strip()
        if not s: return
        self.text.append(s)
        if self.in_title: self.title += ' '+s
        # Heading extraction is intentionally done by regex against raw HTML below.

def read_html(path_or_url: str):
    if re.match(r'^https?://', path_or_url):
        req=urllib.request.Request(path_or_url, headers={'User-Agent':'Mozilla/5.0 FreshSites gate'})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode(r.headers.get_content_charset() or 'utf-8','replace'), path_or_url
    p=Path(path_or_url)
    if not p.is_absolute(): p=REPO/p
    return p.read_text(encoding='utf-8'), str(p)

def verify_image(src: str, base: str):
    if src.startswith('data:'): return True, 'data'
    if re.match(r'^https?://', src): url=src
    else:
        if re.match(r'^https?://', base): url=urllib.parse.urljoin(base, src)
        else:
            p=Path(base).parent / src
            return p.exists(), str(p)
    try:
        req=urllib.request.Request(url, method='HEAD', headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status < 400, url
    except Exception as e:
        return False, f'{url} ({e})'

def score_demo(html: str, base: str, expected_name: str, vertical: str):
    p=DemoParser(); p.feed(html)
    text=' '.join(p.text); low=(html+' '+text).lower(); issues=[]; score=10.0
    def fail(amount, msg):
        nonlocal score; score-=amount; issues.append(msg)
    if not p.viewport: fail(1.0,'missing mobile viewport')
    if not re.search(r'<h1[^>]*>\s*[^<]{18,}', html, re.I|re.S): fail(1.3,'weak/missing H1')
    if expected_name and expected_name.split()[0].lower() not in p.title.lower(): fail(0.8,'title does not contain business name')
    if p.forms < 1: fail(1.2,'missing contact form')
    if p.submit < 1: fail(0.8,'form missing submit button')
    for field in ['name','email','message']:
        if field not in p.name_fields: fail(0.5,f'form missing {field}')
    if p.tel < 1: fail(1.0,'missing tel: link')
    if not any('google.com/maps' in x or 'maps?' in x for x in p.iframes): fail(0.8,'missing Google map embed')
    if 'buy-bar' not in low or 'get this site' not in low: fail(1.0,'missing buy bar')
    if '£149' not in html: fail(0.7,'missing £149 price')
    if 'not for me' not in low: fail(0.5,'missing Not For Me flow')
    if 'color:#fff' not in low and 'color: #fff' not in low and 'color:white' not in low: fail(0.7,'no forced white CTA text')
    if 'formsubmit.co/ajax' not in low and 'formspree' not in low and 'web3forms' not in low: fail(0.8,'form action is not wired to an inbox service')
    if len(re.findall(r'class="service-card"|class="card"|<article', html, re.I)) < 3: fail(1.0,'fewer than 3 service cards')
    broken=[]
    for src in p.imgs:
        ok, loc=verify_image(src, base)
        if not ok: broken.append(loc)
    if broken: fail(1.5, 'broken images: '+ '; '.join(broken[:3]))
    if len(p.imgs) < 1: fail(0.8,'no hero/image asset')
    if vertical and vertical.lower() not in ['garage','automotive'] and re.search(r'\bgarage\b|\bmot\b|\bcar service\b', low):
        fail(1.5,'wrong vertical copy appears to be garage/automotive')
    if re.search(r'lorem ipsum|12345 somewhere|user@untitled|nashville', low): fail(1.2,'template placeholder text leaked')
    return round(max(0,score),1), issues

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('demo')
    ap.add_argument('--original-score', type=float, required=True)
    ap.add_argument('--business', default='')
    ap.add_argument('--vertical', default='')
    ap.add_argument('--audit-json')
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args(argv)
    html,base=read_html(args.demo)
    demo_score, issues=score_demo(html, base, args.business, args.vertical)
    original=args.original_score
    severe=False; candidate_score=None; conversion_assets=[]; trust_service=[]
    if args.audit_json and Path(args.audit_json).exists():
        audit=json.loads(Path(args.audit_json).read_text())
        severe=bool(audit.get('severe_defects'))
        candidate_score=audit.get('candidate_score_100')
        conversion_assets=audit.get('conversion_assets') or []
        trust_service=(audit.get('trust_assets') or [])+(audit.get('service_assets') or [])
    approved=True; reasons=[]
    if not severe and original >= MAX_ORIGINAL_SCORE: reasons.append(f'original score {original}/10 is not weak enough')
    if candidate_score is not None and not severe and candidate_score >= 50: reasons.append(f'candidate score {candidate_score}/100 too functional')
    if len(conversion_assets) >= 4 and len(trust_service) >= 3 and not severe: reasons.append('original already has too much conversion/trust infrastructure')
    if demo_score < MIN_DEMO_SCORE: reasons.append(f'demo score {demo_score}/10 below {MIN_DEMO_SCORE}')
    if demo_score - original < MIN_IMPROVEMENT: reasons.append(f'improvement {demo_score-original:+.1f} below +{MIN_IMPROVEMENT}')
    if issues: reasons.extend(issues)
    approved=not reasons
    out={'approved':approved,'demo_score':demo_score,'original_score':original,'improvement':round(demo_score-original,1),'reasons':reasons,'severe_original_defect':severe,'candidate_score_100':candidate_score}
    if args.json: print(json.dumps(out,indent=2))
    else:
        print(f"QUALITY GATE {'PASS' if approved else 'BLOCK'}: {args.business or args.demo}")
        print(f"original {original}/10 -> demo {demo_score}/10 ({demo_score-original:+.1f})")
        for r in reasons: print('-',r)
    return 0 if approved else 1
if __name__=='__main__': sys.exit(main())
