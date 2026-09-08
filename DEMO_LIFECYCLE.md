# FreshSites Demo Lifecycle & Auto-Cleanup

## Lifecycle Phases

Each demo follows a 15-day lifecycle:

```
Day 0:   INITIAL SEND
         - Build demo HTML
         - Push to GitHub Pages
         - Send cold email to prospect
         - Status: sent
         - Add demo_expires_at: now() + 15 days

Day 5:   RESEND + FOLLOW-UP
         - Check for replies (mailbox scan)
         - If no reply: send follow-up email
         - Status: follow_up_sent
         - Add follow_up_sent_at: timestamp

Day 10:  CHECK REPLIES
         - Scan mailbox for responses
         - If reply found: mark as lead_engaged
         - If bounce: mark as bounced
         - Status: checked

Day 15:  AUTO-DELETE
         - If status NOT lead_engaged or bounced:
           - Delete demo HTML from docs/demos/
           - Commit deletion to git
           - Mark as demo_deleted
           - Remove from GitHub Pages
         - If status = lead_engaged: KEEP (convert to project)
         - If status = bounced: KEEP (for post-mortem)
         - Status: lifecycle_complete
```

## Database Schema Addition

```sql
ALTER TABLE leads ADD COLUMN demo_created_at TEXT;
ALTER TABLE leads ADD COLUMN demo_expires_at TEXT;
ALTER TABLE leads ADD COLUMN follow_up_sent_at TEXT;
ALTER TABLE leads ADD COLUMN last_reply_checked_at TEXT;
ALTER TABLE leads ADD COLUMN demo_status TEXT DEFAULT 'pending';
-- pending → sent → follow_up_sent → checked → demo_deleted / lifecycle_complete
```

## Automation

### Day 5: Resend Follow-up
```bash
0 9 * * * cd ~/git/freshsites-outreach && python3 agents/lifecycle_resend.py
```

### Day 10: Check Replies
```bash
0 10 * * * cd ~/git/freshsites-outreach && python3 agents/lifecycle_check_replies.py
```

### Day 15: Auto-Delete
```bash
0 11 * * * cd ~/git/freshsites-outreach && python3 agents/lifecycle_cleanup.py
```

## Benefits

- No ever-expanding repo (demos auto-purge after 15 days)
- Forced follow-up (automatic resend Day 5)
- Reply tracking (auto-check Day 10)
- Engaged leads preserved (Day 15+ only if prospect replied)
- Clean audit trail (deleted demos logged, not lost)
