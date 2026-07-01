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

The layer SHALL resolve a prose "Exhibit N" reference to an exhibit using tiered evidence evaluated in a fixed order — caption-carries-number, then prose description bridge, then label-anchor geometry — and MUST tag each resolved link with a confidence from the fixed vocabulary: caption-carries-number as `verified`, prose description bridge as `inferred`, label-anchor geometry as `hint`. A later tier MUST NOT bind a number that an earlier tier already resolved, and MUST NOT bind an object that an earlier tier already bound to a different number. Document-order position alone MUST NOT resolve a reference, and MUST NOT combine with page or type signals to form a resolving path; it MAY only corroborate a candidate that one of the three qualifying tiers above already resolved. A reference with no qualifying evidence MUST be left unresolved rather than bound to the nearest exhibit.

For the prose description bridge, an exhibit's "distinctive caption head" is its caption with boilerplate markers removed, and the layer MUST reject a head that is shorter than a configured minimum length or that matches a configured generic-noun stop list, so a reference does not bind on a non-distinctive head.

#### Scenario: Tier order prevents an earlier-resolved number from rebinding

- **WHEN** the description bridge has already resolved "Exhibit 6" to a table, and label-anchor geometry later evaluates an "Exhibit 5" label whose nearest object is that same table
- **THEN** label-anchor does not bind "Exhibit 5" to that table because it is already bound to a different number

#### Scenario: Description bridge binds the correct table

- **WHEN** prose names a description near "Exhibit N" that matches one exhibit's distinctive caption head unambiguously
- **THEN** that "Exhibit N" reference resolves to that exhibit with `inferred` confidence

#### Scenario: Non-distinctive caption head does not bind

- **WHEN** an exhibit's caption reduces to a head shorter than the minimum length or on the generic-noun stop list after boilerplate removal
- **THEN** the description bridge does not bind any reference on that head

#### Scenario: Document-order position alone does not resolve

- **WHEN** a reference has only document-order position and no page, type, or local-label corroboration
- **THEN** the reference is left unresolved

#### Scenario: Ambiguous reference stays unresolved

- **WHEN** an "Exhibit N" reference has no caption-number, no unambiguous description match, and no separated nearest object
- **THEN** the reference is left unresolved

### Requirement: Anti-binding guards for label-anchor resolution

When binding a bare "Exhibit N" label to the nearest exhibit object, the layer SHALL reject the bind unless the nearest object is within a configured fraction of the label's page height AND the object is not already bound to a different exhibit number. When a runner-up object exists, the layer SHALL additionally reject the bind unless the nearest object is closer than a configured fraction of the runner-up distance. When the page has a single exhibit object (no runner-up), the separation check is not applicable and the distance and number-conflict guards alone govern the bind.

#### Scenario: Close sole object binds

- **WHEN** a page has a single exhibit object within the page-height fraction of the label and the object is not bound to a different number
- **THEN** the label binds to that object with `hint` confidence despite having no runner-up competitor

#### Scenario: Sole distant object rejected

- **WHEN** a page has a single exhibit object and the label is farther than the page-height fraction from it
- **THEN** the label is left unresolved despite having no runner-up competitor

#### Scenario: Number conflict rejected

- **WHEN** the nearest object is already bound to a different exhibit number
- **THEN** the label does not bind to that object

### Requirement: Dual-type phantom signalling for undetected exhibits

The layer SHALL emit a phantom record when a reference resolves to a number with no registered exhibit, and MUST classify it as `mentioned-only` when only prose cites the number, or as `label-detected-object-undetected` when a label block names the exhibit but no object was detected. For a `label-detected-object-undetected` phantom, the layer MUST record the label block's own source anchor as a pointer; deriving a re-scan region from that pointer is out of scope for this change.

#### Scenario: Labelled-but-undetected exhibit flagged for re-extraction

- **WHEN** a label block names "Exhibit N" but no table or figure object was detected for it
- **THEN** a phantom record of type `label-detected-object-undetected` is emitted carrying the label block's source anchor

#### Scenario: Prose-only reference to a missing exhibit

- **WHEN** an "Exhibit N" number appears only in prose, with no label block and no detected object
- **THEN** a phantom record of type `mentioned-only` is emitted

### Requirement: Reading-view projection structure

The layer SHALL emit a human reading view that renders the linearized stream in order, where each prose block appears with its label-derived formatting, each exhibit appears as its placeholder anchor followed by its rendered body (a table rendering for tables, a preserved-image marker for figures), and each resolved "Exhibit N" reference is annotated with its target and confidence while each unresolved reference is annotated as unresolved.

#### Scenario: Resolved and unresolved references are both annotated

- **WHEN** the reading view renders a prose block with one resolved and one unresolved "Exhibit N" reference
- **THEN** the resolved reference shows its target exhibit and confidence
- **AND** the unresolved reference is marked unresolved

### Requirement: RAG chunks preserve source references and relatedness

The layer SHALL emit RAG chunks that each carry their source anchors, and MUST record bidirectional relatedness edges between a prose chunk and any exhibit it resolves, plus reading-order neighbor edges.

#### Scenario: Bidirectional link between prose and its exhibit

- **WHEN** a prose chunk resolves a reference to an exhibit chunk
- **THEN** the prose chunk lists the exhibit chunk in its related references
- **AND** the exhibit chunk lists that prose chunk in its related references
