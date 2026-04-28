---
paths:
  - "apis/**/*.yml"
  - "apis/**/*.yaml"
---

# OpenAPI authoring rules

These rules apply when editing any spec under `apis/`. The companion hook
`.claude/hooks/validate-openapi-conventions.py` warns at save-time on the
machine-checkable subset.

## Source-of-truth alignment

- **Verify before writing.** Before adding or modifying a schema, read the
  corresponding Kotlin source class (request/response/event class). The
  schema must reflect the live class — same field names, same types, no
  invented fields.
- For ambiguous nested types you cannot fully verify, use
  `additionalProperties: true` on a typed `object` with a clear
  description note. Do **not** invent fields.
- When the live source has typed identifiers (`UUID`, `String`), reflect
  that exactly: `format: uuid` for `UUID`, no format for plain `String`.
- Rail services (`fx-ted`, `fx-pix`, `fx-boleto`, `fx-exchange`,
  `fx-customer-compliance`) are **internal**. Their events do not appear
  in `apis/fx-webhook/openapi.yml`. Public webhook resources are
  `ACCOUNT`, `BENEFICIARY`, `OPERATION` only.

## Reusability

- Any value used in **two or more** places gets extracted to
  `components.schemas`. Do not repeat inline definitions.
- Cross-cutting parameters (`X-Trace-Version`, `X-Idempotency-Key`,
  pagination params) live in `components.parameters` and are referenced
  via `$ref`.
- Repeated response shapes (errors, acknowledgements) live in
  `components.responses` and are referenced via `$ref`. Example:
  `WebhookAck` for the standard 200 response on every webhook event.
- Standard schemas that appear in every spec: `Currency`, `Rail`,
  `ErrorResponse`, `PaginationMeta`. Always named components, never
  inline.

## Discriminated unions

- Use `oneOf` paired with `discriminator: { propertyName, mapping }`.
  Never `oneOf` without `discriminator`.
- **Every variant referenced from `oneOf` must have a `title:` field.**
  Mintlify uses the title for tab labels — without it, partners see
  "Option 1 / Option 2 / Option 3".
- Pick the most semantic discriminator field. If `rail` uniquely
  identifies the variant, use `rail`. Otherwise `type`.
- The discriminator value matches the live `JsonSubTypes` name
  (e.g., `"PixKey"`, not `"PIX_KEY"`, when the Kotlin class is annotated
  with `@JsonSubTypes(name = "PixKey")`).

## Examples

- Every request body declares **at least one** named example via the
  `examples:` map. Single `example:` is fine for trivial cases.
- Use realistic data: real UUIDs, BRL/USD amounts in minor units,
  Brazilian city names, real PIX key formats. Do not use placeholders
  like `string`, `<value>`, or `0`.
- Multi-shape operations get one named example per shape (e.g.,
  `change-url`, `replace-resources`, `disable-retry`).

## Naming

- Schema names match the Kotlin source class name where there is a 1:1
  mapping (`OperationEvent`, `BeneficiaryReferenceEvent`, `AmountEvent`).
- For schemas distinct from the live class, prefer descriptive names
  (`PixKeyAddressEvent` for the financial-address variant, not just
  `PixKeyEvent` which conflicts).
- Field names are always camelCase.
- Enum values are uppercase with underscores (`PENDING_REVIEW`).

## Versioning and paths

- `/v1` is a **header selector** (`X-Trace-Version: 1`). It is **never**
  a URL path segment. Do not write paths like `/api/v1/...`.
- Server URL is per-service: `https://faas.{env}.tracefinance.io/account`,
  `/payment`, `/webhook`.
- Strip `/dashboard` and `/admin` paths — only `/api` channel is
  documented (per `CONTRIBUTING.md`). Public discovery endpoints (e.g.,
  `/references/...`) sit outside `/api` and require no auth — set
  `security: []` to override the global `bearerAuth`.

## Pagination

- List endpoints reference the shared parameters: `PaginationLimit`,
  `PaginationCursor`, `PaginationDirection`, `PaginationSortOrder`.
- Response wraps as `{ data: [...], meta: PaginationMeta }`. The schema
  name is `XxxList`.

## Description style

- Sentence case. No marketing language ("seamless", "powerful",
  "best-in-class"). The `check-description.py` hook flags marketing
  words on MDX; the same restraint applies here.
- No internal infrastructure terms in public-facing descriptions: do
  **not** mention SQS, SNS topic names, Kotlin class names, internal
  service names, etc.
- Cross-link to narrative pages with markdown links:
  `[Errors](/guides/principles/errors)`.

## After every spec change

Run `mint validate` and `mint broken-links`. Both must pass before the
spec is considered done.
