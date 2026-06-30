## Why

Many EMBA exhibits (e.g. restaurant economics) use indentation and category headings instead of grid lines, so parent-child structure must be inferred from layout rather than table borders (`ROADMAP.md` "Hierarchy table without full grid lines").
This change adds borderless-hierarchy semantics while keeping uncertain assignments honest.

> Maturity: draft. Dependencies: `source-document-schema-validation`, `exhibit-semantics-foundation`. Do not implement until bbox normalization and source-note anchoring are stable.

## What Changes

- Infer indentation levels from horizontal bbox clusters and map category headings to child rows.
- Classify section headers and leaf rows; preserve parent-child row relationships.
- Support percentage ranges and value ranges (e.g. `70.0-80.0`).
- Associate footnotes and source notes with the nearest exhibit.
- Keep uncertain hierarchy assignments as semantic `hint` confidence rather than hard facts.

## Non-Goals

- Financial arithmetic validation unless already provided by `table-semantics`.
- Chart digitization (`docs/adr/0002-defer-chart-digitization.md`).
- Exporter migration.

## Capabilities

### New Capabilities

- `hierarchy-no-grid-semantics`: indentation-derived hierarchy interpretation for borderless exhibits that preserves parent-child structure, parses value ranges, anchors nearby notes, and downgrades uncertain mappings to hints, all citing source references.

### Modified Capabilities

<!-- None; standalone interpretation extension over exhibit-semantics anchors. -->

## Impact

- Depends on stable bbox normalization (`source-document/v1`) and exhibit anchors (`exhibit-semantics/v1`).
- No exporter or `case_spec.json` change in this change.
