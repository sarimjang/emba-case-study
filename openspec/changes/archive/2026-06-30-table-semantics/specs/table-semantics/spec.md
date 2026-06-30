## ADDED Requirements

### Requirement: Cell role classification with grouped headers

The table semantics layer SHALL classify each source table cell into a role of `column_group_header`, `column_header`, `row_header`, or `data`, preserving `col_span` and `row_span`.
A header cell that spans more than one column MUST be classified `column_group_header`; a single-column header cell MUST be `column_header`; a row-axis header cell MUST be `row_header`; all other cells MUST be `data`.
Long text cells, merged headers, and blank cells MUST be preserved rather than dropped.

#### Scenario: Grouped column header detected

- **WHEN** a header cell spans two or more columns
- **THEN** its role is `column_group_header` and its `col_span` is preserved

#### Scenario: Leaf header and data separated

- **WHEN** a single-column header cell and a body cell are classified
- **THEN** the header cell role is `column_header` and the body cell role is `data`

#### Scenario: Blank cell preserved

- **WHEN** a table contains a blank cell
- **THEN** the blank cell is retained with role `data` and empty text

### Requirement: Financial amount parsing

The layer SHALL parse cell amounts covering currency symbols, thousands separators, percentages, value ranges, and parenthesized negatives.
A parenthesized amount such as `(500)` MUST parse to a negative value.
A value range such as `70.0-80.0` MUST parse to a range with low and high bounds.
A cell that is not a parseable amount MUST be left without a parsed value rather than coerced.

#### Scenario: Parenthesized negative parsed

- **WHEN** a cell contains `(500)`
- **THEN** the parsed value is `-500.0`

##### Example: amount parsing table

- **GIVEN** cells `$2,000`, `(500)`, `15%`, and `70.0-80.0`
- **WHEN** amounts are parsed
- **THEN** the results are `2000.0`, `-500.0`, a percent value `15.0`, and a range `[70.0, 80.0]`

#### Scenario: Non-amount left unparsed

- **WHEN** a cell contains free text that is not a number
- **THEN** no numeric value is attached to that cell

### Requirement: Subtotal and total candidate detection

The layer SHALL mark rows whose row-header text indicates a subtotal or total as subtotal/total candidates, recording each as a semantic hint with a source reference.
Detection MUST be expressed as a candidate hint, not an asserted fact, when it is inferred from row-label text.

#### Scenario: Total row marked as candidate

- **WHEN** a row header text matches a total or subtotal label
- **THEN** a subtotal/total candidate hint is emitted with a `source_refs` entry

### Requirement: Arithmetic validation where inferable

The layer SHALL emit an arithmetic check for a total candidate when the column's data values are parseable and their sum is comparable to the total cell value.
A check whose sum matches the stated total MUST be recorded with confidence `verified`; a mismatch MUST be recorded with confidence `rejected`; an unparseable column MUST NOT produce a check.

#### Scenario: Matching total verified

- **WHEN** the data values in a column sum to the stated total value
- **THEN** an arithmetic check is recorded with confidence `verified`

#### Scenario: Mismatched total rejected

- **WHEN** the data values do not sum to the stated total
- **THEN** an arithmetic check is recorded with confidence `rejected`

#### Scenario: Unparseable column produces no check

- **WHEN** a column's values cannot all be parsed as amounts
- **THEN** no arithmetic check is emitted for that column
