#!/usr/bin/env python3
"""
Re-score all demo_built leads using the actual v3 scoring engine.
Updates freshsites.db with per-site score and breakdown.
"""
import sqlite3, requests, re, sys, json
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from scoring_v3 import score_website_v3

DB = Path(__file__).parent.parent / "leads" / "freshsites.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


def fetch_and_score(name, url):
    """Fetch site and score using v3 engine."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  FETCH FAIL: {url} - {e}")
        return None, None

    # Extract rendered text (what a user actually sees)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Remove script/style/nav/footer/noise
    for tag in soup(["script", "style", "nav", "footer", "noscript"]):
        tag.decompose()
    
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    
    # Get visible text
    text = " ".join(t.strip() for t in soup.stripped_strings)
    text = " ".join(text.split())  # Collapse whitespace
    text = text[:4000]

    # Check for iframes (mobile indicator / bloat)
    has_iframes = len(soup.find_all("iframe")) > 0

    score, breakdown = score_website_v3(text, title, url, has_iframes)
    
    return score, breakdown


def main():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name, website FROM leads WHERE status='demo_built' ORDER BY score")
    leads = c.fetchall()
    
    if not leads:
        print("No leads to score.")
        return

    updated = 0
    for lead in leads:
        name = lead["name"]
        url = lead["website"]
        print(f"\n[{name}] {url}")
        
        score, breakdown = fetch_and_score(name, url)
        if score is None:
            continue
            
        # Show what was actually detected
        actual = {k:v for k,v in breakdown.items() if v != 0}
        print(f"  Score: {score}/10")
        print(f"  Issues: {json.dumps(actual, indent=4)}")
        
        # Update database
        bd_json = json.dumps(breakdown)
        c.execute(
            "UPDATE leads SET score=?, score_breakdown=? WHERE id=?",
            (round(score, 1), bd_json, lead["id"])
        )
        conn.commit()
        updated += 1

    conn.close()
    print(f"\n=== Updated {updated}/{len(leads)} scores ===")


if __name__ == "__main__":
    main()
