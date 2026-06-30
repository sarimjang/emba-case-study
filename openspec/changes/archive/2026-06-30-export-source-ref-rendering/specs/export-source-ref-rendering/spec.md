## ADDED Requirements

### Requirement: Shared evidence rendering helper

A single shared helper SHALL convert an evidence item — a legacy string or a structured evidence object — into display text, so the Markdown, DOCX, and PPTX generators render evidence consistently.
A legacy string item MUST render exactly as its own text, unchanged.
A structured evidence object MUST render its `text` first, and MUST append its `source_refs` when present.

#### Scenario: Legacy string renders unchanged

- **WHEN** an evidence item is a plain string
- **THEN** the rendered text equals that string with no added decoration

#### Scenario: Structured object renders text then references

- **WHEN** an evidence item is a structured object with `text` and `source_refs`
- **THEN** the rendered text begins with the object's `text`
- **AND** the source references appear after the text

##### Example: structured evidence rendering

- **GIVEN** an item `{"text": "Valves carry the highest margin.", "source_refs": ["exhibit-1"]}`
- **WHEN** it is rendered
- **THEN** the output contains `Valves carry the highest margin.` followed by `exhibit-1`

#### Scenario: Structured object without references

- **WHEN** a structured object has `text` but no `source_refs`
- **THEN** only the `text` is rendered, with no empty reference decoration

### Requirement: Generators render structured evidence across formats

The Markdown, DOCX, and PPTX generators SHALL render structured evidence and its source references wherever they render evidence and appendix list fields, using the shared helper.
Existing all-string case specs MUST produce unchanged output, and the generators MUST NOT read Docling raw JSON (`docs/adr/0001-keep-docling-raw-json-out-of-public-contract.md`).

#### Scenario: All three formats render a structured item

- **WHEN** a case spec carries a structured evidence item and each generator runs
- **THEN** the Markdown, DOCX, and PPTX outputs each contain the item's text and its reference

#### Scenario: Legacy spec output unchanged

- **WHEN** a legacy all-string case spec is rendered
- **THEN** the generated output is identical to the pre-change output
