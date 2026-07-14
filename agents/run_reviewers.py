#!/usr/bin/env python3
"""
Run the multi-reviewer gate on a site.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reviewers.content_reviewer import review_content
from reviewers.visual_reviewer import review_visual


def run_reviewers(slug: str):
    cache_path = Path(__file__).parent.parent / "extracted" / f"{slug}.json"
    if not cache_path.exists():
        print(f"No cache found for {slug}")
        return False

    data = json.loads(cache_path.read_text())

    # For now we use what we have in the cache
    content_result = review_content(data)
    visual_result = review_visual(data, expected_brand=data.get("brand_color", ""))

    print(f"\n=== Multi-Reviewer Results for {data.get('name')} ===")
    print(f"Content Reviewer: {content_result['score']}/10 - {'PASS' if content_result['pass'] else 'FAIL'}")
    for f in content_result['findings']:
        print(f"  + {f}")
    for g in content_result['gaps']:
        print(f"  - {g}")

    print(f"\nVisual Reviewer:  {visual_result['score']}/10 - {'PASS' if visual_result['pass'] else 'FAIL'}")
    for f in visual_result['findings']:
        print(f"  + {f}")
    for g in visual_result['gaps']:
        print(f"  - {g}")

    overall_pass = content_result['pass'] and visual_result['pass']
    print(f"\n=== OVERALL: {'PASS - ready for generation' if overall_pass else 'FAIL - needs work'} ===")

    return overall_pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_reviewers.py <slug>")
        sys.exit(1)
    run_reviewers(sys.argv[1])
