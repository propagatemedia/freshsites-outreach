#!/usr/bin/env python3
"""
Outreach Gate — reads a vision-review verdict and decides if a lead may be emailed.

The vision agent writes review/<slug>/verdict.json (see references/vision-rubric.md).
This gate enforces Tyrone's honesty rules mechanically so nothing gets emailed that
shouldn't:

  - captured_ok must be true      (we actually saw both pages)
  - send_ok must be true          (agent's honest call)
  - is_demo_better must be true
  - improvement must be >= +2.0    (demo is a real, visible step up)
  - prospect overall must be < 6.5 (we don't cold-email people with decent sites)

Exit 0 = CLEAR TO SEND. Exit 1 = BLOCKED (prints why).

Usage:
  PYTHONPATH="" ./.venv/bin/python3.11 agents/gate_check.py <slug>
"""
import sys, json
from pathlib import Path

REPO = Path(__file__).parent.parent
MIN_IMPROVEMENT = 2.0
MAX_PROSPECT_SCORE = 6.5


def check(slug: str) -> bool:
    vpath = REPO / "review" / slug / "verdict.json"
    if not vpath.exists():
        print(f"BLOCKED: no verdict.json for {slug} — run the vision review first.")
        return False

    v = json.loads(vpath.read_text())
    reasons = []

    if not v.get("captured_ok", False):
        reasons.append("screenshots did not capture cleanly — page unseen")
    if not v.get("send_ok", False):
        reasons.append("agent set send_ok=false (honest call: skip)")
    if not v.get("is_demo_better", False):
        reasons.append("demo not judged better than prospect site")

    improvement = v.get("improvement", 0)
    if improvement < MIN_IMPROVEMENT:
        reasons.append(f"improvement {improvement:+.1f} < required +{MIN_IMPROVEMENT}")

    prospect_overall = v.get("prospect", {}).get("overall", 0)
    if prospect_overall >= MAX_PROSPECT_SCORE:
        reasons.append(f"prospect site scores {prospect_overall}/10 (>= {MAX_PROSPECT_SCORE}) — too good to credibly pitch")

    print(f"=== GATE: {slug} ===")
    print(f"  prospect overall: {prospect_overall}/10")
    print(f"  demo overall:     {v.get('demo', {}).get('overall', '?')}/10")
    print(f"  improvement:      {improvement:+.1f}")
    print(f"  honest call:      {v.get('honest_call', '(none)')}")
    print()

    if reasons:
        print("RESULT: BLOCKED")
        for r in reasons:
            print(f"  - {r}")
        return False
    print("RESULT: CLEAR TO SEND")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: gate_check.py <slug>")
        sys.exit(1)
    sys.exit(0 if check(sys.argv[1]) else 1)
