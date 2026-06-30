## Context

`exhibit-semantics-foundation` classifies tables and figures but has no path for borderless hierarchy exhibits (e.g. restaurant-economics breakdowns: category headings + indented child rows + value ranges), which Docling tends to emit as text blocks rather than a grid table. This change adds indentation-derived hierarchy inference over source blocks, reusing the shared amount parser from `table-semantics`, and constructs `hierarchy_table` exhibits conservatively.
Binding constraints: source-document facts only as input (ADR-0001), source anchors + the fixed confidence vocabulary, and no chart digitization.

## Goals / Non-Goals

**Goals:**

- Infer indent levels from bbox left-edge clustering and map category headings to child rows.
- Parse value/percentage ranges; associate footnotes/source notes with the nearest exhibit block.
- Construct `hierarchy_table` exhibits only on strong evidence; keep uncertain structure as `hint`.

**Non-Goals:**

- Financial arithmetic (owned by `table-semantics`); chart handling (change 6); exporter/`case_spec.json` changes.
- Reclassifying real grid tables as hierarchies.

## Decisions

### Standalone hierarchy_semantics module over block bboxes

Implement `scripts/hierarchy_semantics.py` with pure functions (`infer_indent_levels`, `build_parent_child`, `parse_range`, `associate_notes`, `hierarchy_exhibit_from_blocks`) operating on `source-document/v1` page blocks.
Rationale: independent, deterministic, testable without Docling; the extractor calls it for page-level text structure the table path does not cover.
Alternative considered: fold into `table_semantics` — rejected; hierarchy works over blocks, not table cells.

### Left-edge clustering with tolerance, leftmost = level 0

Cluster block bbox left edges (`bbox[0]`) within a tolerance into ordered levels; blocks without a bbox default to level 0.
Rationale: indentation is the borderless-exhibit signal; tolerance absorbs OCR jitter. Reuses `table_semantics.parse_amount` for ranges.

### Conservative exhibit trigger to avoid spurious hierarchies

Emit a `hierarchy_table` exhibit only when a page shows >=2 distinct indent levels AND >=1 leaf parses as a range/amount; otherwise emit nothing.
Rationale: prevents ordinary prose pages from producing false hierarchy exhibits; uncertain structure stays a `hint`.

## Implementation Contract

- **Behavior**: for a page whose blocks form an indented value breakdown, `extract_exhibit_semantics` gains a `hierarchy_table` exhibit with parent-child and note-association hints (each with `source_refs` and confidence). Prose-only pages and the committed grid-table fixture produce no hierarchy exhibit.
- **Interface / data shape**: `infer_indent_levels(blocks, tol=4.0) -> {block_id: level}`; `build_parent_child(blocks_with_levels) -> [{block_id, parent_id|None}]`; `parse_range(text) -> {kind: range|percent|number, ...}|None`; `associate_notes(blocks) -> [{note_id, exhibit_id}]`; `hierarchy_exhibit_from_blocks(blocks, source_ref) -> dict|None`. Exhibit shape matches `exhibit-semantics/v1` (`id`, `type: hierarchy_table`, `source_refs`, `semantic_hints` with `kind` in {indent_hierarchy, note_association}, confidence `hint`, `checks: []`).
- **Failure modes**: missing bbox → level 0 (retained); non-range/amount leaf → unparsed; insufficient evidence → no exhibit (None). Nothing coerced or guessed.
- **Acceptance criteria**: spec scenarios hold against hand-built block fixtures (heading + indented value rows; prose-only); the committed real source_document fixture yields no `hierarchy_table` exhibit; `python3 -m unittest discover -s tests` passes.
- **Scope boundaries**: in scope — hierarchy module, conservative integration, tests. Out of scope — arithmetic, charts, exporters, case_spec.

## Risks / Trade-offs

- [Left-edge clustering misreads multi-column layouts] → require >=2 levels + a parsed leaf before emitting; otherwise emit nothing, so false positives stay rare.
- [Integration changes extractor output on real inputs] → conservative trigger plus a regression test asserting the grid-table fixture produces no hierarchy exhibit.

## Migration Plan

Additive — new module, conservative enrichment in the extractor, new tests. Existing exhibit output for tables/figures is unchanged. Rollback is removing the module and the integration call.

## Open Questions

- Deeply nested (3+ level) hierarchies are represented by level integers and nearest-shallower-parent mapping; richer nesting semantics can refine later within the same hint shape.
