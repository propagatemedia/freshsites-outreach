#!/usr/bin/env python3
"""
Image Pre-Flight Checker
Validates all external image URLs in demo pages before deployment.

Usage:
    PYTHONPATH="" ./.venv/bin/python3.11 agents/check_images.py demos/*.html
"""

import re
import sys
import requests
from pathlib import Path


def check_images_in_file(html_path: str) -> bool:
    html = Path(html_path).read_text(encoding="utf-8")
    urls = re.findall(r'src="(https?://[^"]+\.(?:jpg|jpeg|png|webp|gif))[^"]*"', html)
    urls += re.findall(r'src="(https://images\.unsplash\.com/[^"]+)"', html)
    
    print(f"\n📄 {Path(html_path).name}")
    all_ok = True
    for url in urls:
        try:
            r = requests.head(url, timeout=15, allow_redirects=True)
            ok = r.status_code == 200
            all_ok = all_ok and ok
            icon = "✅" if ok else f"❌ HTTP {r.status_code}"
            print(f"  {icon} {url[:70]}")
        except Exception as e:
            all_ok = False
            print(f"  ❌ ERROR: {url[:70]} - {str(e)[:50]}")
    return all_ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_images.py <html_file> [html_file2 ...]")
        sys.exit(1)

    overall = True
    for path in sys.argv[1:]:
        if Path(path).suffix == ".html":
            ok = check_images_in_file(path)
            overall = overall and ok

    print(f"\n{'='*60}")
    print(f"OVERALL: {'ALL IMAGES OK' if overall else 'SOME IMAGES BROKEN — FIX BEFORE DEPLOY'}")
    print(f"{'='*60}")
    sys.exit(0 if overall else 1)
