## Why

`docling-ingestion-adapter` defines the `source-document/v1` shape, but without a shared validator and deterministic fixtures every downstream change (exhibit semantics, table/hierarchy/chart semantics, case-spec refs) would re-derive and re-check the contract independently.
This change freezes `source-document/v1` behind testable helpers so changes 3–9 can cite a stable, validated anchor format (`ROADMAP.md` "Maturity and dependency policy", Phase 2).

## What Changes

- Add shared validation helpers for `source_document.json` (a reusable module, e.g. `scripts/source_document_schema.py`) that assert the `source-document/v1` field contract and the facts-only constraint.
- Add deterministic, repo-owned fixtures covering pages, blocks, bbox values, table cells, captions, headers, footers, and source notes — including at least one generated PDF fixture (title, section header, paragraph, table, caption, page header, page footer).
- Add fixture-driven tests under `tests/` that verify `source_document.json` preserves source-document facts and rejects documents that smuggle in business interpretation, accounting interpretation, chart digitization conclusions, subtotal meaning, or EMBA analysis claims.
- Provide a validation entry point the adapter and downstream changes can call (function-level and/or CLI), returning structured errors that name the offending field or path.

## Non-Goals

- Defining new `source-document/v1` fields — the shape is owned by `docling-ingestion-adapter`; this change validates it, it does not extend it.
- Exhibit semantic inference, case evidence migration, and export formatting (downstream changes).
- Requiring real EMBA case PDFs — acceptance fixtures MUST be deterministic and repo-owned (`ROADMAP.md` verification plan); real PDFs remain exploratory only.
- Image-fixture inclusion is optional and gated on repo-size/licensing; its absence MUST NOT block this change.

## Capabilities

### New Capabilities

- `source-document-validation`: shared, reusable validation helpers plus deterministic fixtures that assert a `source_document.json` conforms to `source-document/v1` and carries observed facts only, giving downstream changes a frozen anchor contract.

### Modified Capabilities

<!-- None. Adds validation tooling around the existing source-document/v1 contract without changing adapter requirements. -->

## Impact

- New file(s): a source-document schema/validation module under `scripts/`, fixtures under a repo-owned fixtures path, tests under `tests/`.
- Establishes the frozen anchor format that unblocks changes 3–9 from draft status.
- Depends on `docling-ingestion-adapter` having defined the first normalized shape.
- No change to exporters, `case_spec.json`, or `SKILL.md`.
