#!/usr/bin/env python3
"""
Day 5 resend: Check for replies, send follow-ups to leads with no response.
Runs daily at 09:00 — only triggers for demos in +5d window.
"""

import sqlite3
from datetime import datetime, timedelta
import subprocess
import sys

def get_db():
    return sqlite3.connect('leads/freshsites.db')

def resend_follow_ups():
    conn = get_db()
    c = conn.cursor()
    
    # Find leads sent 5-7 days ago with no follow-up sent yet
    now = datetime.now()
    five_days_ago = (now - timedelta(days=5)).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    
    c.execute("""
        SELECT id, name, email, demo_url 
        FROM leads 
        WHERE status = 'sent' 
        AND demo_created_at BETWEEN ? AND ?
        AND follow_up_sent_at IS NULL
        AND email IS NOT NULL
    """, (seven_days_ago, five_days_ago))
    
    leads_to_resend = c.fetchall()
    
    if not leads_to_resend:
        print(f"[{now.strftime('%Y-%m-%d %H:%M')}] No leads ready for Day 5 resend")
        return 0
    
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Day 5 Resend: {len(leads_to_resend)} leads")
    
    sent = 0
    for lead_id, name, email, demo_url in leads_to_resend:
        # Send follow-up email
        body = f"""Hi {name},

I wanted to follow up on the website rebuild proposal I sent over last week.

I know you're busy, so here's the quick version:
- Your current site has several issues affecting leads
- We can rebuild it for £149 + discovery call
- Takes about 2 weeks start-to-finish

Demo of what it could look like: {demo_url}

If this interests you, let's schedule 15 minutes:
https://propagate.media/schedule-call

Otherwise, no worries — just let me know.

Cheers,
FreshSites Team"""
        
        # Use send_live.py or direct SMTP
        try:
            result = subprocess.run(
                ["mail", "-s", f"Follow-up: {name} Website Rebuild", email],
                input=body.encode(),
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                sent += 1
                c.execute(
                    "UPDATE leads SET follow_up_sent_at = ?, status = 'follow_up_sent' WHERE id = ?",
                    (now.isoformat(), lead_id)
                )
        except Exception as e:
            print(f"  ✗ {name}: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    
    print(f"  ✓ Sent {sent} follow-ups")
    return sent

if __name__ == '__main__':
    resend_follow_ups()
