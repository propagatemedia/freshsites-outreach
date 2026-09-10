#!/usr/bin/env python3
"""
Gate 1 v3: free-tier-only triage with majority vote + citation forcing.

Goal: find genuine rebuild candidates at ~$0 cost. Nothing escalates to the
paid main model until it has survived a 3-agent majority vote on the free
delegation model.

Design fixes vs earlier versions (both failed on 2026-09-10):
  v1 (broad PASS/REJECT opinion): defaulted to "small business = needs rebuild"
     regardless of actual site quality. 8/10 false positive rate.
  v2 (narrow 4-dimension scoring): agents sometimes hallucinated page content
     entirely while still returning confident scores (e.g. described a roofing
     site as showing "plumbing logos", claimed a loaded page was "blank").

v3 fixes:
  1. 3 agents per lead (not 2) - majority vote absorbs one hallucinating outlier
     instead of averaging it in or needing a tie-breaker every time.
  2. CITATION FORCING: each agent must quote a specific concrete detail from
     the page (an exact phrase, color, button label, or piece of contact info)
     as evidence for its verdict. An agent that can't produce a real citation
     is more likely hallucinating - citation-free responses get down-weighted
     or discarded before the vote, not trusted equally.
  3. Escalation to the human/paid layer is BATCHED and MINIMAL: only leads
     that get a 2-of-3 or 3-of-3 "genuinely bad" vote proceed to a human
     screenshot spot-check. Rejected leads never cost paid attention.

This script is the deterministic vote-counting layer. Agent dispatch
(delegate_task calls) happens in the orchestrator turn - this just tallies
what came back and decides escalate vs drop.
"""
import sqlite3
from datetime import datetime

DB = '/Users/tyronemacmini/git/freshsites-outreach/leads/freshsites.db'


def has_real_citation(citation: str) -> bool:
    """Reject empty, generic, or suspiciously vague citations.
    A real citation names something SPECIFIC that could only come from
    actually seeing the page: an exact phrase, a number, a color, a button
    label. Generic statements ('the layout looks old', 'it has content')
    without a concrete quoted detail are treated as unverified.
    """
    if not citation or len(citation.strip()) < 8:
        return False
    generic_phrases = [
        'looks old', 'looks dated', 'looks modern', 'looks good', 'looks bad',
        'has content', 'no content', 'seems fine', 'seems broken',
    ]
    stripped = citation.lower().strip()
    # if the ENTIRE citation is just a generic phrase with nothing concrete added, reject
    if any(stripped == g or stripped == g + '.' for g in generic_phrases):
        return False
    return True


def tally_votes(lead_id: int, agent_results: list) -> dict:
    """agent_results: list of 3 dicts, each {'verdict': 'PASS'|'REJECT', 'citation': str}

    Returns aggregated decision. Citation-free votes are flagged but still
    counted (down-weighted in reporting, not silently dropped) - if 2+ agents
    fail to cite anything concrete, the whole result is untrustworthy and
    escalates to human review by default rather than auto-rejecting (a
    human should decide when the free-tier signal itself is unreliable,
    not have it silently discarded).
    """
    if len(agent_results) != 3:
        raise ValueError(f"Expected exactly 3 agent results, got {len(agent_results)}")

    verdicts = [r['verdict'] for r in agent_results]
    citations = [r.get('citation', '') for r in agent_results]
    valid_citations = [has_real_citation(c) for c in citations]

    pass_count = verdicts.count('PASS')
    reject_count = verdicts.count('REJECT')
    uncited_count = valid_citations.count(False)

    if uncited_count >= 2:
        decision = 'ESCALATE_LOW_CONFIDENCE'
        reason = f'{uncited_count}/3 agents gave no concrete citation - signal unreliable, needs human review'
    elif pass_count >= 2:
        decision = 'ESCALATE_TO_HUMAN'
        reason = f'{pass_count}/3 agents voted PASS (genuinely needs rebuild) with citations'
    else:
        decision = 'AUTO_REJECT'
        reason = f'{reject_count}/3 agents voted REJECT (site is fine)'

    return {
        'lead_id': lead_id,
        'verdicts': verdicts,
        'citations': citations,
        'valid_citations': valid_citations,
        'pass_count': pass_count,
        'reject_count': reject_count,
        'uncited_count': uncited_count,
        'decision': decision,
        'reason': reason,
    }


def record_result(lead_id: int, result: dict, human_final_verdict: str = None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().isoformat()

    for i, (verdict, citation, valid) in enumerate(zip(result['verdicts'], result['citations'], result['valid_citations'])):
        note = f"citation={citation!r} valid={valid}"
        c.execute(
            "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (lead_id, 'gate1_v3_vote', f'agent_{i+1}', verdict, note, now)
        )

    final = human_final_verdict if human_final_verdict else result['decision']
    c.execute(
        "INSERT INTO gate_log (lead_id, gate_name, agent, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, 'gate1_final', 'orchestrator', final, result['reason'], now)
    )

    stage_map = {
        'ESCALATE_TO_HUMAN': 'gate1_pending_human_screenshot',
        'ESCALATE_LOW_CONFIDENCE': 'gate1_pending_human_screenshot',
        'AUTO_REJECT': 'gate1_reject_auto',
        'PASS': 'gate1_pass',
        'REJECT': 'gate1_reject',
    }
    stage = stage_map.get(final, 'gate1_reject_auto')
    c.execute("UPDATE leads SET pipeline_stage = ?, updated_at = ? WHERE id = ?", (stage, now, lead_id))
    conn.commit()
    conn.close()
    return stage


if __name__ == '__main__':
    # self-tests
    t1 = tally_votes(1, [
        {'verdict': 'REJECT', 'citation': 'hero shows "NICEIC Approved" badge and modern nav with dropdown menu'},
        {'verdict': 'REJECT', 'citation': 'site uses custom logo and real photography of a van'},
        {'verdict': 'REJECT', 'citation': 'clean typography, working "Get a Quote" button in orange'},
    ])
    print("Unanimous REJECT (good site):", t1)
    assert t1['decision'] == 'AUTO_REJECT'

    t2 = tally_votes(2, [
        {'verdict': 'PASS', 'citation': 'page uses Times New Roman headings and a bright blue table layout, no viewport meta'},
        {'verdict': 'PASS', 'citation': 'buttons are glossy 3D icons typical of 2005-era web design'},
        {'verdict': 'REJECT', 'citation': 'has a phone number and email visible'},
    ])
    print("2/3 PASS with citations:", t2)
    assert t2['decision'] == 'ESCALATE_TO_HUMAN'

    t3 = tally_votes(3, [
        {'verdict': 'PASS', 'citation': 'looks bad'},
        {'verdict': 'REJECT', 'citation': ''},
        {'verdict': 'PASS', 'citation': 'seems broken'},
    ])
    print("Low-confidence (no real citations):", t3)
    assert t3['decision'] == 'ESCALATE_LOW_CONFIDENCE'

    print("\n✓ All self-tests passed")
