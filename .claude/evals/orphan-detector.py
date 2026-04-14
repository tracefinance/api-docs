#!/usr/bin/env python3
"""Eval: every .mdx file must appear in docs.json navigation."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (
    collect_mdx_files, rel_path, load_docs_json,
    extract_nav_pages, output_result,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=90.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    docs = load_docs_json()
    nav_pages = extract_nav_pages(docs)
    files = collect_mdx_files()
    issues = []

    for f in files:
        rp = rel_path(f)
        # docs.json references pages without .mdx extension
        page_path = rp.removesuffix(".mdx")
        if page_path not in nav_pages:
            issues.append({
                "file": rp,
                "message": f"Not in docs.json navigation — orphan page",
            })

    total = len(files)
    passed = total - len(issues)
    score = (passed / total * 100) if total > 0 else 100.0

    output_result("orphan-detector", score, total, passed, issues, args.threshold)
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
