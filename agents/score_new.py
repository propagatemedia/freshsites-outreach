#!/usr/bin/env python3
"""
Score a single URL using browser-rendered v4 scoring.
Saves to freshsites.db if sub-5.0.

Usage:
    PYTHONPATH="" python3.11 agents/score_new.py <url>
"""
import json, re, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path

DB = Path(__file__).parent.parent / "leads" / "freshsites.db"
SCORER = Path(__file__).parent / "scoring_v4.py"


def get_title_and_text(url: str) -> tuple[str, str]:
    """Use browser_navigate + browser_snapshot (full) to get rendered text."""
    # Write a temp script that uses the browser tools
    script = f'''
import json, sys, time
sys.path.insert(0, "{Path(__file__).parent}")

# Import browser tools from hermes context
from hermes_tools import browser_navigate, browser_snapshot, browser_get_images

try:
    browser_navigate(url="{url}")
    time.sleep(3)  # Wait for hydration
    snap = browser_snapshot(full=True)
    print("SNAPSHOT_START")
    print(snap)
    print("SNAPSHOT_END")
except Exception as e:
    print("ERROR: " + str(e), file=sys.stderr)
    sys.exit(1)
'''
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=60,
        env={**dict(subprocess.os.environ), "PYTHONPATH": ""}
    )
    
    # Parse snapshot from output
    output = result.stdout
    start_marker = "SNAPSHOT_START\n"
    end_marker = "\nSNAPSHOT_END"
    
    start = output.find(start_marker)
    end = output.find(end_marker)
    
    if start == -1 or end == -1:
        print(f"Browser snapshot failed for {url}")
        print("stdout:", output[:500])
        print("stderr:", result.stderr[:500])
        return None, None
    
    snapshot = output[start + len(start_marker):end]
    
    # Extract title from snapshot
    title_match = re.search(r'title="([^"]+)"', snapshot)
    title = title_match.group(1) if title_match else url
    
    return title, snapshot


def score_with_v4(url: str, title: str, snapshot: str) -> dict:
    """Pipe snapshot to scoring_v4.py."""
    result = subprocess.run(
        [sys.executable, str(SCORER), url, title],
        input=snapshot,
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except:
        print(f"Scoring parse error: {result.stderr}")
        return None


def extract_data_from_snapshot(snapshot: str) -> dict:
    """Extract key business data from the snapshot."""
    text = snapshot
    
    # Phone
    phone_match = re.search(r'(?:tel|phone|contact).*?(\d[\d\s\(\)\-]{8,})', text, re.I)
    phone = phone_match.group(1).strip() if phone_match else None
    if phone:
        phone = re.sub(r'\s+', ' ', phone)
    
    # Email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    email = email_match.group(1) if email_match else None
    
    # Address
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    address_lines = []
    for i, line in enumerate(lines):
        if re.search(r'(?:ld|sy|hr|np|cf|sa)\d[0-9a-z]?\s?\d[a-z]{2}', line, re.I):
            # Found postcode - capture 2-3 lines before
            start = max(0, i - 2)
            address_lines = lines[start:i+1]
            break
    address = '\n'.join(address_lines) if address_lines else None
    
    # Hours
    hour_match = re.search(r'(?:mon\s*[-–]?\s*fri|opening|open|hours).*?(?:\d[\.:]\d{2}|am|pm|closed)', text, re.I)
    hours = hour_match.group(0) if hour_match else None
    
    return {
        "phone": phone,
        "email": email,
        "address": address,
        "hours": hours,
    }


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"Analyzing: {url}")
    
    # 1. Browser render
    title, snapshot = get_title_and_text(url)
    if not snapshot:
        print(f"FAILED: Could not render {url}")
        sys.exit(1)
    
    print(f"  Title: {title}")
    print(f"  Snapshot length: {len(snapshot)} chars")
    
    # 2. Score
    result = score_with_v4(url, title, snapshot)
    if not result:
        print("FAILED: Scoring error")
        sys.exit(1)
    
    print(f"\n  === SCORE: {result['score']}/10 ===")
    print(f"  Content: {result['content_score']}/10")
    print(f"  Design: {result['design_score']}/10")
    print(f"  Conversion: {result['conversion_score']}/10")
    print(f"\n  Content findings:")
    for f in result['content']:
        print(f"    - {f}")
    print(f"\n  Design findings:")
    for f in result['design']:
        print(f"    - {f}")
    print(f"\n  Conversion findings:")
    for f in result['conversion']:
        print(f"    - {f}")
    
    # 3. Only save if sub-5.0
    if result['score'] >= 5.0:
        print(f"\n  DISQUALIFIED: Score {result['score']} >= 5.0")
        return
    
    # 4. Extract data and save to DB
    biz_data = extract_data_from_snapshot(snapshot)
    
    # Create slug from URL
    slug = re.sub(r'\W+', '-', url.replace('https://', '').replace('http://', '').rstrip('/'))
    slug = re.sub(r'^-+|-+$', '', slug)
    
    demo_url = f"https://propagatemedia.github.io/freshsites-outreach/demos/{slug}.html"
    
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    c.execute('''
        INSERT INTO leads 
        (name, website, phone, email, address, score, score_breakdown, demo_url, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (
        title.split('|')[0].strip() if '|' in title else title,
        url,
        biz_data.get('phone'),
        biz_data.get('email'),
        biz_data.get('address'),
        result['score'],
        json.dumps(result),
        demo_url,
        'scored'
    ))
    conn.commit()
    conn.close()
    
    print(f"\n  SAVED to leads DB as 'scored' (score: {result['score']})")
    
    # 5. Save extracted cache for demo generation
    extracted = {
        "name": title.split('|')[0].strip() if '|' in title else title,
        "slug": slug,
        "url": url,
        "title": title,
        "phone": biz_data.get('phone', ''),
        "email": biz_data.get('email', ''),
        "location": biz_data.get('address', ''),
        "hours": biz_data.get('hours', ''),
        "extracted_at": __import__('datetime').datetime.now().isoformat(),
    }
    cache_dir = Path(__file__).parent.parent / "extracted"
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / f"{slug}.json").write_text(json.dumps(extracted, indent=2))
    print(f"  Saved extracted cache: extracted/{slug}.json")


if __name__ == "__main__":
    main()
