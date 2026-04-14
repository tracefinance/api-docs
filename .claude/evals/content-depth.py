#!/usr/bin/env python3
"""Eval: detect stub pages vs. substantive content.

Scoring:
  - Substantive (200+ words of real prose): PASS
  - Thin (30-199 words): WARN (counted as pass)
  - Stub (<30 words or TODO-only): FAIL
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (
    collect_mdx_files, rel_path, extract_body, word_count,
    has_todo_only, output_result, SUBSTANTIVE_WORD_COUNT, THIN_WORD_COUNT,
)


def check_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    rp = rel_path(path)
    body = extract_body(text)
    wc = word_count(body)

    if has_todo_only(text) or wc < THIN_WORD_COUNT:
        return {
            "file": rp,
            "words": wc,
            "category": "stub",
            "message": f"Stub page ({wc} words) — needs content",
        }
    return None  # thin and substantive both pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=50.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = collect_mdx_files()
    issues = []

    for f in files:
        issue = check_file(f)
        if issue:
            issues.append(issue)

    total = len(files)
    passed = total - len(issues)
    score = (passed / total * 100) if total > 0 else 100.0

    output_result("content-depth", score, total, passed, issues, args.threshold)
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
