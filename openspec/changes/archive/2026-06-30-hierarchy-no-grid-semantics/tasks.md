## 1. Module and indent inference

- [x] 1.1 Create the Standalone hierarchy_semantics module over block bboxes (`scripts/hierarchy_semantics.py`) implementing Left-edge clustering with tolerance, leftmost = level 0, satisfying the Indentation level inference from bbox clusters requirement: `infer_indent_levels(blocks, tol)` clusters bbox left edges into ordered levels; blocks without a bbox default to level 0. Behavior: two left-edge clusters map to levels 0 and 1; a bbox-less block is retained at level 0. Verify: unit tests for the two-level and missing-bbox scenarios.

## 2. Parent-child and parsing

- [x] 2.1 Implement Parent-child mapping for category headings: `build_parent_child(blocks_with_levels)` maps each block to the nearest preceding shallower block as parent, emitted as `hint`-confidence hints with source refs; top-level blocks have no parent. Behavior: an indented row's parent is the preceding heading; a shallowest block has none. Verify: unit tests for the child-mapped and top-level-no-parent scenarios.
- [x] 2.2 Implement Value and percentage range parsing: `parse_range(text)` reuses the shared amount parser so `70.0-80.0` yields a range with low/high; non-ranges return None. Behavior: a percentage range parses to bounds; prose returns None. Verify: unit test for the percentage-range scenario.

## 3. Notes and conservative exhibit construction

- [x] 3.1 Implement Footnote and source-note association: `associate_notes(blocks)` links each footnote/source-note block to the nearest preceding non-note block as a hint with a source reference. Behavior: a source-note block is associated with the preceding exhibit block. Verify: unit test for the note-attached scenario.
- [x] 3.2 Implement Conservative exhibit trigger to avoid spurious hierarchies, satisfying the Conservative hierarchy exhibit construction requirement: `hierarchy_exhibit_from_blocks` emits a `hierarchy_table` exhibit only when a page has >=2 indent levels and >=1 leaf parsing as a range/amount; integrate into `extract_exhibit_semantics`. Behavior: an indented value breakdown yields a hierarchy exhibit with parent-child hints; a prose-only page and the committed grid-table fixture yield none. Verify: unit tests for the hierarchy-built and prose-no-exhibit scenarios, plus a regression assertion on the real fixture.

## 4. Regression

- [x] 4.1 Confirm no regression across the suite. Behavior: existing extractor/table/export tests stay green alongside the new hierarchy tests. Verify: `python3 -m unittest discover -s tests` exits OK.
