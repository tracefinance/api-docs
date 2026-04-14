---
name: evaluate
description: Run documentation quality evals. Use when asked to check quality, run evals, or validate docs. Also use after completing a batch of content work to verify quality.
---

# Evaluate documentation quality

Run the eval suite to measure documentation health.

## Usage

- `/evaluate` — run all evals and report scores
- `/evaluate frontmatter` — run a specific eval
- `/evaluate --threshold 90` — override pass threshold

## Available evals

| Eval | What it checks | Default threshold |
|---|---|---|
| `frontmatter-completeness` | title + description present | 95% |
| `content-depth` | Stub detection (TODO-only pages) | 50% |
| `description-quality` | Non-placeholder, >= 20 chars | 95% |
| `orphan-detector` | Every .mdx in docs.json | 90% |
| `navigation-coverage` | Every docs.json entry has a .mdx file | 90% |
| `freshness-checker` | Pages updated within 90 days | 70% |
| `openapi-completeness` | No TODO stubs in OpenAPI specs | 50% |

## Instructions

When the user runs `/evaluate` with no arguments, run ALL evals:

```bash
for eval in frontmatter-completeness content-depth description-quality orphan-detector navigation-coverage freshness-checker openapi-completeness; do
  python3 .claude/evals/$eval.py --json 2>&1
  echo "---"
done
```

Parse each result JSON and present a summary table:

| Eval | Score | Status |
|---|---|---|
| name | XX.X% | PASS/FAIL |

If a specific eval name is given, run only that one:

```bash
python3 .claude/evals/{eval-name}.py --json 2>&1
```

Show detailed issues for any eval scoring below 80%.

After showing results, suggest the highest-impact fix: which eval has the worst score and what specific files need attention.

When `--threshold` is passed, override the default threshold for all evals.

## After content work

When you've just finished writing or editing multiple pages, proactively suggest running `/evaluate` to verify quality hasn't regressed.
