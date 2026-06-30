## Context

`exhibit-semantics-foundation` classifies tables coarsely (grid/matrix/financial/mixed) but emits only a classification hint. This change adds the detailed table semantics the roadmap Phase 4 calls for: cell roles, financial number parsing, subtotal/total detection, and arithmetic checks — all enriching the existing `exhibit-semantics/v1` exhibits, citing source anchors, and using the fixed confidence vocabulary.
Inputs are Docling-normalized table cells, which carry `start/end_row_offset_idx`, `start/end_col_offset_idx`, `row_span`, `col_span`, `column_header`, and `row_header` flags.

## Goals / Non-Goals

**Goals:**

- Deterministic cell-role classification with grouped-header support, preserving spans and blank/long-text cells.
- Robust financial amount parsing (currency, commas, percent, ranges, parenthesized negatives).
- Conservative subtotal/total detection as candidate hints, with arithmetic checks only where columns are fully parseable.

**Non-Goals:**

- No-grid hierarchy inference (change 5); chart handling (change 6); exporter/`case_spec.json` changes (changes 7–8).
- Asserting accounting meaning beyond a parseable arithmetic check.

## Decisions

### Standalone table_semantics module enriching exhibit hints

Implement `scripts/table_semantics.py` with pure functions (`classify_cell_roles`, `parse_amount`, `detect_subtotal_total_candidates`, `arithmetic_checks`) and have `extract_exhibit_semantics` enrich grid/matrix/financial exhibits by calling it.
Rationale: keeps the foundation classifier small and the table logic independently testable; downstream changes import the same parsers.
Alternative considered: inline everything in the extractor — rejected; harms testability and reuse.

### Amount parsing returns a typed result, never a coerced guess

`parse_amount(text)` returns a structured result (`kind` ∈ number/percent/range, value(s)) or `None` when the text is not an amount. Parenthesized values are negative; ranges yield low/high bounds.
Rationale: the Source Reference Rule and ADR-0002 conservatism require not fabricating values; unparseable cells stay unparsed.

### Arithmetic checks are evidence-gated

An arithmetic check is emitted only when every data value in the column parses; a matching sum is `verified`, a mismatch is `rejected`, an unparseable column yields no check.
Rationale: matches the `CONTEXT.md` confidence semantics (`verified` requires arithmetic support) and avoids false precision.

## Implementation Contract

- **Behavior**: for each grid/matrix/financial exhibit, `extract_exhibit_semantics` output gains: per-cell `role` annotations (preserving spans), parsed amounts where present, subtotal/total candidate hints, and arithmetic `checks` entries. Chart/mixed exhibits are unchanged.
- **Interface / data shape**: `table_semantics.classify_cell_roles(table) -> list[dict]` (each cell + `role` ∈ {column_group_header, column_header, row_header, data}); `parse_amount(str) -> dict|None` (`{kind, value}` or `{kind: "range", low, high}`); `detect_subtotal_total_candidates(roled_cells) -> list[hint]`; `arithmetic_checks(roled_cells) -> list[check]` where a check is `{kind: "arithmetic", column, sum, total, confidence}`. Exhibit `semantic_hints` gain role/subtotal hints (each with `source_refs` + `confidence`); `checks` gains arithmetic results.
- **Failure modes**: non-amount cells → no parsed value; unparseable column → no check; weak/ambiguous role → `data`. Nothing is coerced or guessed.
- **Acceptance criteria**: spec scenarios in `specs/table-semantics/spec.md` hold against hand-built deterministic fixtures (grouped header, financial column with a total, mixed text) and the committed real source_document fixture; `python3 -m unittest discover -s tests` stays green.
- **Scope boundaries**: in scope — cell roles, amount parsing, subtotal/total candidates, arithmetic checks, enriched hints/checks. Out of scope — no-grid hierarchy, charts, exporters, case_spec.

## Risks / Trade-offs

- [Grouped-header heuristics misread an irregular header band] → fall back to `column_header`/`data`; spans are still preserved so change 5+ can refine.
- [Locale-specific number formats beyond the parsed set] → `parse_amount` returns `None` (unparsed) rather than a wrong value; extend the parser as real fixtures demand.

## Migration Plan

Additive — new `table_semantics` module, enrichment inside the existing extractor, new tests. The `exhibit-semantics/v1` shape gains optional hint kinds and `checks` entries; existing fields are unchanged. Rollback is removing the module and the enrichment call.

## Open Questions

- Multi-level (3+ deep) nested column hierarchies are represented via spans + group/leaf roles only in this change; deeper nesting semantics, if needed, are a later refinement within the same anchor shape.
