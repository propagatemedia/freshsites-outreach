#!/usr/bin/env python3
"""
Day 10 check: Scan mailbox for replies from prospects.
Marks leads as lead_engaged if response received.
"""

import sqlite3
from datetime import datetime, timedelta
import imaplib
import email
import re

def get_db():
    return sqlite3.connect('leads/freshsites.db')

def check_replies():
    conn = get_db()
    c = conn.cursor()
    
    # Get IMAP credentials (from env or config)
    try:
        m = imaplib.IMAP4_SSL('c1100730.sgvps.net', 993, timeout=20)
        m.login('freshsites@sites.propagate.media', open('/Users/tyronemacmini/.config/himalaya/password.txt').read().strip())
    except Exception as e:
        print(f"IMAP auth failed: {str(e)[:50]}")
        return 0
    
    m.select('INBOX')
    status, data = m.search(None, 'SINCE', (datetime.now() - timedelta(days=6)).strftime('%d-%b-%Y'))
    ids = data[0].split()
    
    matched = 0
    now = datetime.now()
    
    # Get all leads we've contacted
    c.execute("SELECT id, name, email FROM leads WHERE status IN ('sent', 'follow_up_sent')")
    our_leads = {row[2]: row[0] for row in c.fetchall() if row[2]}  # email -> id
    
    # Check each reply
    for msg_id in ids:
        status, msg_data = m.fetch(msg_id, '(RFC822)')
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        
        from_addr = msg.get('From', '').lower()
        
        # Match sender to our leads
        for our_email, lead_id in our_leads.items():
            if our_email.lower() in from_addr or from_addr in our_email.lower():
                # Found a reply!
                c.execute(
                    "UPDATE leads SET status = 'lead_engaged', last_reply_checked_at = ? WHERE id = ?",
                    (now.isoformat(), lead_id)
                )
                matched += 1
                print(f"  ✓ Reply from {from_addr} → marked as engaged")
                break
    
    conn.commit()
    m.close()
    
    print(f"Day 10 Check: {matched} replies found")
    return matched

if __name__ == '__main__':
    check_replies()
