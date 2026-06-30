# source-document-validation Specification

## Purpose

TBD - created by archiving change 'source-document-schema-validation'. Update Purpose after archive.

## Requirements

### Requirement: source-document/v1 structural validation

The validator SHALL accept a parsed `source_document.json` and confirm it declares `schema_version` `source-document/v1` and contains every required field defined by the contract.
Required top-level fields MUST include `schema_version`, `source.path`, `source.mime_type`, `source.provider`, `source.provider_version`, `source.ingested_at`, `source.docling_command`, `pages`, `tables`, `figures`, and `notes`.
Each page MUST carry `page_number`, `width`, and `height`; each block MUST carry `id`, `self_ref`, `type`, `label`, `text`, `page_number`, `bbox`, `parent_ref`, `child_refs`, and `confidence`.
On failure the validator MUST return a structured error naming the offending field path.

#### Scenario: Valid document passes

- **WHEN** a `source_document.json` carrying all required fields is validated
- **THEN** the validator returns success with no errors

#### Scenario: Missing field is named

- **WHEN** a document omits a required top-level, page, or block field
- **THEN** the validator returns failure and the error names the offending field path

##### Example: page missing height

- **GIVEN** a document whose `pages[0]` has `page_number` and `width` but no `height`
- **WHEN** the document is validated
- **THEN** the result is failure with an error referencing `pages[0].height`

---
### Requirement: Facts-only constraint enforcement

The validator SHALL reject a `source_document.json` that carries business interpretation, accounting interpretation, chart digitization conclusions, subtotal meaning, or EMBA analysis claims, because `source-document/v1` records observed facts only (`CONTEXT.md` "Source Document").
Interpretation MUST be detected through reserved interpretation keys that belong to `exhibit_semantics.json`, not the source document.

#### Scenario: Interpretation key rejected

- **WHEN** a block or table carries an interpretation field such as a subtotal-meaning or exhibit-classification key
- **THEN** the validator returns failure identifying the interpretation field as not allowed in source-document/v1

#### Scenario: Observed facts allowed

- **WHEN** a document records only observed facts (text, bbox, cells, captions, headers, footers, notes, provenance)
- **THEN** the validator returns success

---
### Requirement: Deterministic repo-owned fixtures

This change SHALL provide deterministic, repo-owned fixtures covering pages, blocks, bbox values, table cells, captions, headers, footers, and source notes, and MUST NOT require real EMBA case PDFs for pass/fail acceptance.
At least one generated PDF fixture MUST contain a title, section header, paragraph, table, caption, page header, and page footer.

#### Scenario: Fixtures drive validation tests

- **WHEN** the validation test suite runs
- **THEN** it loads only repo-owned deterministic fixtures
- **AND** no test depends on a real EMBA case PDF

#### Scenario: Generated PDF fixture coverage

- **WHEN** the generated PDF fixture is ingested and validated
- **THEN** the resulting source document exercises pages, a table with cells, a caption, a page header, and a page footer
