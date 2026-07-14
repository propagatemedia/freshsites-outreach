#!/usr/bin/env python3
"""
review_and_send.py — the outreach gate orchestrator.

Ties the vision review pipeline together for ONE lead:
  1. capture   : screenshot prospect site + demo (vision_capture.py)
  2. review    : [AGENT STEP] load both images, score vs references/vision-rubric.md,
                 write review/<slug>/verdict.json
  3. gate      : gate_check.py — refuses to send unless the demo is honestly better
  4. send      : emailer.generate_email + Himalaya (only if gate passes)

Because step 2 is genuine visual judgment (not keyword heuristics), it is performed by
the agent, not this script. Run modes:

  # Step 1 only — capture screenshots, then the agent reviews:
  PYTHONPATH="" ./.venv/bin/python3.11 agents/review_and_send.py <slug> --capture

  # Steps 3-4 — after verdict.json exists, gate then send (test or live):
  PYTHONPATH="" ./.venv/bin/python3.11 agents/review_and_send.py <slug> --send [--test]

--test sends to tyrone@propagate.media instead of the real lead email.
"""
import sys, os, json, subprocess, re, sqlite3
from pathlib import Path

REPO = Path(__file__).parent.parent
DB = REPO / "leads" / "freshsites.db"
PY = sys.executable


def get_lead(slug: str):
    """Find the lead row whose demo_url ends with <slug>.html. Returns dict or None."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE demo_url LIKE ?", (f"%{slug}.html",))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def capture(slug: str, lead: dict):
    prospect = lead["website"]
    demo = lead["demo_url"]
    print(f"Capturing screenshots for {slug}...")
    r = subprocess.run([PY, str(REPO / "agents" / "vision_capture.py"), slug, prospect, demo],
                       capture_output=True, text=True)
    print(r.stdout)
    cap = json.loads((REPO / "review" / slug / "capture.json").read_text())
    print("\n" + "=" * 60)
    print("AGENT REVIEW STEP REQUIRED:")
    print(f"  1. Load {cap.get('prospect_shot') or prospect}")
    print(f"  2. Load {cap.get('demo_shot') or demo}")
    print(f"  3. Score both against agents/references/vision-rubric.md")
    print(f"  4. Write review/{slug}/verdict.json")
    print(f"  5. Re-run with --send")
    print("=" * 60)


def gate(slug: str) -> bool:
    r = subprocess.run([PY, str(REPO / "agents" / "gate_check.py"), slug])
    return r.returncode == 0


def send(slug: str, lead: dict, test: bool):
    sys.path.insert(0, str(REPO / "agents"))
    from emailer import generate_email
    to = "tyrone@propagate.media" if test else lead.get("email")
    if not to:
        print(f"BLOCKED: no email address for {slug} and not in --test mode.")
        return False
    ld = dict(lead)
    ld["email"] = to
    email_raw, _ = generate_email(ld)
    subj_m = re.search(r"Subject:\s*(.+)", email_raw.split("\n\n")[0])
    subject = subj_m.group(1).strip() if subj_m else "Your website"
    body = email_raw.split("\n\n", 1)[1] if "\n\n" in email_raw else email_raw
    msg = (f"From: freshsites@sites.propagate.media\nTo: {to}\n"
           f"Subject: {subject}\nContent-Type: text/html; charset=utf-8\n\n{body}")
    r = subprocess.run(["himalaya", "message", "send", "--account", "freshsites"],
                       input=msg, capture_output=True, text=True, timeout=30)
    ok = r.returncode == 0
    print(f"{'SENT' if ok else 'FAIL'} ({'TEST' if test else 'LIVE'}) -> {to} : {subject}")
    if not ok:
        print(r.stderr[:200])
    return ok


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    slug = sys.argv[1]
    mode = sys.argv[2]
    test = "--test" in sys.argv

    lead = get_lead(slug)
    if not lead:
        print(f"No lead found with demo_url ending {slug}.html")
        sys.exit(1)

    if mode == "--capture":
        capture(slug, lead)
    elif mode == "--send":
        if not gate(slug):
            print("\nOutreach BLOCKED by review gate. Not sending.")
            sys.exit(1)
        print()
        send(slug, lead, test)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
