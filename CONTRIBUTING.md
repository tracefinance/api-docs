# Contributing to Trace Finance Developer Docs

Rules and conventions for anyone editing this documentation site.

## Audience

These docs are **public** and serve **customers** — the companies integrating with Trace FX. Do not publish internal implementation details, backoffice endpoints, or dashboard-specific content.

## Terminology

| Term | Meaning | Usage |
|---|---|---|
| **Customer** | The company integrating with Trace FX | "As a customer, you authenticate using your API credentials." |
| **Account owner** | The person or entity whose account is being managed (maps to `account.owner` in the API) | "Create an account for an account owner." |

Never use "customer" to mean the account owner. Never use "partner" or "client" — use "customer."

## Content ownership

| Content | Location | Owner | When to update |
|---|---|---|---|
| Endpoint reference (OpenAPI) | `apis/{service}/openapi.yml` | Service team | Every `/api` endpoint change |
| Everything else (MDX) | `guides/`, `journeys/`, `webhooks/`, `reference/`, `snippets/` | Whoever writes docs | Product or conceptual changes |

## Drift prevention

OpenAPI specs live in this repo, not in the service repos. To prevent drift:

1. **PR checklist in service repos**: if a PR changes an `/api` endpoint, the author opens a follow-up PR here updating `apis/{service}/openapi.yml`.
2. **CODEOWNERS**: `apis/fx-account/openapi.yml` and `apis/fx-payment/openapi.yml` require review from the respective backend team.
3. **Quarterly audit**: verify that deployed endpoints still match the committed specs.

## Scope: `/api` channel only

Both services expose three channels (`/api`, `/dashboard`, `/admin`). Only `/api` endpoints appear in these docs. Strip `/dashboard` and `/admin` paths from OpenAPI specs before committing.

## File naming

- Kebab-case: `open-brl-account.mdx`, not `openBrlAccount.mdx`.
- No date prefixes or version numbers: `deposit.mdx`, not `01-deposit.mdx`.
- The filename becomes the URL path — keep it readable.

## Frontmatter

Every MDX file requires `title` and `description`:

```yaml
---
title: "Authenticate requests"
description: "How to obtain and use Auth0 JWTs to call Trace FX APIs."
---
```

Optional fields:
- `sidebarTitle`: when `title` would wrap in the sidebar.
- `icon`: for top-level group landing pages only.
- `tag: "BETA"`: for unreleased endpoints or features.

## Internal links

Root-relative, no file extension:

```mdx
[see authentication](/guides/authentication)
```

Never use relative paths (`../`) or absolute external URLs for internal pages.

## Voice and style

- Second-person ("you"), active voice.
- Sentence case for headings.
- Bold for UI elements (**Dashboard**).
- `code` formatting for filenames, commands, headers (`X-Idempotency-Key`), and endpoint paths (`POST /accounts`).
- No marketing adjectives (*powerful, seamless, robust*).
- No filler phrases (*in order to, it's important to note*).
- No editorializing (*simply, just, obviously*).
- Internal class names (`AmountV2`, `ApplicationException`, `DefaultClaims`) **never appear** in public content. Use the field name as customers see it: "amount object", "error response."

## Components

Use Mintlify built-in components. Do not create custom components.

| Need | Use |
|---|---|
| Step-by-step instructions | `<Steps>` |
| Mutually exclusive examples | `<Tabs>` |
| Optional deep detail | `<Accordion>` / `<Expandable>` |
| Multi-language code | `<CodeGroup>` |
| Callouts | `<Note>`, `<Tip>`, `<Info>`, `<Warning>`, `<Check>` |
| Cross-page navigation | `<Card>` |
| API parameter (MDX-only reference) | `<ParamField>` |

## Code examples

- Use realistic values: actual currency codes (`BRL`, `USD`), realistic UUIDs, sandbox base URL (`https://faas.sandbox.tracefinance.io`).
- Every code block must declare its language: ` ```json `, ` ```bash `, etc.
- Money uses minor units: `{ "value": 500000, "asset": "BRL" }` not `{ "amount": "5.00 BRL" }`.
- No `foo`, `bar`, `test123`, or placeholder values.

## Reusable content

Shared fragments live in `snippets/`. Import them in MDX:

```mdx
import AuthHeader from '/snippets/auth-header.mdx';

<AuthHeader />
```

Only create a snippet when the exact same content appears on multiple pages. Do not snippet content that varies between pages.

## Adding a new endpoint

1. Add the operation to `apis/{service}/openapi.yml`.
2. Add the operation path to the relevant group in `docs.json` (e.g., `"POST /api/operations/withdrawal"`).
3. Run `mint dev` — verify the endpoint renders with a playground.
4. Run `mint broken-links`.

## Adding a new guide page

1. Create the MDX file at the appropriate path (e.g., `guides/topic.mdx`).
2. Add the path (without `.mdx`) to the appropriate group in `docs.json`.
3. Include `title` and `description` frontmatter.
4. Cross-link from at least one existing page — orphan pages are hard to find.
5. Run `mint dev` and `mint broken-links`.

## Validation before merge

Every PR to `main` must pass:

- `mint dev` renders changed pages without errors.
- `mint broken-links` passes.
- `mint validate` passes.
- OpenAPI changes validate as OpenAPI 3.x.

## `.mintignore`

Drafts go in `drafts/` or use `*.draft.mdx`. Use `.mintignore` to exclude files from builds entirely. Do not rely on "not in docs.json" — Mintlify can still index unlisted pages for search.

## Images

Store in `/images/{topic}/`. Always include descriptive alt text that says what the image *conveys*, not what it *is*.

Provide light and dark variants when images have white backgrounds:

```mdx
<img src="/images/quickstart/response-light.png" className="block dark:hidden" alt="..." />
<img src="/images/quickstart/response-dark.png" className="hidden dark:block" alt="..." />
```
