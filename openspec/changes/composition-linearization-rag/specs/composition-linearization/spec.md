## ADDED Requirements

### Requirement: Derived composition layer that never mutates canonical artifacts

The composition layer SHALL read `source-document/v1` and `exhibit-semantics/v1` and produce derived projections without writing to either canonical artifact. The derived output MUST be regenerable from the two inputs alone.

#### Scenario: Canonical inputs are left untouched

- **WHEN** the composition layer runs over a source document and its exhibit semantics
- **THEN** it emits derived reading-view and RAG-chunk projections
- **AND** neither `source_document.json` nor `exhibit_semantics.json` is modified

### Requirement: Native-order linearization with exhibit placeholders

The layer SHALL linearize a page using the source document's native block order as the spine, and SHALL insert each exhibit as a single placeholder anchor at its caption position, falling back to bounding-box position when the exhibit has no caption. The exhibit body MUST NOT be duplicated inline as prose.

#### Scenario: Exhibit placed at its caption position

- **WHEN** a page has prose blocks and a table whose caption is one of those blocks
- **THEN** the table appears as one placeholder anchor adjacent to its caption
- **AND** the surrounding prose keeps its native reading order

#### Scenario: Uncaptioned exhibit placed by bounding box

- **WHEN** an exhibit has no caption reference
- **THEN** the placeholder is inserted at the position implied by its bounding box among the native-order blocks

### Requirement: Conservative duplicate suppression

The layer SHALL suppress a prose block only when its text exactly equals a table cell on the same page AND its bounding-box center lies inside that table's bounding box. A block that fails either condition MUST be preserved.

#### Scenario: True duplicate suppressed

- **WHEN** a prose block's text equals a table cell and its center lies inside that table's bounding box
- **THEN** the prose block is suppressed and only the exhibit placeholder remains

#### Scenario: Distinct content preserved

- **WHEN** prose blocks share only a boilerplate suffix with a table's cells but sit outside the table's bounding box
- **THEN** the prose blocks are preserved and not treated as duplicates

### Requirement: Confidence-tiered Exhibit reference resolution

The layer SHALL resolve a prose "Exhibit N" reference to an exhibit using tiered evidence, and MUST tag each resolved link with a confidence from the fixed vocabulary: caption-carries-number as `verified`, prose description bridge as `inferred`, label-anchor geometry as `hint`, document-order sequence as `hint`. A reference with no qualifying evidence MUST be left unresolved rather than bound to the nearest exhibit.

#### Scenario: Description bridge binds the correct table

- **WHEN** prose names a description near "Exhibit N" that matches one exhibit's distinctive caption head unambiguously
- **THEN** that "Exhibit N" reference resolves to that exhibit with `inferred` confidence

#### Scenario: Ambiguous reference stays unresolved

- **WHEN** an "Exhibit N" reference has no caption-number, no unambiguous description match, and no separated nearest object
- **THEN** the reference is left unresolved

### Requirement: Anti-binding guards for label-anchor resolution

When binding a bare "Exhibit N" label to the nearest exhibit object, the layer SHALL reject the bind unless the nearest object is closer than a configured fraction of the runner-up distance, is within a configured fraction of the label's page height, and the object is not already bound to a different exhibit number.

#### Scenario: Sole distant object rejected

- **WHEN** a page has a single exhibit object and the label is farther than the page-height fraction from it
- **THEN** the label is left unresolved despite having no runner-up competitor

#### Scenario: Number conflict rejected

- **WHEN** the nearest object is already bound to a different exhibit number
- **THEN** the label does not bind to that object

### Requirement: Dual-type phantom signalling for undetected exhibits

The layer SHALL emit a phantom record when a reference resolves to a number with no registered exhibit, and MUST classify it as `mentioned-only` when only prose cites the number, or as `label-detected-object-undetected` when a label block names the exhibit but no object was detected.

#### Scenario: Labelled-but-undetected exhibit flagged for re-extraction

- **WHEN** a label block names "Exhibit N" but no table or figure object was detected for it
- **THEN** a phantom record of type `label-detected-object-undetected` is emitted with the label's region reference

### Requirement: RAG chunks preserve source references and relatedness

The layer SHALL emit RAG chunks that each carry their source anchors, and MUST record bidirectional relatedness edges between a prose chunk and any exhibit it resolves, plus reading-order neighbor edges.

#### Scenario: Bidirectional link between prose and its exhibit

- **WHEN** a prose chunk resolves a reference to an exhibit chunk
- **THEN** the prose chunk lists the exhibit chunk in its related references
- **AND** the exhibit chunk lists that prose chunk in its related references
