## Why

Matrix and financial exhibits carry meaning in grouped headers, cell roles, signs, and subtotals that a flat classification cannot express; flattening them into Markdown columns loses that structure (`ROADMAP.md` "Matrix table with grouped headers", "Financial statement table").
This change adds full table semantics over the exhibit-semantics foundation.

> Maturity: draft. Dependencies: `exhibit-semantics-foundation`. Do not implement until `exhibit_semantics.json` exhibit anchors and confidence fields are stable.

## What Changes

- Implement grouped-header table support: classify `column_group_header`, `column_header`, `row_header`, and `data` cells and preserve nested column hierarchy with `col_span`.
- Preserve long-text cells, merged headers, blank-cell handling, and row/column spans.
- Parse currency, percentages, ranges, commas, and parenthesized negatives.
- Detect subtotal and total candidates and emit arithmetic validation results where formulas are explicit or inferable.

## Non-Goals

- No-grid hierarchy inference (`hierarchy-no-grid-semantics`).
- Chart and figure handling (`chart-figure-preservation`).
- Case-spec exporter rendering (`export-source-ref-rendering`).

## Capabilities

### New Capabilities

- `table-semantics`: grouped-header and financial-statement table interpretation that classifies cell roles, parses financial number formats, and attaches subtotal/total and arithmetic-check results to exhibit anchors, all preserving source references.

### Modified Capabilities

<!-- May extend exhibit-semantics during implementation; recorded as a delta then if behavior changes. -->

## Impact

- Extends the exhibit-semantics interpretation layer; depends on stable `exhibit-semantics/v1` anchors.
- Provides the financial-exhibit semantics that `case-spec-source-refs` evidence can cite.
- No exporter or `case_spec.json` change in this change.
