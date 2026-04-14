#!/usr/bin/env python3
"""Eval: detect TODO stubs in OpenAPI specs.

Checks for:
  - Operations with 'TODO' in description
  - Operations missing request body schemas (POST/PUT/PATCH)
  - Operations missing response schemas
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import REPO_ROOT, output_result

# Simple YAML value extractor (avoids PyYAML dependency)
TODO_RE = re.compile(r"TODO", re.IGNORECASE)

APIS_DIR = REPO_ROOT / "apis"
METHODS_NEEDING_BODY = {"post", "put", "patch"}


def parse_openapi_operations(spec_path: Path) -> list[dict]:
    """Extract operations from an OpenAPI YAML file.

    Returns list of {method, path, has_description_todo, has_request_body, has_response_schema}.
    Uses a simple line-based parser to avoid PyYAML dependency.
    """
    try:
        import yaml
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
    except ImportError:
        # Fallback: parse with json if it's JSON, otherwise line-scan for TODOs
        try:
            with open(spec_path) as f:
                spec = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return _line_scan_for_todos(spec_path)

    operations = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            desc = op.get("description", "") or ""
            has_todo = bool(TODO_RE.search(desc))
            has_body = "requestBody" in op
            responses = op.get("responses", {})
            has_response_schema = any(
                "content" in (r if isinstance(r, dict) else {})
                for r in responses.values()
                if isinstance(r, dict) and r.get("description", "") != ""
            )
            operations.append({
                "method": method.upper(),
                "path": path,
                "has_description_todo": has_todo,
                "has_request_body": has_body,
                "has_response_schema": has_response_schema,
            })
    return operations


def _line_scan_for_todos(spec_path: Path) -> list[dict]:
    """Fallback: scan YAML for TODO strings without full parsing."""
    text = spec_path.read_text(encoding="utf-8")
    operations = []
    current_path = None
    current_method = None
    for line in text.splitlines():
        stripped = line.strip()
        # Detect path entries (indented under paths:)
        if line.startswith("  /") and line.rstrip().endswith(":"):
            current_path = stripped.rstrip(":")
        elif line.startswith("    ") and stripped.split(":")[0] in (
            "get", "post", "put", "patch", "delete", "head", "options"
        ):
            current_method = stripped.split(":")[0].upper()
        elif "TODO" in line and current_path and current_method:
            operations.append({
                "method": current_method,
                "path": current_path,
                "has_description_todo": True,
                "has_request_body": False,
                "has_response_schema": False,
            })
    return operations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=50.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    issues = []
    total_ops = 0

    for spec_file in sorted(APIS_DIR.rglob("openapi.*")):
        service = spec_file.parent.name
        operations = parse_openapi_operations(spec_file)

        for op in operations:
            total_ops += 1
            op_id = f"{op['method']} {op['path']}"

            if op["has_description_todo"]:
                issues.append({
                    "service": service,
                    "operation": op_id,
                    "message": "Description contains TODO",
                })

            if op["method"] in METHODS_NEEDING_BODY and not op["has_request_body"]:
                issues.append({
                    "service": service,
                    "operation": op_id,
                    "message": f"{op['method']} operation missing requestBody schema",
                })

            if not op["has_response_schema"]:
                issues.append({
                    "service": service,
                    "operation": op_id,
                    "message": "Missing response content schema",
                })

    # Score: per-operation, each issue deducts from that operation
    failed_ops = len({(i["service"], i["operation"]) for i in issues})
    passed = total_ops - failed_ops
    score = (passed / total_ops * 100) if total_ops > 0 else 100.0

    output_result("openapi-completeness", score, total_ops, passed, issues, args.threshold)
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
