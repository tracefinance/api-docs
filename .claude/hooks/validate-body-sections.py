#!/usr/bin/env python3
"""Hook: enforce required body sections based on page type template.

Non-blocking (warning only) — guides the writer without hard-blocking saves.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
from _lib import (
    load_hook_input, abs_to_rel, infer_page_type,
    FRONTMATTER_RE, SECTION_HEADING_RE, TEMPLATES_DIR,
)


def get_required_sections(page_type: str) -> list[str]:
    template = TEMPLATES_DIR / f"{page_type}.mdx"
    if not template.exists():
        return []
    text = template.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    return [h.strip().lower() for h in SECTION_HEADING_RE.findall(body)]


def main():
    result = load_hook_input()
    if result is None:
        sys.exit(0)

    file_path, content = result

    page_type = infer_page_type(abs_to_rel(file_path))
    if not page_type or page_type == "landing":
        sys.exit(0)

    required = get_required_sections(page_type)
    if not required:
        sys.exit(0)

    actual = [h.strip().lower() for h in SECTION_HEADING_RE.findall(content)]
    missing = [s for s in required if s not in actual]

    if missing:
        print(f"TEMPLATE WARNING ({page_type}):", file=sys.stderr)
        print(f"  Missing required sections: {', '.join(f'## {s.title()}' for s in missing)}", file=sys.stderr)
        print(f"  Template: .claude/templates/{page_type}.mdx", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
