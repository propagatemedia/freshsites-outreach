#!/usr/bin/env python3
"""
Gate 1 v2: narrow-check aggregation with tie-breaker.

4 subagents each score ONE dimension pair on a discrete scale:
  1  = hard fail (dead/parked, national brand, wrong trade)
  3  = not great (dated, some redeeming features)
  6  = not bad (competent, mostly fine)
  10 = perfect (modern, professional - NOT a rebuild candidate)

Aggregation:
  avg <= 3.5              -> SURVIVES to human screenshot review
  avg >= 7.0               -> AUTO-REJECT, dropped, never reaches human
  3.5 < avg < 7.0          -> AMBIGUOUS, needs tie-breaker
  any two scores differ    -> AMBIGUOUS, needs tie-breaker
    by more than 5 points

This script only does the aggregation math + DB logging. The actual agent
dispatch (delegate_task calls) happens in the orchestrator turn, not here -
this is the deterministic decision layer that sits between "agents responded"
and "what do we do with that".
"""
import sqlite3
import statistics
from datetime import datetime

DB = '/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db'

DIMENSION_LABELS = [
    'dead_site_or_national_brand',   # 1 = dead/parked/national brand, 10 = live+genuinely small
    'mobile_and_photography',         # 1 = broken/no real photos, 10 = responsive+real photography
    'layout_and_cta',                 # 1 = no design/broken CTA, 10 = modern layout+working CTA
    'real_business_and_trade_match',  # 1 = directory page/wrong trade, 10 = real matching business
]


def aggregate_scores(lead_id: int, scores: list, reasonings: list) -> dict:
    """scores: list of 4 ints (1/3/6/10). reasonings: list of 4 strings."""
    if len(scores) != 4:
        raise ValueError(f"Expected exactly 4 scores, got {len(scores)}")

    avg = statistics.mean(scores)
    max_spread = max(scores) - min(scores)

    ambiguous = (3.5 < avg < 7.0) or (max_spread > 5)

    if ambiguous:
        decision = 'NEEDS_TIEBREAKER'
    elif avg <= 3.5:
        decision = 'SURVIVES_TO_HUMAN'
    else:
        decision = 'AUTO_REJECT'

    return {
        'lead_id': lead_id,
        'scores': scores,
        'avg': round(avg, 2),
        'max_spread': max_spread,
        'decision': decision,
        'reasonings': reasonings,
    }


def record_gate1_v2(lead_id: int, result: dict, tiebreaker_verdict: str = None, tiebreaker_reasoning: str = None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().isoformat()

    for i, (dim, score, reasoning) in enumerate(zip(DIMENSION_LABELS, result['scores'], result['reasonings'])):
        c.execute(
            "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (lead_id, 'gate1_narrow_check', f'agent_{dim}', str(score), reasoning, now)
        )

    notes = f"avg={result['avg']}, spread={result['max_spread']}, decision={result['decision']}"
    if tiebreaker_verdict:
        notes += f" | TIEBREAKER: {tiebreaker_verdict} - {tiebreaker_reasoning}"
        final_decision = tiebreaker_verdict
    else:
        final_decision = result['decision']

    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate1_final', 'orchestrator', final_decision, notes, now)
    )

    stage_map = {
        'SURVIVES_TO_HUMAN': 'gate1_pending_human_screenshot',
        'AUTO_REJECT': 'gate1_reject_auto',
        'PASS': 'gate1_pending_human_screenshot',
        'REJECT': 'gate1_reject_tiebreaker',
    }
    stage = stage_map.get(final_decision, 'gate1_reject_auto')

    c.execute("UPDATE leads SET pipeline_stage = ?, updated_at = ? WHERE id = ?", (stage, now, lead_id))
    conn.commit()
    conn.close()
    return stage


if __name__ == '__main__':
    # self-test
    test = aggregate_scores(999, [1, 3, 1, 6], ["dead", "dated", "no cta", "ok match"])
    print(test)
    assert test['decision'] == 'SURVIVES_TO_HUMAN'

    test2 = aggregate_scores(999, [10, 6, 10, 6], ["modern", "ok", "great cta", "ok"])
    print(test2)
    assert test2['decision'] == 'AUTO_REJECT'

    test3 = aggregate_scores(999, [10, 1, 10, 1], ["great", "bad", "great", "bad"])
    print(test3)
    assert test3['decision'] == 'NEEDS_TIEBREAKER'

    print("\n✓ All self-tests passed")
