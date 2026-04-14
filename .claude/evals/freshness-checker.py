#!/usr/bin/env python3
"""Eval: flag pages not updated in git for more than N days."""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import collect_mdx_files, rel_path, REPO_ROOT, output_result


DEFAULT_STALE_DAYS = 90


def git_last_modified(file_path: Path) -> datetime | None:
    """Get the last commit date for a file from git."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(file_path)],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        if result.returncode == 0 and result.stdout.strip():
            return datetime.fromisoformat(result.stdout.strip())
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=70.0)
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    files = collect_mdx_files()
    issues = []

    for f in files:
        rp = rel_path(f)
        last_mod = git_last_modified(f)

        if last_mod is None:
            # File not yet committed — not stale, skip
            continue

        age_days = (now - last_mod).days
        if age_days > args.stale_days:
            issues.append({
                "file": rp,
                "days_since_update": age_days,
                "last_updated": last_mod.isoformat(),
                "message": f"Stale: {age_days} days since last update (threshold: {args.stale_days})",
            })

    total = len(files)
    passed = total - len(issues)
    score = (passed / total * 100) if total > 0 else 100.0

    output_result("freshness-checker", score, total, passed, issues, args.threshold)
    sys.exit(0 if score >= args.threshold else 1)


if __name__ == "__main__":
    main()
