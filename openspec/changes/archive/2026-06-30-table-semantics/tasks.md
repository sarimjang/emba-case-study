## 1. Module and cell roles

- [x] 1.1 Create the Standalone table_semantics module enriching exhibit hints (`scripts/table_semantics.py`) providing Cell role classification with grouped headers: `classify_cell_roles(table)` assigns each cell `column_group_header` (header with col_span>1), `column_header`, `row_header`, or `data`, preserving spans and blank/long-text cells. Behavior: a multi-column header cell becomes `column_group_header` with its `col_span` intact; blank cells are retained as `data`. Verify: unit tests for the grouped-header, leaf-vs-data, and blank-cell scenarios.

## 2. Amount parsing

- [x] 2.1 Implement Amount parsing returns a typed result, never a coerced guess, satisfying the Financial amount parsing requirement: `parse_amount(text)` handles currency, commas, percent, ranges, and parenthesized negatives, returning a typed result or None. Behavior: `(500)` parses to `-500.0`; `70.0-80.0` parses to a range; free text returns None. Verify: unit tests for parenthesized-negative, range, percent, and non-amount-left-unparsed scenarios.

## 3. Subtotal/total and arithmetic

- [x] 3.1 Implement Subtotal and total candidate detection: `detect_subtotal_total_candidates(roled_cells)` marks rows whose row-header text matches a subtotal/total label as candidate hints with `source_refs`. Behavior: a total-labelled row yields a candidate hint, expressed as a candidate not an asserted fact. Verify: unit test for the total-row-marked scenario.
- [x] 3.2 Implement Arithmetic checks are evidence-gated, satisfying the Arithmetic validation where inferable requirement: `arithmetic_checks(roled_cells)` emits a check only when a column's data values all parse; a matching sum is `verified`, a mismatch is `rejected`, an unparseable column yields no check. Behavior: matching column sum → `verified`; mismatch → `rejected`; unparseable column → no check. Verify: unit tests for the matching, mismatched, and unparseable scenarios.

## 4. Integration and regression

- [x] 4.1 Enrich `extract_exhibit_semantics` grid/matrix/financial exhibits by calling the table_semantics module: add per-cell `role` annotations, subtotal/total candidate hints, and arithmetic `checks`, each carrying `source_refs` and a confidence from the fixed vocabulary; chart/mixed exhibits stay unchanged. Behavior: a financial exhibit gains role annotations and a verified/rejected arithmetic check; the committed real fixture still extracts. Verify: unit test on a financial fixture asserts roles + a check, and `python3 -m unittest discover -s tests` exits OK.
