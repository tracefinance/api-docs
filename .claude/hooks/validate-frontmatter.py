#!/usr/bin/env python3
"""Hook: validate frontmatter on MDX files after write/edit.

Blocks saves with missing title or description.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
from _lib import (
    load_hook_input, parse_frontmatter, is_placeholder,
    MIN_DESCRIPTION_LENGTH,
)


def main():
    result = load_hook_input()
    if result is None:
        sys.exit(0)

    _, content = result
    fm = parse_frontmatter(content)
    errors = []

    if not fm.get("title"):
        errors.append("Missing required frontmatter field: title")

    desc = fm.get("description", "")
    if not desc:
        errors.append("Missing required frontmatter field: description")
    elif len(desc) < MIN_DESCRIPTION_LENGTH:
        errors.append(f"Description too short ({len(desc)} chars, need {MIN_DESCRIPTION_LENGTH}+)")
    elif is_placeholder(desc):
        errors.append(f"Placeholder description detected: '{desc}'")

    if errors:
        print("FRONTMATTER VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
