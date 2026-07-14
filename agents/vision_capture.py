#!/usr/bin/env python3
"""
Vision Review Harness — capture screenshots for the FreshSites review agent.

This does NOT judge on its own (no keyword heuristics — that was the old, weak
reviewer.py). It captures full-page screenshots of the PROSPECT's live site and
YOUR demo, side by side, so a vision-capable agent can score them against
references/vision-rubric.md and produce a structured verdict.

Flow:
  1. This script screenshots both URLs (headless Chromium via Playwright browsers
     already cached by Hermes) into review/<slug>/.
  2. The agent loads both images, applies the rubric, writes review/<slug>/verdict.json.
  3. gate_check.py reads verdict.json and blocks/passes outreach.

Usage:
  PYTHONPATH="" ./.venv/bin/python3.11 agents/vision_capture.py <slug> <prospect_url> <demo_url>

If Playwright isn't importable, falls back to printing the two URLs so the agent
can screenshot them with its own browser tool instead.
"""
import sys, os, json, subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent
REVIEW_DIR = REPO / "review"


def find_chromium():
    """Locate a cached Playwright/Chromium headless shell."""
    cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    if not cache.exists():
        cache = Path.home() / ".cache" / "ms-playwright"
    if not cache.exists():
        return None
    # prefer headless shell; cover mac arm64/x64 + linux layouts
    patterns = [
        "chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
        "chromium-*/chrome-*/Chromium.app/Contents/MacOS/Chromium",
        "chromium-*/chrome-*/chrome",
        "chromium_headless_shell-*/*/headless_shell",
    ]
    for pat in patterns:
        hits = list(cache.glob(pat))
        if hits:
            return str(hits[0])
    return None


def screenshot(url, out_path, chromium):
    """Full-page screenshot via headless chromium CLI (no python playwright needed)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        chromium, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--window-size=1440,2400",
        f"--screenshot={out_path}", url,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return out_path.exists()
    except Exception as e:
        print(f"screenshot error: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 4:
        print("Usage: vision_capture.py <slug> <prospect_url> <demo_url>")
        sys.exit(1)
    slug, prospect_url, demo_url = sys.argv[1], sys.argv[2], sys.argv[3]
    out_dir = REVIEW_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    chromium = find_chromium()
    result = {"slug": slug, "prospect_url": prospect_url, "demo_url": demo_url,
              "prospect_shot": None, "demo_shot": None, "method": None}

    if chromium:
        p_shot = out_dir / "prospect.png"
        d_shot = out_dir / "demo.png"
        ok_p = screenshot(prospect_url, p_shot, chromium)
        ok_d = screenshot(demo_url, d_shot, chromium)
        result["method"] = "chromium-cli"
        result["prospect_shot"] = str(p_shot) if ok_p else None
        result["demo_shot"] = str(d_shot) if ok_d else None
    else:
        result["method"] = "agent-browser-fallback"
        result["note"] = "No cached chromium. Agent must screenshot both URLs with its browser tool."

    (out_dir / "capture.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
