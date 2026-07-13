#!/usr/bin/env python3
"""
Batch scan all known Powys garage sites using browser-rendered v4 scoring.
Saves only sub-5.0 leads to freshsites.db.

Usage: PYTHONPATH="" python3.11 agents/scan_batch.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from hermes_tools import browser_navigate, browser_snapshot
from scoring_v4 import analyze_content, analyze_design, analyze_conversion, score_from_analysis
import sqlite3, re, json, time
from datetime import datetime

DB = Path(__file__).parent.parent / "leads" / "freshsites.db"
EXTRACTED_DIR = Path(__file__).parent.parent / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)

URLS = [
    "https://www.crossing-garage.co.uk/",
    "https://mepostonmotors.co.uk/",
    "https://www.graiggochgarage.co.uk/",
    "https://bradleysgarage.co.uk/",
    "https://daautoswelshpool.co.uk/",
    "https://dcautorepairs.co.uk/",
    "https://ksgaragenewtown.co.uk/",
    "https://jthughesnewtown.co.uk/",
    "https://evansmotorsgarage.co.uk/",
    "https://www.motwelshpool.co.uk/",
]


def scan_one(url: str) -> dict:
    """Scan single URL, return score data."""
    print(f"\n{'='*60}")
    print(f"Scanning: {url}")
    print(f"{'='*60}")
    
    try:
        browser_navigate(url=url)
        time.sleep(3)
        snap = browser_snapshot(full=True)
    except Exception as e:
        print(f"  BROWSER FAIL: {e}")
        return None
    
    # Title from first line
    title = snap.split("\n")[0] if snap else url
    
    # Score
    content = analyze_content(snap, title)
    design = analyze_design(snap, title, url)
    conv = analyze_conversion(snap, title)
    result = score_from_analysis(content, design, conv)
    
    print(f"  Score: {result['score']}/10")
    print(f"  Content: {result['content_score']}, Design: {result['design_score']}, Conversion: {result['conversion_score']}")
    
    return {
        "url": url,
        "title": title,
        "snapshot": snap,
        **result
    }


def save_if_qualified(data: dict):
    """Save sub-5.0 site to DB."""
    score = data["score"]
    if score >= 5.0:
        print(f"  DISQUALIFIED: {score} >= 5.0")
        return False
    
    url = data["url"]
    title = data["title"]
    snap = data["snapshot"]
    
    # Extract business data
    text = snap
    low = text.lower()
    
    # Phone
    tel_match = re.search(r'href="tel:([\d\s\(\)\-+]+)"', text)
    if tel_match:
        phone = tel_match.group(1).strip()
    else:
        phone_match = re.search(r'(?:tel|phone|call|contact)\s*[\:：]?\s*([\d\s\(\)\-]{8,})', text, re.I)
        phone = phone_match.group(1).strip() if phone_match else ""
    phone = re.sub(r'\s+', ' ', phone) if phone else ""
    
    # Email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    email = email_match.group(1) if email_match else ""
    
    # Address (postcode context)
    address = ""
    pc_match = re.search(r'((?:LD|SY|HR|NP|CF|SA)\d{1,2}\s?\d[A-Z]{2})', text)
    if pc_match:
        postcode = pc_match.group(1)
        idx = text.find(postcode)
        context = text[max(0, idx-200):idx+50]
        lines = [l.strip() for l in context.split("\n") if l.strip() and len(l.strip()) > 3]
        if len(lines) >= 2:
            address = ", ".join(lines[-3:])
    
    # Business name
    name_match = re.search(r'heading\s+"([^"]{3,60})"\s+\[level=1', text)
    if not name_match:
        name_match = re.search(r'heading\s+"([^"]{3,60})"\s+\[level=2', text)
    business_name = name_match.group(1) if name_match else title.split("|")[0].strip()
    
    # Services
    services = []
    for kw in ["Servicing", "Repair", "MOT", "Tyre", "Clutch", "Brake", "Exhaust", "Air Con", "Diagnostic", "Timing"]:
        if kw.lower() in low:
            services.append(kw)
    
    # Slug
    slug = re.sub(r'\W+', '-', url.replace('https://', '').replace('http://', '').rstrip('/'))
    slug = re.sub(r'^-+|-+$', '', slug)
    demo_url = f"https://propagatemedia.github.io/freshsites-outreach/demos/{slug}.html"
    
    # Save to DB
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO leads 
        (name, website, phone, email, address, score, score_breakdown, demo_url, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        business_name, url, phone, email, address,
        score, json.dumps(data), demo_url, 'scored',
        datetime.now().isoformat(), datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    
    # Save cache
    cache = {
        "name": business_name, "slug": slug, "url": url, "title": title,
        "phone": phone, "email": email, "location": address,
        "services": services, "extracted_at": datetime.now().isoformat(),
    }
    (EXTRACTED_DIR / f"{slug}.json").write_text(json.dumps(cache, indent=2))
    
    print(f"  SAVED: {business_name} - {score}/10")
    return True


def main():
    saved_count = 0
    for url in URLS:
        data = scan_one(url)
        if data:
            if save_if_qualified(data):
                saved_count += 1
    
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE: {saved_count} sub-5.0 sites saved")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
