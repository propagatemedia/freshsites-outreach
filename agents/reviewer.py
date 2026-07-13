#!/usr/bin/env python3
"""
Demo Reviewer Agent — QA gate before outreach.
Checks live deployed demo for critical issues that kill conversions.
Usage: PYTHONPATH="" ./.venv/bin/python3.11 agents/reviewer.py <demo_url> <original_score>
Returns exit 0 on PASS, exit 1 on FAIL.
"""

import sys, re, requests
from urllib.parse import urljoin

def check_page_load(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        return True, r.text
    except Exception as e:
        return False, str(e)

def check_images(html, base_url):
    """Find all image src URLs, verify they return 200."""
    urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    broken = []
    for u in urls:
        full = urljoin(base_url, u)
        try:
            r = requests.head(full, timeout=10, allow_redirects=True)
            if r.status_code >= 400:
                broken.append((full, r.status_code))
        except Exception as e:
            broken.append((full, str(e)))
    return broken

def find_issues(html):
    """Check for critical missing elements in HTML."""
    issues = []
    checks = [
        ("<form", "No contact form found"),
        ("type=\"submit\"", "Form has no submit button"),
        ("name=\"name\"", "Form missing name field"),
        ("name=\"email\"", "Form missing email field"),
        ("tel:", "No phone link (tel:)"),
        ("hero", "No hero section"),
        ("object-fit:cover", "Hero image missing object-fit:cover"),
        ("Our Services", "No services section heading"),
        ("map-frame", "No Google Maps embed"),
        ("position:absolute;inset:0", "Hero may not fill section properly"),
    ]
    lower = html.lower()
    for pattern, msg in checks:
        if pattern.lower() not in lower:
            issues.append(msg)
    return issues

def check_phone_visible(html):
    """Ensure phone number in CTA section uses white text on dark bg."""
    # Look for the CTA phone link - if it has no explicit color or uses brand color, it's invisible
    phone_match = re.search(r'class="phone"[^>]*>([^<]+)</a>', html)
    if not phone_match:
        return True, None  # no phone class found, skip
    # Check CSS: if phone class has color same as background brand, warn
    phone_css = re.search(r'\.phone\{([^}]+)\}', html)
    if phone_css:
        styles = phone_css.group(1)
        if '#fff' not in styles.lower() and 'white' not in styles.lower():
            return False, f"Phone link color in CTA may be invisible. Styles: {styles[:60]}"
    return True, None

def check_meta(html, expected_name):
    """Verify title tag contains business name."""
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if not title_match:
        return False, "No <title> tag"
    title = title_match.group(1)
    if expected_name.split()[0] not in title:
        return False, f"Title mismatch: '{title}' does not contain '{expected_name.split()[0]}'"
    return True, None

def review_demo(url, original_score, expected_name=""):
    print(f"=== REVIEW: {url} ===\n")
    
    ok, html_or_err = check_page_load(url)
    if not ok:
        print(f"FAIL: Page did not load: {html_or_err}")
        return False
    html = html_or_err
    
    all_ok = True
    
    # 1. Images
    broken = check_images(html, url)
    if broken:
        print(f"[FAIL] Broken images ({len(broken)}):")
        for u, s in broken[:5]:
            print(f"  - {u} -> {s}")
        all_ok = False
    else:
        print("[PASS] All images load")
    
    # 2. Critical elements
    issues = find_issues(html)
    if issues:
        print(f"[FAIL] Missing critical elements:")
        for i in issues:
            print(f"  - {i}")
        all_ok = False
    else:
        print("[PASS] All critical elements present")
    
    # 3. Phone visibility
    ok, err = check_phone_visible(html)
    if not ok:
        print(f"[WARN] {err}")
    else:
        print("[PASS] Phone link styling OK")
    
    # 4. Title
    if expected_name:
        ok, err = check_meta(html, expected_name)
        if not ok:
            print(f"[FAIL] {err}")
            all_ok = False
        else:
            print("[PASS] Title tag correct")
    
    # 5. Score improvement (rough check: demo should be much better)
    # We can't auto-score the demo from HTML, so we rely on preflight score threshold
    print(f"[INFO] Original score: {original_score}/10")
    
    print()
    if all_ok:
        print("=== RESULT: PASS ===")
    else:
        print("=== RESULT: FAIL — fix issues before sending ===")
    print()
    return all_ok

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: reviewer.py <demo_url> [original_score] [business_name]")
        sys.exit(1)
    url = sys.argv[1]
    score = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    name = sys.argv[3] if len(sys.argv) > 3 else ""
    passed = review_demo(url, score, name)
    sys.exit(0 if passed else 1)
