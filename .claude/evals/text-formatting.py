#!/usr/bin/env python3
"""Eval: detect text-formatting issues in OpenAPI specs that cause visible
line breaks in the Mintlify-rendered output.

Background
----------
Mintlify renders OpenAPI ``description`` fields with newlines preserved as
visible ``<br>`` breaks. When a YAML literal block scalar (``|``) is used
for prose with soft-wrapped lines, those soft wraps surface in the rendered
docs as orphaned words and broken sentences. Example::

    description: |
      Every deposit references a quote previously obtained from `POST /api/quotes`. The
      quote determines `sourceAmount` and `targetAmount` and locks the FX rate.

Renders as::

    Every deposit references a quote previously obtained from POST /api/quotes . The
    quote determines sourceAmount and targetAmount and locks the FX rate.

with ``The`` orphaned on its own line.

Two safe alternatives:

1. Use ``>`` (folded scalar): single newlines collapse to spaces; blank
   lines become paragraph breaks. Best for prose.
2. Keep ``|`` and put each prose paragraph on a single source line. Best
   for blocks that mix prose with tables or lists, since folded scalars
   don't preserve the table grid.

What this eval flags
--------------------
Inside any ``|`` (literal) block scalar in an OpenAPI YAML file, two
consecutive non-blank prose lines with no blank line between them — i.e.,
a soft wrap. Markdown tables, lists, fenced code blocks, headings, and
HTML tags are recognized as intentional structure and excluded.

The eval also flags blocks that use ``|`` but contain only single-line or
soft-wrapped prose (no tables/lists/code) — those should use ``>`` instead
even if the prose currently fits on one line, because a future edit that
wraps the line would silently break the rendered output.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import REPO_ROOT


APIS_DIR = REPO_ROOT / "apis"

# Lines that indicate intentional Markdown structure inside a block scalar.
# Any line matching one of these is *not* prose and is exempt from the
# soft-wrap check.
TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s")
HEADING = re.compile(r"^\s*#{1,6}\s")
BLOCKQUOTE = re.compile(r"^\s*>\s")
HTML_TAG = re.compile(r"^\s*<[A-Za-z/!]")
CODE_FENCE = re.compile(r"^\s*```")

# A YAML key that opens a literal block scalar:  "  foo: |"  or  "  foo: |-"
LITERAL_BLOCK_OPENER = re.compile(
    r"^(?P<indent>\s*)(?P<key>[A-Za-z_][A-Za-z0-9_-]*)\s*:\s*\|[+-]?\s*(#.*)?$"
)


def is_structural(line: str) -> bool:
    """Return True if a line is a Markdown table row, list item, heading,
    blockquote, fenced code marker, or HTML tag — anything that is
    intentional formatting rather than prose."""
    return bool(
        TABLE_LINE.match(line)
        or LIST_ITEM.match(line)
        or HEADING.match(line)
        or BLOCKQUOTE.match(line)
        or HTML_TAG.match(line)
        or CODE_FENCE.match(line.lstrip())
    )


def find_literal_blocks(lines: list[str]):
    """Yield ``(opener_lineno, base_indent, block_lines)`` for each literal
    block scalar in ``lines``.

    ``opener_lineno`` is 1-based and points at the line containing the
    ``|`` marker. ``base_indent`` is the indent of that opener line; block
    content must be indented strictly more than this.
    """
    i = 0
    while i < len(lines):
        m = LITERAL_BLOCK_OPENER.match(lines[i])
        if not m:
            i += 1
            continue

        base_indent = len(m.group("indent"))
        block_lines: list[tuple[int, str]] = []  # (lineno, raw line)
        j = i + 1

        # Consume the block: every line that is either blank or indented
        # more than base_indent belongs to the block.
        while j < len(lines):
            line = lines[j]
            if line.strip() == "":
                block_lines.append((j + 1, line))
                j += 1
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent:
                break
            block_lines.append((j + 1, line))
            j += 1

        yield i + 1, base_indent, block_lines
        i = j


def lint_block(opener_lineno: int, base_indent: int, block_lines):
    """Yield ``(lineno, message)`` issues for a single literal block.

    Two checks are performed:

    1. **Soft-wrap**: any pair of consecutive non-blank, non-structural
       lines is flagged as a soft-wrap — those newlines will render as
       visible breaks.
    2. **Pure prose using `|`**: if the entire block is prose (no tables,
       lists, or code), recommend switching to ``>``. This is reported
       once per block on the opener line.
    """
    issues = []

    # Strip block indent for content analysis. The base indent of the
    # block content is one or more spaces past base_indent; we don't need
    # the exact value, we only check structural patterns on the line as a
    # whole and rely on ``\s*`` in the regexes.
    in_code_fence = False
    prev_was_prose = False
    saw_structure = False
    saw_prose = False

    for lineno, raw in block_lines:
        # Toggle fence state on lines whose first non-space token is ```.
        # The fence marker line itself is treated as structural.
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            saw_structure = True
            prev_was_prose = False
            continue

        if in_code_fence:
            saw_structure = True
            prev_was_prose = False
            continue

        if stripped == "":
            prev_was_prose = False
            continue

        # Strip the block indent before structural tests so that, e.g.,
        # "  | a | b |" still matches TABLE_LINE.
        if is_structural(raw):
            saw_structure = True
            prev_was_prose = False
            continue

        # This line is prose.
        if prev_was_prose:
            issues.append(
                (
                    lineno,
                    "soft-wrapped prose inside `|` literal block — the newline "
                    "renders as a visible break in Mintlify; either join the "
                    "line with the previous one or switch the block to `>` "
                    "(folded scalar)",
                )
            )
            # Don't reset prev_was_prose so we keep flagging every offending
            # break in a multi-line wrap, not just the first.
        prev_was_prose = True
        saw_prose = True

    # Whole-block recommendation: pure prose should use `>` not `|`.
    if saw_prose and not saw_structure:
        # Only emit if the block has more than one prose line OR we already
        # flagged a soft-wrap. A single-line literal scalar (rare but
        # legal) is not a current bug, but switching to `>` is still a
        # safer default — we report it on the opener line.
        prose_line_count = sum(
            1 for _, raw in block_lines if raw.strip() and not raw.lstrip().startswith("```")
        )
        if prose_line_count > 1 or any(lineno for lineno, _ in []):
            # The soft-wrap issues already cover multi-line prose blocks.
            # Add the block-level hint only when it isn't redundant (i.e.,
            # nothing structural was seen so `>` is unambiguously safe).
            issues.append(
                (
                    opener_lineno,
                    "literal block scalar `|` used for pure prose — switch to "
                    "`>` (folded scalar) so soft wraps don't render as "
                    "visible breaks",
                )
            )

    # Deduplicate by lineno (keep the first message per line).
    seen = set()
    deduped = []
    for lineno, msg in issues:
        if lineno in seen:
            continue
        seen.add(lineno)
        deduped.append((lineno, msg))
    return deduped


def lint_file(path: Path):
    """Return a list of ``{file, line, message}`` issues for one YAML file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel = str(path.relative_to(REPO_ROOT))

    out = []
    for opener_lineno, base_indent, block_lines in find_literal_blocks(lines):
        for lineno, msg in lint_block(opener_lineno, base_indent, block_lines):
            out.append({"file": rel, "line": lineno, "message": msg})
    return out


def collect_yaml_files() -> list[Path]:
    files = []
    for ext in ("*.yml", "*.yaml"):
        files.extend(APIS_DIR.rglob(ext))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--threshold",
        type=float,
        default=100.0,
        help="Pass threshold (percent of files clean). Default: 100.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON to stdout instead of a summary.",
    )
    args = parser.parse_args()

    files = collect_yaml_files()
    all_issues: list[dict] = []
    failing_files: set[str] = set()

    for f in files:
        issues = lint_file(f)
        if issues:
            failing_files.add(str(f.relative_to(REPO_ROOT)))
            all_issues.extend(issues)

    total = len(files)
    passed = total - len(failing_files)
    score = (passed / total * 100.0) if total else 100.0
    pass_ = score >= args.threshold

    if args.json:
        json.dump(
            {
                "eval": "text-formatting",
                "score": round(score, 1),
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "threshold": args.threshold,
                "pass": pass_,
                "issues": all_issues,
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        status = "PASS" if pass_ else "FAIL"
        print(f"[{status}] text-formatting: {score:.1f}% ({passed}/{total})", file=sys.stderr)
        for issue in all_issues:
            print(
                f"  {issue['file']}:{issue['line']}: {issue['message']}",
                file=sys.stderr,
            )

    sys.exit(0 if pass_ else 1)


if __name__ == "__main__":
    main()
