## Why

Once `source_document.json` is frozen and validated, the pipeline needs an interpretation layer that explains what an exhibit appears to mean without polluting the facts-only source document (`CONTEXT.md` "Exhibit Semantics").
This change adds that foundation so table, hierarchy, chart, and case-spec changes have stable exhibit anchors and a shared confidence vocabulary to cite.

> Maturity: draft. Dependencies: `source-document-schema-validation` (and the `source-document/v1` shape it freezes). Do not implement until the upstream anchor format and minimum table/figure shapes are stable (`ROADMAP.md` "Maturity and dependency policy").

## What Changes

- Add `scripts/extract_exhibit_semantics.py` that reads `source_document.json` (never Docling raw JSON, per `docs/adr/0001-keep-docling-raw-json-out-of-public-contract.md`) and emits `exhibit_semantics.json` (`schema_version: exhibit-semantics/v1`).
- Classify each exhibit as `grid_table`, `matrix_table`, `financial_statement`, `hierarchy_table`, `chart`, or `mixed`.
- Preserve a source reference back to `source_document.json` for every semantic claim.
- Apply the semantic confidence vocabulary `observed`, `inferred`, `verified`, `hint`, `rejected` (`CONTEXT.md` "Semantic Confidence").
- Emit semantic hints rather than overclaiming certainty.

## Non-Goals

- Full table semantics, full hierarchy parsing, and chart digitization (later changes / `docs/adr/0002-defer-chart-digitization.md`).
- Exporter migration and `case_spec.json` changes.
- Reading Docling raw JSON directly.

## Capabilities

### New Capabilities

- `exhibit-semantics`: a deterministic classifier over validated source-document facts that produces `exhibit_semantics.json` with exhibit types, per-claim source references, and confidence-tagged hints — the interpretation anchor that downstream semantic and analysis changes cite.

### Modified Capabilities

<!-- None yet; introduces a new interpretation layer. -->

## Impact

- New file: `scripts/extract_exhibit_semantics.py`; new contract `exhibit-semantics/v1`.
- Freezes the exhibit-anchor and confidence-field formats that unblock changes 4, 5, 6, and 7 from draft.
- No exporter or `case_spec.json` impact in this change.
