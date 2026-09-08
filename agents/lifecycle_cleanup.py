#!/usr/bin/env python3
"""
Day 15 cleanup: Delete expired demos from GitHub Pages.
Only deletes if NO reply received. Engaged leads kept indefinitely.
Bounces also kept for analysis.
"""

import sqlite3
from datetime import datetime, timedelta
import subprocess
import os

def get_db():
    return sqlite3.connect('leads/freshsites.db')

def cleanup_expired_demos():
    conn = get_db()
    c = conn.cursor()
    
    now = datetime.now()
    fifteen_days_ago = (now - timedelta(days=15)).isoformat()
    
    # Find demos created 15+ days ago, no reply, not engaged
    c.execute("""
        SELECT id, name, demo_url 
        FROM leads 
        WHERE demo_created_at <= ?
        AND status NOT IN ('lead_engaged', 'bounced')
        AND demo_url IS NOT NULL
    """, (fifteen_days_ago,))
    
    to_delete = c.fetchall()
    
    if not to_delete:
        print(f"[{now.strftime('%Y-%m-%d %H:%M')}] No expired demos to clean")
        return 0
    
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Day 15 Cleanup: {len(to_delete)} demos expiring")
    
    deleted = 0
    os.chdir('/Users/tyronemacmini/git/freshsites-outreach')
    
    for lead_id, name, demo_url in to_delete:
        # Extract filename from URL
        # https://propagatemedia.github.io/freshsites-outreach/demos/electriserve-ltd.html
        filename = demo_url.split('/')[-1]
        filepath = f'docs/demos/{filename}'
        
        try:
            # Remove file if exists
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted += 1
                
                # Commit deletion
                subprocess.run(['git', 'rm', filepath], check=True)
                subprocess.run(
                    ['git', 'commit', '-m', f'Auto-cleanup Day 15: Delete expired demo for {name}'],
                    check=True,
                    capture_output=True
                )
                subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
                
                # Mark in DB
                c.execute(
                    "UPDATE leads SET status = 'demo_deleted', demo_url = NULL WHERE id = ?",
                    (lead_id,)
                )
                
                print(f"  ✓ Deleted: {name}")
        except Exception as e:
            print(f"  ✗ {name}: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    
    print(f"  Total deleted: {deleted}")
    return deleted

if __name__ == '__main__':
    cleanup_expired_demos()
