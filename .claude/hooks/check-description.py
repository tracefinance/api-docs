#!/usr/bin/env python3
"""Hook: real-time description quality check on MDX writes."""

import json
import re
import sys

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PLACEHOLDER_PATTERNS = ["todo", "tbd", "placeholder", "fill in", "description here", "{{", "..."]
MIN_DESC_LEN = 20

# Words that indicate marketing language
MARKETING_WORDS = [
    "powerful", "seamless", "robust", "cutting-edge", "world-class",
    "best-in-class", "enterprise-grade", "next-generation", "revolutionary",
]


def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".mdx"):
        sys.exit(0)

    if "/snippets/" in file_path or "/.claude/" in file_path:
        sys.exit(0)

    content = tool_input.get("content", "")
    if not content:
        try:
            with open(file_path) as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            sys.exit(0)

    m = FRONTMATTER_RE.match(content)
    if not m:
        sys.exit(0)

    # Extract description
    desc = ""
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("description:"):
            desc = line.partition(":")[2].strip().strip('"').strip("'")
            break

    if not desc:
        # frontmatter hook already catches missing descriptions
        sys.exit(0)

    warnings = []

    # Check for marketing language in description
    desc_lower = desc.lower()
    for word in MARKETING_WORDS:
        if word in desc_lower:
            warnings.append(f"Marketing language in description: '{word}'")

    if warnings:
        print("DESCRIPTION QUALITY WARNING:", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)
        # Non-blocking
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
