#!/usr/bin/env python3
"""Hook: real-time description quality check on MDX writes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
from _lib import load_hook_input, parse_frontmatter

MARKETING_WORDS = [
    "powerful", "seamless", "robust", "cutting-edge", "world-class",
    "best-in-class", "enterprise-grade", "next-generation", "revolutionary",
]


def main():
    result = load_hook_input()
    if result is None:
        sys.exit(0)

    _, content = result
    fm = parse_frontmatter(content)
    desc = fm.get("description", "")

    if not desc:
        sys.exit(0)

    warnings = []
    desc_lower = desc.lower()
    for word in MARKETING_WORDS:
        if word in desc_lower:
            warnings.append(f"Marketing language in description: '{word}'")

    if warnings:
        print("DESCRIPTION QUALITY WARNING:", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
