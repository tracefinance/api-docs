#!/usr/bin/env python3
"""Hook: enforce OpenAPI authoring conventions on apis/**/*.yml.

Non-blocking (warning only). Catches the most common drift from the rules
documented in .claude/rules/openapi.md:

  - paths containing the `/v1/` segment (versioning is header-based)
  - `oneOf` without `discriminator`
  - `oneOf` variants missing `title:` (Mintlify renders "Option N" without it)
  - `requestBody` blocks missing `example:` or `examples:`

Skips gracefully when PyYAML is unavailable or the YAML cannot be parsed.
"""

import json
import sys

try:
    import yaml
except ImportError:
    yaml = None


def load_input():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return None

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith((".yml", ".yaml")):
        return None
    if "/apis/" not in file_path:
        return None

    content = tool_input.get("content", "")
    if not content:
        try:
            with open(file_path) as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            return None

    return file_path, content


def check_paths(spec, warnings):
    for path in spec.get("paths") or {}:
        if "/v1/" in path:
            warnings.append(
                f"path `{path}` contains `/v1/` — versioning is header-based "
                f"(`X-Trace-Version`), not a URL segment"
            )


def check_oneof(spec, warnings):
    schemas = (spec.get("components") or {}).get("schemas") or {}
    for name, schema in schemas.items():
        if not isinstance(schema, dict):
            continue
        one_of = schema.get("oneOf")
        if not isinstance(one_of, list):
            continue

        if "discriminator" not in schema:
            warnings.append(
                f"schema `{name}` uses `oneOf` without `discriminator` — "
                f"Mintlify needs the discriminator to render tab labels"
            )

        for variant in one_of:
            if not isinstance(variant, dict):
                continue
            ref = variant.get("$ref")
            if not isinstance(ref, str):
                continue
            if not ref.startswith("#/components/schemas/"):
                continue
            ref_name = ref.rsplit("/", 1)[-1]
            ref_schema = schemas.get(ref_name)
            if isinstance(ref_schema, dict) and "title" not in ref_schema:
                warnings.append(
                    f"schema `{ref_name}` is a `oneOf` variant of `{name}` "
                    f"but has no `title:` — it will render as `Option N` "
                    f"in Mintlify tabs"
                )


def check_request_examples(spec, warnings):
    paths = spec.get("paths") or {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            if not isinstance(op, dict):
                continue
            req = op.get("requestBody")
            if not isinstance(req, dict):
                continue
            content = req.get("content") or {}
            for media_type, media_obj in content.items():
                if not isinstance(media_obj, dict):
                    continue
                if "example" not in media_obj and "examples" not in media_obj:
                    warnings.append(
                        f"`{method.upper()} {path}` ({media_type}) has "
                        f"requestBody without `examples:` or `example:`"
                    )


def main():
    if yaml is None:
        sys.exit(0)

    result = load_input()
    if result is None:
        sys.exit(0)

    file_path, content = result

    try:
        spec = yaml.safe_load(content)
    except yaml.YAMLError:
        sys.exit(0)

    if not isinstance(spec, dict):
        sys.exit(0)

    warnings = []
    check_paths(spec, warnings)
    check_oneof(spec, warnings)
    check_request_examples(spec, warnings)

    if warnings:
        print(f"OPENAPI CONVENTIONS WARNING ({file_path}):", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
        print("  See .claude/rules/openapi.md for the full ruleset.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
