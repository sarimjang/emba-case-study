## ADDED Requirements

### Requirement: Indentation level inference from bbox clusters

The hierarchy layer SHALL infer indentation levels for a sequence of source blocks by clustering their bounding-box left edges within a tolerance, assigning level 0 to the leftmost cluster and increasing levels to deeper indents.
Blocks lacking a usable bbox MUST default to level 0 rather than being dropped.

#### Scenario: Two indent levels detected

- **WHEN** blocks have left edges grouped into two clusters
- **THEN** the leftmost cluster maps to level 0 and the indented cluster to level 1

##### Example: heading and child rows

- **GIVEN** a heading at left edge 72 and two rows at left edge 96
- **WHEN** indent levels are inferred
- **THEN** the heading is level 0 and the two rows are level 1

#### Scenario: Missing bbox defaults to level zero

- **WHEN** a block has no bbox
- **THEN** it is assigned level 0 and retained

### Requirement: Parent-child mapping for category headings

The layer SHALL map each block to the nearest preceding block at a shallower level as its parent, so category headings own the indented rows beneath them.
Uncertain assignments MUST be expressed as semantic hints with `hint` confidence and a source reference, not as asserted facts.

#### Scenario: Child row mapped to heading

- **WHEN** an indented row follows a shallower heading
- **THEN** the row's parent is that heading
- **AND** the relationship is emitted as a hint with a source reference

#### Scenario: Top-level block has no parent

- **WHEN** a block is at the shallowest level
- **THEN** it has no parent

### Requirement: Value and percentage range parsing

The layer SHALL parse value ranges and percentage ranges such as `70.0-80.0` into low and high bounds, reusing the shared amount parser.
A block whose text is not a range or amount MUST be left without a parsed value.

#### Scenario: Percentage range parsed

- **WHEN** a block text is `70.0-80.0`
- **THEN** it parses to a range with low `70.0` and high `80.0`

### Requirement: Footnote and source-note association

The layer SHALL associate footnote and source-note blocks with the nearest preceding non-note block on the page, recording the association as a hint with a source reference.

#### Scenario: Note attached to nearest exhibit block

- **WHEN** a source-note block follows an exhibit block
- **THEN** the note is associated with that exhibit block via a hint

### Requirement: Conservative hierarchy exhibit construction

The layer SHALL only construct a `hierarchy_table` exhibit when a page exposes at least two distinct indent levels among its text blocks and at least one leaf parses as a range or amount; otherwise it MUST NOT emit a hierarchy exhibit.
Ordinary prose pages MUST NOT produce a spurious hierarchy exhibit.

#### Scenario: Hierarchy exhibit built from indented value rows

- **WHEN** a page has a heading plus indented rows whose leaves carry value ranges
- **THEN** a `hierarchy_table` exhibit is emitted with parent-child hints

#### Scenario: Prose page produces no hierarchy exhibit

- **WHEN** a page contains only flat prose blocks with no indented value rows
- **THEN** no `hierarchy_table` exhibit is emitted
