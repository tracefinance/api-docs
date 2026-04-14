#!/usr/bin/env python3
"""Eval: description field must be present, non-placeholder, and meaningful."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (
    collect_mdx_files, rel_path, parse_frontmatter,
    is_placeholder, output_result, MIN_DESCRIPTION_LENGTH,
)


def check_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    rp = rel_path(path)

    desc = fm.get("description", "")
    if not desc:
        return {"file": rp, "message": "Missing description"}
    if len(desc) < MIN_DESCRIPTION_LENGTH:
        return {"file": rp, "message": f"Description too short ({len(desc)} chars)"}
    if is_placeholder(desc):
        return {"file": rp, "message": f"Placeholder description: '{desc}'"}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=95.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = collect_mdx_files()
    issues = [i for i in (check_file(f) for f in files) if i]

    total = len(files)
    passed = total - len(issues)
    score = (passed / total * 100) if total > 0 else 100.0

    output_result("description-quality", score, total, passed, issues, args.threshold)
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
