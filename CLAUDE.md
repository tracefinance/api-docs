# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Trace Finance's public developer documentation for the FX platform, built on [Mintlify](https://mintlify.com). Partners ("customers") integrate with two services — **FX Account** (multi-currency account management) and **FX Payment** (deposits, withdrawals, swaps, beneficiaries) — documented here as one unified API surface.

Content is public. Internal class names, backoffice endpoints, dashboard endpoints, and ADRs never appear here.

## Commands

- `mint dev` — preview at `http://localhost:3000` (run from repo root)
- `mint build` — strict build validation + OpenAPI spec validation
- `mint broken-links` — check internal links
- `mint accessibility` — check alt text and color contrast
- `mint update` — upgrade CLI if `mint dev` misbehaves
- Install CLI: `npm i -g mint`

Validation = `mint build` passes + `mint broken-links` passes + `mint accessibility` passes.

## Architecture

### Configuration

**`docs.json`** is the source of truth for navigation, theming, and OpenAPI wiring. Currently one tab: **Guides**. The **API Reference** tab will be added when OpenAPI schemas are fleshed out. Every page must be listed in `docs.json` or it won't appear in the sidebar.

### Content (MDX)

Pages are MDX with YAML frontmatter (`title` + `description` required). Mintlify components (`<Steps>`, `<Tabs>`, `<Note>`, etc.) are available without imports.

| Folder | Content |
|---|---|
| `guides/` | Authentication, environments, API principles (versioning, idempotency, pagination, money, errors) |
| `journeys/` | End-to-end flows: open accounts, deposit, withdraw, swap |
| `webhooks/` | Webhook setup and event catalog |
| `snippets/` | Reusable MDX fragments imported into other pages |
| `apis/` | OpenAPI specs (scaffold) — `fx-account/openapi.yml` and `fx-payment/openapi.yml` |

### API Reference (OpenAPI) — deferred

OpenAPI specs live in `apis/` but are not yet wired into `docs.json` navigation. When schemas are ready, add the `openapi` key and an API Reference tab to `docs.json`. Endpoint pages auto-generate from `apis/{service}/openapi.yml`. Only `/api` channel endpoints are documented. `/dashboard` and `/admin` are internal.

## Terminology

- **Customer** = the company integrating with Trace FX.
- **Account owner** = the person whose account is managed (maps to `account.owner`).
- Never use "partner" or "client."

## Key rules (full rulebook in CONTRIBUTING.md)

- Internal links: root-relative, no extension (`/guides/authentication`).
- No internal class names in public content (`AmountV2` → "amount object").
- Money: minor units as integers (`{ "value": 500000, "asset": "BRL" }`).
- Code blocks always declare language.
- Sentence case headings; no marketing adjectives; no filler.
- OpenAPI specs live here — when service teams change `/api` endpoints, they PR the spec update here too.

## When adding a page

1. Create `.mdx` with `title` + `description` frontmatter.
2. Add path to `docs.json` navigation.
3. `mint dev` to verify rendering.
4. `mint broken-links` before committing.

## Quality system

This repo has a dual-layer quality system adapted from the Trace knowledge base vault.

### Hooks (real-time, on every write/edit)

Registered in `.claude/settings.json` as PostToolUse hooks:

| Hook | Behavior |
|---|---|
| `validate-frontmatter.py` | **Blocks** saves with missing `title` or bad `description` |
| `validate-body-sections.py` | **Warns** about missing required sections per page type |
| `check-description.py` | **Warns** about marketing language in descriptions |

### Evals (run via `/evaluate` skill)

| Eval | Checks | CI Threshold |
|---|---|---|
| `frontmatter-completeness` | title + description present | 95% |
| `content-depth` | Stub detection (TODO-only pages) | 50% |
| `description-quality` | Non-placeholder descriptions | 95% |
| `orphan-detector` | Every .mdx in docs.json | 90% |
| `navigation-coverage` | Every docs.json entry has .mdx | 90% |
| `openapi-completeness` | No TODO stubs in OpenAPI specs | 50% (deferred from CI until API Reference tab is added) |

Run a single eval: `python3 .claude/evals/{name}.py --json`
Run all: use the `/evaluate` skill.

### Templates

`.claude/templates/{page-type}.mdx` define required `##` sections per page type. The `validate-body-sections` hook checks new content against these.

Page types are inferred from file paths:
- `guides/principles/*.mdx` → `principle` (Overview, How it works, Examples)
- `guides/*.mdx` → `guide` (Overview, Details, Related)
- `journeys/*.mdx` → `journey` (Overview, Prerequisites, Steps, What happens next)
- `reference/*-overview.mdx` → `reference-overview` (Overview, Key concepts)
- `webhooks/overview.mdx` → `webhook-overview` (Overview, Setup, Signatures, Retry policy)

### Reusable snippets

`snippets/` contains shared MDX blocks. Import them in any page:

```mdx
import SandboxNote from '/snippets/sandbox-note.mdx';
<SandboxNote />
```

Available: `auth-header`, `sandbox-note`, `idempotency-note`, `pagination-response`, `error-response`, `money-format`, `version-header`.

### CI (GitHub Actions)

`.github/workflows/docs-quality.yml` runs on every PR: `mint build`, `mint broken-links`, `mint accessibility`, plus all blocking evals with score thresholds.

## Source services

Internal docs for reference (not published, but useful for authoring):

- **fx-account**: `../fx-account/docs/` — domain model, HTTP contracts, journeys, events, ADRs
- **fx-payment**: `../fx-payment/docs/` — domain model, HTTP contracts, journeys, events, ADRs

These contain detailed specs for every endpoint, event payload, and business rule. Use them as source material when writing guides and filling OpenAPI schemas.
