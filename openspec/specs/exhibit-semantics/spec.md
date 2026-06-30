# exhibit-semantics Specification

## Purpose

TBD - created by archiving change 'exhibit-semantics-foundation'. Update Purpose after archive.

## Requirements

### Requirement: Reads validated source document only

The extractor SHALL accept a `source_document.json` that conforms to `source-document/v1` and MUST NOT read Docling raw JSON or any provider-native schema (`docs/adr/0001-keep-docling-raw-json-out-of-public-contract.md`).
When the input fails `source-document/v1` validation, the extractor MUST exit non-zero with the structured field-path errors and emit no `exhibit_semantics.json`.

#### Scenario: Non-conforming source document rejected

- **WHEN** the input document fails `source-document/v1` validation
- **THEN** the extractor exits non-zero and reports the offending field path
- **AND** no `exhibit_semantics.json` is written

#### Scenario: Conforming source document accepted

- **WHEN** a valid `source-document/v1` document is supplied
- **THEN** the extractor produces an `exhibit_semantics.json` artifact

---
### Requirement: Emits exhibit-semantics/v1 with classified exhibits

The extractor SHALL emit `exhibit_semantics.json` declaring `schema_version` `exhibit-semantics/v1` and an `exhibits` array.
Each exhibit MUST carry an `id`, a `type`, and a `source_refs` array.
The `type` MUST be one of `grid_table`, `matrix_table`, `financial_statement`, `hierarchy_table`, `chart`, or `mixed`.

#### Scenario: Table classified as a known exhibit type

- **WHEN** the source document contains a table with a cell grid
- **THEN** the output contains an exhibit whose `type` is one of the six allowed values
- **AND** the exhibit carries a non-empty `source_refs` array

##### Example: grid table classification

- **GIVEN** a source document with one table that has rows, columns, and a caption
- **WHEN** exhibit semantics are extracted
- **THEN** an exhibit with `type` `grid_table` is emitted referencing the table's `self_ref`

#### Scenario: Figure classified as chart

- **WHEN** the source document contains a figure block
- **THEN** an exhibit with `type` `chart` is emitted referencing the figure
- **AND** no numeric chart series values are produced

---
### Requirement: Source reference for every semantic claim

The extractor SHALL attach a `source_refs` entry to every exhibit and every semantic hint it emits, referencing the originating `source_document.json` anchor (a block, table, or figure `self_ref`).
A semantic claim without a source reference MUST NOT be emitted.

#### Scenario: Hint carries a source reference

- **WHEN** the extractor emits a semantic hint about an exhibit
- **THEN** the hint includes a `source_refs` entry pointing at a `source_document.json` anchor

#### Scenario: Anchorless claim suppressed

- **WHEN** a candidate claim cannot be tied to a source anchor
- **THEN** the extractor omits the claim rather than emitting it without a reference

---
### Requirement: Semantic confidence vocabulary

Every semantic hint SHALL declare a `confidence` drawn from the fixed vocabulary `observed`, `inferred`, `verified`, `hint`, or `rejected` (`CONTEXT.md` "Semantic Confidence").
A value copied directly from source-document facts MUST use `observed`; a value derived from layout, proximity, labels, or formatting MUST use `inferred` or `hint`.
The extractor MUST NOT emit a confidence value outside this vocabulary.

#### Scenario: Inferred classification tagged

- **WHEN** an exhibit type is derived from layout rather than copied from a source fact
- **THEN** the related hint declares `confidence` `inferred` or `hint`

#### Scenario: Invalid confidence rejected

- **WHEN** the output is validated
- **THEN** every `confidence` value is one of the six allowed tokens

---
### Requirement: Conservative interpretation, no overclaim

The extractor SHALL emit semantic hints rather than asserting certainty, and MUST NOT digitize chart numeric series or assert subtotal meaning, arithmetic validation, or full table role semantics in this foundation scope (`docs/adr/0002-defer-chart-digitization.md`).

#### Scenario: Chart values not fabricated

- **WHEN** an exhibit is classified as `chart`
- **THEN** the exhibit records no plotted numeric series values

#### Scenario: Uncertain classification downgraded to hint

- **WHEN** classification evidence is weak
- **THEN** the exhibit type resolves to `mixed` or the classification hint uses `hint` confidence
