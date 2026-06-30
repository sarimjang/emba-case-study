# case-spec-source-refs Specification

## Purpose

TBD - created by archiving change 'case-spec-source-refs'. Update Purpose after archive.

## Requirements

### Requirement: Backward-compatible structured evidence

Evidence and reference fields that today accept string arrays SHALL also accept structured evidence objects, while legacy string items remain valid and unchanged.
The affected fields MUST include `evidence.quantitative_signals`, `evidence.internal_checks`, `evidence.external_checks`, `evidence.open_issues`, `case.source_notes`, `appendix.references`, `appendix.assumptions`, and `appendix.discussion_questions`.
A list item that is neither a string nor a structured evidence object MUST be rejected.

#### Scenario: Legacy string evidence still valid

- **WHEN** an evidence field contains only strings
- **THEN** validation succeeds and the items are unchanged

#### Scenario: Structured and string items may coexist

- **WHEN** an evidence field mixes a legacy string and a structured evidence object
- **THEN** validation succeeds

#### Scenario: Non-string non-object item rejected

- **WHEN** an evidence field contains an item that is neither a string nor an object
- **THEN** validation fails naming the offending field path

---
### Requirement: Structured evidence object shape

A structured evidence object SHALL contain a non-empty `text` string and MAY contain `source_refs`, `confidence`, and `evidence_type`.
When present, `source_refs` MUST be an array of non-empty strings.
When present, `confidence` MUST be one of `observed`, `inferred`, `verified`, `hint`, or `rejected`.

#### Scenario: Valid structured object accepted

- **WHEN** an evidence object has non-empty `text` and an array `source_refs`
- **THEN** validation succeeds

#### Scenario: Empty text rejected

- **WHEN** an evidence object has an empty or missing `text`
- **THEN** validation fails naming the offending field path

#### Scenario: Invalid confidence rejected

- **WHEN** an evidence object declares a `confidence` outside the fixed vocabulary
- **THEN** validation fails naming the offending field path

---
### Requirement: Source Reference Rule enforcement

A structured evidence object that interprets an exhibit (marked by `evidence_type` of `exhibit_interpretation` or `interprets_exhibit: true`) SHALL cite at least one `exhibit_semantics.json` anchor, because interpreted exhibit claims must not rest on raw source-document facts alone (`CONTEXT.md` "Source Reference Rule").
An evidence object MUST NOT embed layout or OCR data; reserved layout keys such as `bbox`, `cells`, and `page_number` are not allowed in `case_spec.json` evidence.

#### Scenario: Interpretation claim requires exhibit anchor

- **WHEN** an evidence object marks itself as interpreting an exhibit but its `source_refs` cite only source-document anchors
- **THEN** validation fails indicating an exhibit-semantics anchor is required

#### Scenario: Observed fact may cite source-document anchor

- **WHEN** an evidence object is a plain observed fact citing a source-document anchor
- **THEN** validation succeeds

#### Scenario: Embedded layout rejected

- **WHEN** an evidence object carries a reserved layout key such as `bbox` or `cells`
- **THEN** validation fails naming the disallowed key
