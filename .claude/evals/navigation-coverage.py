#!/usr/bin/env python3
"""Eval: every page in docs.json must have a corresponding .mdx file.

Reverse of orphan-detector: catches stale navigation entries pointing
to files that don't exist (yet or anymore).
Skips OpenAPI operation references (e.g., 'GET /api/accounts/{id}').
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (
    REPO_ROOT, load_docs_json, extract_nav_pages, output_result,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=90.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    docs = load_docs_json()
    nav_pages = extract_nav_pages(docs)
    issues = []

    for page in sorted(nav_pages):
        mdx_path = REPO_ROOT / f"{page}.mdx"
        if not mdx_path.exists():
            issues.append({
                "page": page,
                "message": f"docs.json references '{page}' but {page}.mdx does not exist",
            })

    total = len(nav_pages)
    passed = total - len(issues)
    score = (passed / total * 100) if total > 0 else 100.0

    output_result("navigation-coverage", score, total, passed, issues, args.threshold)
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
