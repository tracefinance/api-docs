"""Shared utilities for Mintlify docs evals and hooks."""

import json
import os
import re
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_JSON = REPO_ROOT / "docs.json"
TEMPLATES_DIR = REPO_ROOT / ".claude" / "templates"

EXCLUDED_PREFIXES = (
    ".claude/", ".github/", ".idea/", "node_modules/",
    "drafts/", "images/", "logo/", "apis/", "snippets/",
)

EXCLUDED_FILES = {"README.md", "CONTRIBUTING.md", "CLAUDE.md", "LICENSE"}

# ── Page type inference ────────────────────────────────────────────────

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


def infer_page_type(rel_path: str) -> str | None:
    """Infer the page type from a file's relative path."""
    for pattern, page_type in PAGE_TYPE_RULES:
        if pattern.endswith("/"):
            if rel_path.startswith(pattern):
                return page_type
        else:
            if rel_path == pattern:
                return page_type
    return None


def get_template_path(page_type: str) -> Path | None:
    """Get the template file for a page type."""
    p = TEMPLATES_DIR / f"{page_type}.mdx"
    return p if p.exists() else None


# ── Frontmatter parsing ───────────────────────────────────────────────

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from MDX content. Simple subset parser."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            fm[key] = val
    return fm


# ── Content analysis ──────────────────────────────────────────────────

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
SECTION_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
TODO_RE = re.compile(r"\{/\*\s*TODO:", re.IGNORECASE)
PLACEHOLDER_PATTERNS = ["todo", "tbd", "placeholder", "fill in", "description here", "{{", "..."]

MIN_DESCRIPTION_LENGTH = 20
SUBSTANTIVE_WORD_COUNT = 200
THIN_WORD_COUNT = 30


def extract_headings(text: str) -> list[tuple[int, str]]:
    """Extract (level, title) from markdown headings."""
    return [(len(m.group(1)), m.group(2).strip()) for m in HEADING_RE.finditer(text)]


def extract_body(text: str) -> str:
    """Extract content after frontmatter, stripping MDX comments."""
    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    # Strip MDX comments
    body = re.sub(r"\{/\*.*?\*/\}", "", body, flags=re.DOTALL)
    return body.strip()


def word_count(text: str) -> int:
    """Count words in text, excluding markdown syntax and component tags."""
    # Remove component tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Remove markdown links, images
    clean = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", clean)
    # Remove code blocks
    clean = re.sub(r"```[\s\S]*?```", "", clean)
    # Remove inline code
    clean = re.sub(r"`[^`]+`", "", clean)
    # Remove headings markers
    clean = re.sub(r"^#{1,6}\s+", "", clean, flags=re.MULTILINE)
    return len(clean.split())


def is_placeholder(value: str) -> bool:
    """Check if a string is a placeholder."""
    lower = value.lower().strip()
    return any(p in lower for p in PLACEHOLDER_PATTERNS)


def has_todo_only(text: str) -> bool:
    """Check if body is empty except for TODO comments."""
    body = extract_body(text)
    return len(body) == 0 or (TODO_RE.search(text) and word_count(body) < 5)


# ── docs.json navigation ──────────────────────────────────────────────

def load_docs_json() -> dict:
    """Load and return docs.json."""
    with open(DOCS_JSON) as f:
        return json.load(f)


def extract_nav_pages(docs: dict) -> set[str]:
    """Extract all page paths referenced in docs.json navigation.

    Returns paths without .mdx extension (as they appear in docs.json).
    Skips OpenAPI operation references like 'GET /api/...'
    """
    pages = set()

    def walk(obj):
        if isinstance(obj, str):
            # Skip OpenAPI operation references
            if not re.match(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/", obj):
                pages.add(obj)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            if "pages" in obj:
                walk(obj["pages"])
            if "groups" in obj:
                walk(obj["groups"])
            if "tabs" in obj:
                walk(obj["tabs"])

    nav = docs.get("navigation", {})
    walk(nav)
    return pages


# ── File collection ───────────────────────────────────────────────────

def collect_mdx_files() -> list[Path]:
    """Collect all .mdx files in the repo, excluding non-content dirs."""
    files = []
    for p in REPO_ROOT.rglob("*.mdx"):
        rel = str(p.relative_to(REPO_ROOT))
        if any(rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue
        files.append(p)
    return sorted(files)


def rel_path(p: Path) -> str:
    """Get path relative to repo root."""
    return str(p.relative_to(REPO_ROOT))


# ── Output formatting ─────────────────────────────────────────────────

def output_result(name: str, score: float, total: int, passed: int,
                  issues: list[dict], threshold: float = 0.0):
    """Print eval result as JSON to stdout, human summary to stderr."""
    result = {
        "eval": name,
        "score": round(score, 1),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "threshold": threshold,
        "pass": score >= threshold,
        "issues": issues,
    }
    json.dump(result, sys.stdout, indent=2)
    print(file=sys.stdout)

    # Human-readable summary to stderr
    status = "PASS" if score >= threshold else "FAIL"
    print(f"[{status}] {name}: {score:.1f}% ({passed}/{total})", file=sys.stderr)
    if issues and score < 80:
        for issue in issues[:10]:
            print(f"  - {issue.get('file', '?')}: {issue.get('message', '?')}", file=sys.stderr)
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more", file=sys.stderr)


# ── Hook helpers ───────────────────────────────────────────────────────

def load_hook_input() -> tuple[str, str] | None:
    """Read PostToolUse hook JSON from stdin and return (file_path, content).

    Returns None when the file should be skipped (non-MDX, snippet, template).
    Handles both Write (content in payload) and Edit (read from disk) tools.
    """
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".mdx"):
        return None

    if "/snippets/" in file_path or "/.claude/" in file_path:
        return None

    content = tool_input.get("content", "")
    if not content:
        try:
            with open(file_path) as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            return None

    return file_path, content


def abs_to_rel(file_path: str) -> str:
    """Convert an absolute file path to a path relative to the repo root.

    Falls back to the filename if the path is not under REPO_ROOT.
    """
    try:
        return str(Path(file_path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return Path(file_path).name
