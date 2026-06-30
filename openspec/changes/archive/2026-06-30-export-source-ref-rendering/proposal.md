## Why

Once `case_spec.json` carries structured evidence with source references, the generators must render that text and its references — while still rendering legacy string evidence unchanged (`ROADMAP.md` Phase 8).
This change updates the exporters to consume the new evidence model.

> Maturity: dependent draft. Dependencies: `case-spec-source-refs`. Do not implement until the structured-evidence migration is accepted.

## What Changes

- Update the Markdown, DOCX, and PPTX generators (`scripts/generate_case_md.py`, `scripts/generate_case_docx.py`, `scripts/generate_case_pptx.py`) to render structured evidence `text` first and append source references where supported.
- Keep legacy string-evidence rendering byte-for-byte unchanged.
- Run the existing generator compatibility tests across legacy and structured evidence.

## Non-Goals

- Changing the canonical evidence model beyond the accepted `case-spec-source-refs` migration.
- Reading Docling raw JSON from exporters (forbidden by `docs/adr/0001-keep-docling-raw-json-out-of-public-contract.md`).
- Making export formatting the canonical evidence structure.

## Capabilities

### New Capabilities

- `export-source-ref-rendering`: exporter support that renders structured evidence text and source references in MD/DOCX/PPTX output while preserving identical rendering for legacy string evidence.

### Modified Capabilities

<!-- Modifies exporter rendering behavior; authored as a delta against the relevant export capability spec when implemented. -->

## Impact

- Touches all three generators and their compatibility tests.
- Depends on the accepted structured-evidence shape from `case-spec-source-refs`.
- Legacy exports must remain unchanged; structured rendering is additive.
