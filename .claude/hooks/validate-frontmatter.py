#!/usr/bin/env python3
"""Hook: validate frontmatter on MDX files after write/edit.

Blocks saves with missing title or description.
"""

import json
import re
import sys

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MIN_DESC_LEN = 20
PLACEHOLDER_PATTERNS = ["todo", "tbd", "placeholder", "fill in", "description here", "{{", "..."]


def parse_fm(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def main():
    # Hook receives tool input as JSON on stdin
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".mdx"):
        sys.exit(0)

    # Skip snippets and templates
    if "/snippets/" in file_path or "/.claude/" in file_path:
        sys.exit(0)

    # Read the content that was written
    content = tool_input.get("content", "")
    if not content:
        # For Edit tool, we need to read the file
        try:
            with open(file_path) as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            sys.exit(0)

    fm = parse_fm(content)
    errors = []

    if not fm.get("title"):
        errors.append("Missing required frontmatter field: title")

    desc = fm.get("description", "")
    if not desc:
        errors.append("Missing required frontmatter field: description")
    elif len(desc) < MIN_DESC_LEN:
        errors.append(f"Description too short ({len(desc)} chars, need {MIN_DESC_LEN}+)")
    elif any(p in desc.lower() for p in PLACEHOLDER_PATTERNS):
        errors.append(f"Placeholder description detected: '{desc}'")

    if errors:
        print("FRONTMATTER VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
