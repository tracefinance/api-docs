#!/usr/bin/env python3
"""Hook: enforce required body sections based on page type template.

Non-blocking (warning only) — guides the writer without hard-blocking saves.
"""

import json
import re
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

PAGE_TYPE_RULES = [
    ("index.mdx", "landing"),
    ("quickstart.mdx", "quickstart"),
    ("guides/principles/", "principle"),
    ("guides/", "guide"),
    ("journeys/", "journey"),
    ("webhooks/overview.mdx", "webhook-overview"),
    ("webhooks/events.mdx", "webhook-events"),
    ("reference/errors-catalog.mdx", "errors-catalog"),
    ("reference/", "reference-overview"),
]


def infer_type(file_path: str) -> str | None:
    # Normalize to relative-ish path
    parts = file_path.split("/")
    # Find the api-docs root
    try:
        idx = parts.index("api-docs")
        rel = "/".join(parts[idx + 1:])
    except ValueError:
        rel = "/".join(parts[-2:])

    for pattern, page_type in PAGE_TYPE_RULES:
        if pattern.endswith("/"):
            if rel.startswith(pattern):
                return page_type
        elif rel == pattern or rel.endswith("/" + pattern):
            return page_type
    return None


def get_required_sections(page_type: str) -> list[str]:
    template = TEMPLATES_DIR / f"{page_type}.mdx"
    if not template.exists():
        return []
    text = template.read_text(encoding="utf-8")
    # Strip frontmatter
    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    return [h.strip().lower() for h in HEADING_RE.findall(body)]


def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".mdx"):
        sys.exit(0)

    if "/snippets/" in file_path or "/.claude/" in file_path:
        sys.exit(0)

    page_type = infer_type(file_path)
    if not page_type or page_type == "landing":
        sys.exit(0)  # Landing pages are free-form

    required = get_required_sections(page_type)
    if not required:
        sys.exit(0)

    # Read current file content
    content = tool_input.get("content", "")
    if not content:
        try:
            with open(file_path) as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            sys.exit(0)

    actual = [h.strip().lower() for h in HEADING_RE.findall(content)]
    missing = [s for s in required if s not in actual]

    if missing:
        print(f"TEMPLATE WARNING ({page_type}):", file=sys.stderr)
        print(f"  Missing required sections: {', '.join(f'## {s.title()}' for s in missing)}", file=sys.stderr)
        print(f"  Template: .claude/templates/{page_type}.mdx", file=sys.stderr)
        # Non-blocking — exit 0 so the write still happens
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
