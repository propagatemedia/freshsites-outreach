#!/usr/bin/env python3
"""
Score+Extract Pipeline v4
Browser renders each URL, scores honestly, saves sub-5.0 to DB.

Usage:
    PYTHONPATH="" python3.11 agents/scan_and_score.py <url>
    
Or batch:
    cat urls.txt | while read url; do PYTHONPATH="" python3.11 agents/scan_and_score.py "$url"; done
"""
import json, re, sqlite3, sys, time
from datetime import datetime
from pathlib import Path

# Import browser tools
from hermes_tools import browser_navigate, browser_snapshot, browser_get_images

DB = Path(__file__).parent.parent / "leads" / "freshsites.db"
EXTRACTED_DIR = Path(__file__).parent.parent / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)


def get_snapshot(url: str, wait_seconds: int = 3) -> tuple[str, str]:
    """Browser navigate + snapshot. Returns (title, snapshot_text)."""
    browser_navigate(url=url)
    time.sleep(wait_seconds)
    snap = browser_snapshot(full=True)
    
    # Extract title from first line
    lines = snap.split("\n")
    title = lines[0] if lines and lines[0] else url
    
    return title, snap


def extract_business_data(snapshot: str, url: str) -> dict:
    """Extract phone, email, hours, address from snapshot."""
    text = snapshot
    low = text.lower()
    
    # Phone - look for tel: links first, then plain text patterns
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
    
    # Hours - look for common patterns
    hours = ""
    hour_patterns = [
        r'Mon\s*[-–]\s*Fri[^\n]{5,30}',
        r'Opening\s*(times|hours)[^\n]{5,40}',
        r'(?:Monday|Mon)[^\n]{3,20}(?:\d[\.:]\d{2})',
    ]
    for p in hour_patterns:
        m = re.search(p, text, re.I)
        if m:
            hours = m.group(0).strip()
            break
    
    # Address
    address = ""
    # Look for postcode + nearby lines
    postcode_match = re.search(r'((?:LD|SY|HR|NP|CF|SA)\d{1,2}\s?\d[A-Z]{2})', text)
    if postcode_match:
        postcode = postcode_match.group(1)
        # Get context (2-3 lines before postcode)
        idx = text.find(postcode)
        context = text[max(0, idx-200):idx+50]
        lines = [l.strip() for l in context.split("\n") if l.strip() and len(l.strip()) > 3]
        if len(lines) >= 2:
            address = ", ".join(lines[-3:])
    
    # Business name from title or h1
    name_match = re.search(r'heading\s+"([^"]{3,60})"\s+\[level=1', text)
    if not name_match:
        name_match = re.search(r'heading\s+"([^"]{3,60})"\s+\[level=2', text)
    name = name_match.group(1) if name_match else ""
    
    # Services from nav/headings
    services = []
    service_keywords = ["Servicing", "Repair", "MOT", "Tyre", "Clutch", "Brake", "Exhaust", "Air Con", "Diagnostic", "Timing", "Wheel", "Collection", "Collection & Delivery"]
    for kw in service_keywords:
        if kw.lower() in low:
            services.append(kw)
    
    return {
        "name": name,
        "phone": phone,
        "email": email,
        "hours": hours,
        "address": address,
        "services": services,
    }


def score_with_v4(snapshot: str, title: str, url: str) -> dict:
    """Import and run v4 scoring."""
    sys.path.insert(0, str(Path(__file__).parent))
    from scoring_v4 import analyze_content, analyze_design, analyze_conversion, score_from_analysis
    
    content = analyze_content(snapshot, title)
    design = analyze_design(snapshot, title, url)
    conv = analyze_conversion(snapshot, title)
    
    return score_from_analysis(content, design, conv)


def save_to_db(url: str, title: str, score_data: dict, extracted: dict):
    """Save scored lead to DB if sub-5.0."""
    score = score_data["score"]
    
    if score >= 5.0:
        return False, f"Score {score} >= 5.0 - disqualified"
    
    # Create slug
    slug = re.sub(r'\W+', '-', url.replace('https://', '').replace('http://', '').rstrip('/'))
    slug = re.sub(r'^-+|-+$', '', slug)
    
    business_name = extracted.get("name") or title.split("|")[0].strip() or title.split("-")[0].strip()
    
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    
    # Check if exists
    c.execute("SELECT id FROM leads WHERE website = ?", (url,))
    existing = c.fetchone()
    
    demo_url = f"https://propagatemedia.github.io/freshsites-outreach/demos/{slug}.html"
    score_json = json.dumps(score_data)
    
    if existing:
        c.execute('''
            UPDATE leads SET score=?, score_breakdown=?, status=?, updated_at=?, 
            name=?, phone=?, email=?, address=?
            WHERE website=?
        ''', (
            score, score_json, 'scored', datetime.now().isoformat(),
            business_name, extracted.get("phone"), extracted.get("email"), extracted.get("address"),
            url
        ))
    else:
        c.execute('''
            INSERT INTO leads 
            (name, website, phone, email, address, score, score_breakdown, demo_url, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            business_name, url, extracted.get("phone"), extracted.get("email"),
            extracted.get("address"), score, score_json, demo_url, 'scored',
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()
    
    # Save extracted cache
    cache = {
        "name": business_name,
        "slug": slug,
        "url": url,
        "title": title,
        **extracted,
        "extracted_at": datetime.now().isoformat(),
    }
    (EXTRACTED_DIR / f"{slug}.json").write_text(json.dumps(cache, indent=2))
    
    return True, f"Saved as '{business_name}' - score {score}/10"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"\n{'='*60}")
    print(f"Scanning: {url}")
    print(f"{'='*60}")
    
    # 1. Browser render
    print("  Loading page...", end=" ")
    try:
        title, snapshot = get_snapshot(url)
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
    
    print(f"  Title: {title[:80]}")
    
    # 2. Extract business data
    print("  Extracting business data...", end=" ")
    extracted = extract_business_data(snapshot, url)
    print(f"phone={extracted['phone'][:15] if extracted['phone'] else 'none'}, services={len(extracted['services'])}")
    
    # 3. Score
    print("  Scoring...", end=" ")
    score_data = score_with_v4(snapshot, title, url)
    print(f"{score_data['score']}/10")
    
    # Show breakdown
    print(f"\n  Content:     {score_data['content_score']}/10")
    for f in score_data['content'][:3]:
        print(f"    - {f}")
    print(f"  Design:      {score_data['design_score']}/10")
    for f in score_data['design'][:3]:
        print(f"    - {f}")
    print(f"  Conversion:  {score_data['conversion_score']}/10")
    for f in score_data['conversion'][:3]:
        print(f"    - {f}")
    
    # 4. Save
    saved, msg = save_to_db(url, title, score_data, extracted)
    print(f"\n  {'SAVED' if saved else 'SKIPPED'}: {msg}")


if __name__ == "__main__":
    main()
