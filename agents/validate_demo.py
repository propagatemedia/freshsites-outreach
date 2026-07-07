#!/usr/bin/env python3
"""
Demo Quality Validation
Scores a built demo page and compares against the original website.
Only approves outreach if the demo is objectively better.

Usage:
    PYTHONPATH="" ./.venv/bin/python3.11 agents/validate_demo.py <demo_file> <original_score>
"""

import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup


def score_demo(html_path: Path) -> tuple[float, list[str]]:
    """Score a demo HTML file. Returns (score/10, gaps)."""
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    score = 10.0
    gaps = []

    # Check 1: Hero section with h1
    hero = soup.find("section", class_="hero") or soup.find("div", class_="hero")
    h1 = soup.find("h1")
    if not h1 or not h1.get_text(strip=True):
        score -= 2.0
        gaps.append("missing_h1")
    elif len(h1.get_text(strip=True)) < 10:
        score -= 1.0
        gaps.append("weak_h1")

    # Check 2: Trust bar / social proof
    trust = soup.find("div", class_="trust") or soup.find("section", id="reviews")
    if not trust:
        score -= 1.5
        gaps.append("missing_trust")

    # Check 3: Services section
    services = soup.find("section", id="services") or soup.find("div", class_="cards")
    if not services:
        score -= 1.5
        gaps.append("missing_services")

    # Check 4: Phone number visible
    body_text = soup.get_text()
    phone_patterns = [r"01\d{3}\s?\d{6}", r"01\d{4}\s?\d{5,6}"]
    has_phone = any(re.search(p, body_text) for p in phone_patterns)
    if not has_phone:
        score -= 2.0
        gaps.append("phone_hidden")

    # Check 5: CTA buttons
    ctas = soup.find_all("a", class_=re.compile("btn|cta"))
    if len(ctas) < 2:
        score -= 1.0
        gaps.append("weak_cta")

    # Check 6: Contact section
    contact = soup.find("section", id="contact") or soup.find("section", id="contact-form")
    if not contact:
        score -= 1.0
        gaps.append("missing_contact")

    # Check 7: Email present
    has_email = bool(soup.find("a", href=re.compile(r"mailto:")))
    if not has_email:
        score -= 0.5
        gaps.append("missing_email")

    # Check 8: Address present
    if "SY" not in body_text and "LD" not in body_text:
        score -= 0.5
        gaps.append("missing_address")

    # Check 9: Unsplash images loaded (visual quality)
    imgs = soup.find_all("img")
    unsplash_imgs = [i for i in imgs if "unsplash" in (i.get("src", ""))]
    broken_local = [i for i in imgs if not i.get("src", "").startswith("http")]
    if len(unsplash_imgs) < 3:
        score -= 1.0
        gaps.append("low_image_count")
    if broken_local:
        score -= 1.0
        gaps.append("broken_local_images")

    return max(0, round(score, 1)), gaps


def compare_demo(original_score: float, demo_score: float) -> dict:
    """Compare original vs demo. Returns decision."""
    improvement = demo_score - original_score

    if demo_score < 6.0:
        return {
            "approved": False,
            "reason": f"Demo scores {demo_score}/10 - below quality threshold (6.0)",
            "improvement": improvement,
        }

    if improvement < 1.0:
        return {
            "approved": False,
            "reason": f"Demo only {improvement:+.1f} points better - need at least +1.0 improvement",
            "improvement": improvement,
        }

    return {
        "approved": True,
        "reason": f"Demo is {improvement:+.1f} points better ({original_score} -> {demo_score})",
        "improvement": improvement,
    }


def validate_lead(lead_name: str, demo_path: Path, original_score: float):
    """Run full validation on a lead."""
    print(f"\n{'='*60}")
    print(f"VALIDATING: {lead_name}")
    print(f"{'='*60}")
    print(f"  Original score: {original_score}/10")
    print(f"  Demo file: {demo_path}")

    if not demo_path.exists():
        print(f"  ERROR: Demo file not found")
        return {"approved": False, "reason": "Demo file missing"}

    demo_score, gaps = score_demo(demo_path)
    print(f"  Demo score: {demo_score}/10")
    if gaps:
        print(f"  Gaps found: {', '.join(gaps)}")
    else:
        print(f"  No gaps found")

    result = compare_demo(original_score, demo_score)
    print(f"  Decision: {'APPROVED' if result['approved'] else 'REJECTED'}")
    print(f"  Reason: {result['reason']}")

    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: validate_demo.py <demo_file.html> <original_score>")
        sys.exit(1)

    demo_path = Path(sys.argv[1])
    original_score = float(sys.argv[2])
    lead_name = demo_path.stem.replace("-", " ").title()

    result = validate_lead(lead_name, demo_path, original_score)
    sys.exit(0 if result["approved"] else 1)


if __name__ == "__main__":
    main()
