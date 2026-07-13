#!/usr/bin/env python3
"""Batch extract data from all demo_built leads into extracted/{slug}.json cache."""
import sqlite3, subprocess, sys, json
from pathlib import Path

DB = Path(__file__).parent.parent / "leads" / "freshsites.db"
SCRIPT = Path(__file__).parent / "extract_data.py"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT name, website, score FROM leads WHERE status='demo_built' ORDER BY score")
leads = [dict(r) for r in c.fetchall()]
conn.close()

extracted = 0
for lead in leads:
    slug = __import__("re").sub(r"\W+", "-", lead["website"].replace("https://","").replace("http://","").rstrip("/"))
    print(f"\n[{lead['score']}/10] {lead['name']}: {lead['website']}")
    res = subprocess.run(
        [sys.executable, str(SCRIPT), lead["website"], slug],
        capture_output=True, text=True, timeout=120
    )
    stdout = res.stdout.strip()
    if res.returncode == 0 and stdout.startswith("{"):
        try:
            data = json.loads(stdout)
            print(f"  -> {data.get('brand_color','?')} | {len(data.get('services',[]))} svcs")
            extracted += 1
        except Exception as e:
            print(f"  Parse error: {e}")
    else:
        print(f"  FAILED: {res.stderr[:200]}")

print(f"\n=== Extracted {extracted}/{len(leads)} sites ===")
