#!/usr/bin/env python3
"""
Brand-size pre-filter. Runs BEFORE Gate 1.
Hard-rejects large/established brands so they never reach QA agents.
Cheap regex/heuristic pass — no API calls.
"""

import re

REJECT_PATTERNS = [
    r'\bsince\s+19\d{2}\b',              # "since 1979" - long-established
    r'\b(200|300|400|500)\+?\s*(vans|engineers|tradespeople|staff)\b',
    r'£\d{1,3}(\.\d+)?m(illion)?\s+(revenue|turnover)',
    r'\bnational(ly)?\s+(recognised|known|trusted)\b',
    r'\bfranchise\b',
    r'\b(nationwide|24/7\s+nationwide)\b',
]

MULTI_LOCATION_HINT = re.compile(r'\b(branches?|locations?|depots?)\s+(across|in|throughout)\b', re.I)
LARGE_YEARS = re.compile(r'\b(\d{2,3})\+?\s*years?\b', re.I)
REVIEW_COUNT = re.compile(r'\b(\d{3,})\s*(reviews|ratings)\b', re.I)


def check_brand_size(extracted_text: str, review_count: int = 0) -> dict:
    """
    Returns {'reject': bool, 'reasons': [...], 'flag_for_gate1': bool}
    extracted_text: raw scraped about/homepage text
    review_count: from Google Business profile if available

    'reject' = auto-reject, never reaches Gate 1 (strong/multiple signals only)
    'flag_for_gate1' = weak single signal, pass through as a note but let
                       the human-equivalent Gate 1 agents make the call
    """
    reasons = []
    weak_reasons = []
    text = extracted_text or ""

    for pattern in REJECT_PATTERNS:
        if re.search(pattern, text, re.I):
            reasons.append(f"matched pattern: {pattern}")

    # Years alone is NOT a reject signal (sole traders say "28 years experience"
    # all the time). A single scale-word match (nav link "Meet the Team") is also
    # weak on its own. Only hard-reject on years+scale IF there are 2+ distinct
    # scale words found (reduces one-off false positives like nav menu items).
    years_match = LARGE_YEARS.search(text)
    scale_words_found = set(w.lower() for w in re.findall(r'\b(team|staff|vans?|engineers|branches?|depots?|nationwide)\b', text, re.I))
    if years_match and int(years_match.group(1)) >= 20:
        if len(scale_words_found) >= 3:
            reasons.append(f"{years_match.group(1)}+ years trading AND 3+ distinct scale signals {scale_words_found} (established brand)")
        elif len(scale_words_found) >= 1:
            weak_reasons.append(f"{years_match.group(1)}+ years trading + weak signal(s) {scale_words_found} (verify in Gate 1, could be nav-link false positive)")

    if MULTI_LOCATION_HINT.search(text):
        reasons.append("multi-location/branch language detected")

    review_match = REVIEW_COUNT.search(text)
    if review_match and int(review_match.group(1)) >= 200:
        reasons.append(f"{review_match.group(1)}+ reviews (high volume brand)")

    if review_count and review_count >= 200:
        reasons.append(f"Google review count {review_count} >= 200")

    return {
        'reject': len(reasons) > 0,
        'reasons': reasons,
        'flag_for_gate1': len(weak_reasons) > 0,
        'weak_reasons': weak_reasons,
    }


if __name__ == '__main__':
    # quick self-test
    sample = "Pimlico Plumbers has been trading since 1979 with 230+ vans nationwide."
    result = check_brand_size(sample)
    print(result)
    assert result['reject'] is True
    print("✓ Self-test passed")
