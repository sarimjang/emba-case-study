## ADDED Requirements

### Requirement: Capability detection distinguishes layout-aware extraction

The skill workflow SHALL distinguish plain OCR or plain text extraction from layout-aware extraction via the Docling ingestion adapter, and SHALL disclose to the user which paths preserve document structure and which lose it.
`SKILL.md` MUST describe the layout-aware path using the `scripts/ingest_with_docling.py` adapter and name `source_document.json` as its structure-preserving output.

#### Scenario: Capability brief names the layout-aware option

- **WHEN** the skill presents its capability brief for a scanned or exhibit-heavy source
- **THEN** it names a layout-aware extraction path distinct from plain OCR
- **AND** it states that the plain path loses document structure while the layout-aware path preserves it

### Requirement: Consent-gated layout-aware ingestion of scanned exhibits

The workflow SHALL route scanned or image-only exhibits through Docling-backed ingestion before EMBA analysis only after obtaining user consent, and MUST NOT weaken the adapter's privacy, network, or model-download gates.
`SKILL.md` MUST require explicit consent before running the adapter on a scanned source and MUST point to the existing consent/checkpoint pattern.

#### Scenario: Scanned exhibit routed after consent

- **WHEN** the source is scanned or image-only and the user consents to layout-aware ingestion
- **THEN** the workflow runs the Docling adapter before analysis

#### Scenario: Consent required before ingestion

- **WHEN** layout-aware ingestion would run on a scanned source
- **THEN** the workflow requires explicit user consent first
- **AND** it does not relax the privacy, network, or model-download gates

### Requirement: Source anchors required before trusting exhibit claims

The workflow SHALL require a source anchor from `source_document.json` or `exhibit_semantics.json` before an exhibit interpretation is treated as trusted evidence, consistent with the Source Reference Rule (`CONTEXT.md`).
`SKILL.md` MUST state that exhibit interpretations cite `exhibit_semantics.json` anchors and observed facts cite `source_document.json` anchors.

#### Scenario: Exhibit claim without an anchor is not trusted

- **WHEN** an exhibit interpretation has no `source_document.json` or `exhibit_semantics.json` anchor
- **THEN** the workflow does not treat it as validated evidence

#### Scenario: Anchored interpretation accepted

- **WHEN** an exhibit interpretation cites an `exhibit_semantics.json` anchor
- **THEN** the workflow may treat it as validated evidence
