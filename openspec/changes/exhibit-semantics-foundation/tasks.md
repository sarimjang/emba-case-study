## 1. Input gate

- [x] 1.1 Implement Reuse the change-2 validator as the input gate, satisfying the Reads validated source document only requirement: load the source document and run `source_document_schema.validate_source_document` before interpreting. Behavior: a non-conforming input exits non-zero with field-path errors and writes no output; a conforming input proceeds. Verify: unit tests for the rejected and accepted scenarios.

## 2. Classification and output contract

- [x] 2.1 Implement the Deterministic rule-based classifier over a model, satisfying Emits exhibit-semantics/v1 with classified exhibits: map each source table/figure to an exhibit with `id`, `type` (grid_table/matrix_table/financial_statement/hierarchy_table/chart/mixed), and `source_refs`. Behavior: a table with a cell grid yields a typed exhibit referencing its `self_ref`; a figure yields a `chart` exhibit. Verify: unit tests asserting type and source_refs on the committed grid-table fixture and a hand-built figure fixture.
- [x] 2.2 Emit `exhibit_semantics.json` declaring `schema_version` `exhibit-semantics/v1` with the `exhibits` array. Behavior: output parses and every exhibit carries id/type/source_refs. Verify: unit test loads the output and asserts the schema_version and per-exhibit fields.

## 3. Source refs and confidence

- [x] 3.1 Implement Hints carry confidence and source_refs; no anchorless claims, satisfying the Source reference for every semantic claim requirement: attach `source_refs` to every exhibit and hint, and drop any candidate claim lacking an anchor. Behavior: emitted hints reference a source anchor; anchorless candidates are suppressed. Verify: unit tests for the hint-carries-source-reference and anchorless-claim-suppressed scenarios.
- [x] 3.2 Enforce the Semantic confidence vocabulary requirement: every hint declares a `confidence` in {observed, inferred, verified, hint, rejected}; inferred-from-layout values use inferred/hint. Behavior: output contains no confidence value outside the vocabulary. Verify: unit test asserts all confidence tokens are in the allowed set.

## 4. Conservatism and regression

- [x] 4.1 Implement Conservative interpretation, no overclaim: chart exhibits record no numeric series; weak classification resolves to `mixed` or `hint`. Behavior: a figure-derived chart exhibit has no plotted values; an ambiguous table does not get a guessed concrete type. Verify: unit tests for the chart-values-not-fabricated and uncertain-classification-downgraded scenarios.
- [x] 4.2 Add a thin CLI (`scripts/extract_exhibit_semantics.py SOURCE_DOC --output PATH`) and run the full suite. Behavior: the CLI writes `exhibit_semantics.json` for a valid input and exits non-zero for an invalid one; prior tests stay green. Verify: subprocess test for both exit paths and `python3 -m unittest discover -s tests` exits OK.
