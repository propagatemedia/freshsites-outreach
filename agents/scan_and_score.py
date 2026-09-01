#!/usr/bin/env python3
"""Compatibility wrapper for the current scoring engine.

Old docs referenced agents/scan_and_score.py. Keep that entrypoint working and
route it through score_site.py so there is one scoring implementation.
"""
from score_site import main

if __name__ == "__main__":
    raise SystemExit(main())
