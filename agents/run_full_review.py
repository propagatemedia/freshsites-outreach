#!/usr/bin/env python3
"""
Full Multi-Reviewer Orchestrator
Runs all four specialized reviewers and gives final go/no-go.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reviewers.content_reviewer import review_content
from reviewers.visual_reviewer import review_visual
from reviewers.conversion_reviewer import review_conversion
from reviewers.brand_reviewer import review_brand


def run_full_review(slug: str):
    cache_path = Path(__file__).parent.parent / "extracted" / f"{slug}.json"
    if not cache_path.exists():
        print(f"No cache for {slug}")
        return False

    data = json.loads(cache_path.read_text())
    name = data.get("name", slug)
    brand = data.get("brand_color", "")

    print(f"\n{'='*60}")
    print(f"FULL MULTI-REVIEWER GATE — {name}")
    print(f"{'='*60}")

    c = review_content(data)
    v = review_visual(data, expected_brand=brand)
    conv = review_conversion(data)
    b = review_brand(data, expected_brand=brand)

    results = [
        ("Content", c),
        ("Visual", v),
        ("Conversion", conv),
        ("Brand", b)
    ]

    all_pass = True
    for label, r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"\n{label:12} {r['score']:>4.1f}/10   [{status}]")
        for f in r["findings"][:2]:
            print(f"  + {f}")
        for g in r["gaps"][:2]:
            print(f"  - {g}")
        if not r["pass"]:
            all_pass = False

    print(f"\n{'='*60}")
    if all_pass:
        print("OVERALL: PASS — Site approved for high-quality demo generation")
    else:
        print("OVERALL: FAIL — Do not generate until gaps are addressed")
    print(f"{'='*60}\n")

    return all_pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_full_review.py <slug>")
        sys.exit(1)
    run_full_review(sys.argv[1])
