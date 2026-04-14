#!/usr/bin/env python3
"""Eval: every MDX page must have title and description in frontmatter."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (
    collect_mdx_files, rel_path, parse_frontmatter,
    output_result, MIN_DESCRIPTION_LENGTH,
)


def check_file(path: Path) -> list[dict]:
    issues = []
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    rp = rel_path(path)

    if not fm.get("title"):
        issues.append({"file": rp, "field": "title", "message": "Missing title"})

    desc = fm.get("description", "")
    if not desc:
        issues.append({"file": rp, "field": "description", "message": "Missing description"})
    elif len(desc) < MIN_DESCRIPTION_LENGTH:
        issues.append({
            "file": rp,
            "field": "description",
            "message": f"Description too short ({len(desc)} chars, need {MIN_DESCRIPTION_LENGTH}+)",
        })

    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=95.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = collect_mdx_files()
    all_issues = []

    for f in files:
        all_issues.extend(check_file(f))

    total = len(files)
    failed_files = {i["file"] for i in all_issues}
    passed = total - len(failed_files)
    score = (passed / total * 100) if total > 0 else 100.0

    output_result("frontmatter-completeness", score, total, passed, all_issues, args.threshold)
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
