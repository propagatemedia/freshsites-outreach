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
    r'\b\d{2,3}\+?\s*years?\s+(of\s+)?experience\b',  # only flags 20+ handled below
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
    Returns {'reject': bool, 'reasons': [...]}
    extracted_text: raw scraped about/homepage text
    review_count: from Google Business profile if available
    """
    reasons = []
    text = extracted_text or ""

    for pattern in REJECT_PATTERNS:
        if re.search(pattern, text, re.I):
            reasons.append(f"matched pattern: {pattern}")

    years_match = LARGE_YEARS.search(text)
    if years_match and int(years_match.group(1)) >= 20:
        reasons.append(f"{years_match.group(1)}+ years trading (established)")

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
    }


if __name__ == '__main__':
    # quick self-test
    sample = "Pimlico Plumbers has been trading since 1979 with 230+ vans nationwide."
    result = check_brand_size(sample)
    print(result)
    assert result['reject'] is True
    print("✓ Self-test passed")
