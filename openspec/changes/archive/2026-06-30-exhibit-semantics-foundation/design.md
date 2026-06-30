## Context

`source-document/v1` is now frozen and validated (`scripts/source_document_schema.py`). This change adds the interpretation layer above it: a deterministic classifier that reads a validated source document and emits `exhibit_semantics.json` (`exhibit-semantics/v1`), the anchor contract that table/hierarchy/chart/case-spec changes (4–7) cite.
The binding constraints are ADR-0001 (read `source_document.json`, never raw), ADR-0002 (no chart digitization), and the `CONTEXT.md` glossary (Exhibit Semantics, Semantic Confidence, Source Reference Rule).

## Goals / Non-Goals

**Goals:**

- Freeze `exhibit-semantics/v1`: exhibit `id`/`type`/`source_refs` plus confidence-tagged `semantic_hints`.
- Deterministic classification into the six exhibit types from source-document facts only.
- Every claim carries a source reference; uncertainty is expressed as `hint`/`mixed`, never fabricated certainty.

**Non-Goals:**

- Full table role semantics, grouped-header parsing, financial number parsing, arithmetic checks (change 4).
- No-grid hierarchy inference (change 5); chart digitization (change 6 / ADR-0002).
- Exporter or `case_spec.json` changes.

## Decisions

### Deterministic rule-based classifier over a model

Classify exhibits with deterministic rules over source-document structure (presence of a cell grid, column-span hints, figure blocks, caption proximity) rather than an ML model.
Rationale: deterministic rules give repeatable, repo-owned test outcomes (`ROADMAP.md` verification plan) and avoid a heavy dependency. Foundation scope only needs coarse typing.
Alternative considered: ML classifier — rejected as over-engineering and non-deterministic for CI.

### Reuse the change-2 validator as the input gate

Call `source_document_schema.validate_source_document` before interpreting, and fail fast on a non-conforming input.
Rationale: keeps ADR-0001 boundary enforcement in one place and guarantees the extractor never sees provider-native schema.
Alternative considered: re-validate inline — rejected as duplication.

### Hints carry confidence and source_refs; no anchorless claims

Every emitted hint is a structured object with `confidence` (from the fixed vocabulary) and `source_refs`. A candidate claim without an anchor is dropped, not emitted.
Rationale: enforces the `CONTEXT.md` Source Reference Rule mechanically and keeps interpretation auditable.

## Implementation Contract

- **Behavior**: `python3 scripts/extract_exhibit_semantics.py SOURCE_DOC --output PATH` validates the input as `source-document/v1`, classifies each table/figure into an exhibit, and writes `exhibit_semantics.json`. Non-conforming input exits non-zero with field-path errors and writes nothing.
- **Interface / data shape**: output `{schema_version: "exhibit-semantics/v1", exhibits: [{id, type, source_refs: [...], title?, semantic_hints: [{kind, value, confidence, source_refs}], checks: []}]}`. `type` ∈ {grid_table, matrix_table, financial_statement, hierarchy_table, chart, mixed}; `confidence` ∈ {observed, inferred, verified, hint, rejected}. A reusable function `extract_exhibit_semantics(source_doc) -> dict` backs the CLI.
- **Failure modes**: invalid source document → non-zero, field-path errors, no output; unknown/weak classification → `mixed` or `hint` confidence, never a guessed concrete type; chart exhibits carry no numeric series.
- **Acceptance criteria**: spec scenarios in `specs/exhibit-semantics/spec.md` hold against the committed `tests/fixtures/source_document_v1_real.json` (a grid table) plus hand-built fixtures for figure/matrix/financial cues; `python3 -m unittest discover -s tests` stays green.
- **Scope boundaries**: in scope — input gating, coarse classification, source-ref + confidence-tagged hints, output contract. Out of scope — full table/hierarchy semantics, arithmetic, chart digitization, exporters.

## Risks / Trade-offs

- [Coarse classifier mislabels a borderline exhibit] → resolve weak evidence to `mixed`/`hint` rather than a wrong concrete type; change 4/5 refine within the frozen anchor shape.
- [exhibit-semantics/v1 shape churns and breaks downstream] → keep the v1 field set minimal (id/type/source_refs/semantic_hints/checks); additive fields only after acceptance.

## Migration Plan

Additive — new script, new `exhibit-semantics/v1` artifact, new tests. No change to the adapter, validator output, exporters, or `case_spec.json`. Rollback is deletion of the new files.

## Open Questions

- The full `semantic_hints.kind` vocabulary (column-span, subtotal-candidate, …) is finalized by change 4; this foundation emits only a classification hint and leaves `checks` empty.
