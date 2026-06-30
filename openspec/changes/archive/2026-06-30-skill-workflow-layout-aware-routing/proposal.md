## Why

The skill currently cannot tell users when a path preserves document structure versus when it flattens it, nor does it route scanned exhibits through layout-aware ingestion before analysis (`ROADMAP.md` Phase 7).
This change updates the skill workflow to be layout-aware once the ingestion and source-ref contracts exist.

> Maturity: dependent draft. Dependencies: `docling-ingestion-adapter`, `source-document-schema-validation`, `case-spec-source-refs`. Do not implement until ingestion and source-ref contracts are stable.

## What Changes

- Update `SKILL.md` capability detection to distinguish plain OCR from layout-aware extraction.
- Tell users when the current path preserves structure and when it loses structure.
- Route scanned exhibits through Docling-backed ingestion before EMBA analysis when consent is given.
- Require source anchors from `source_document.json` or `exhibit_semantics.json` before trusting exhibit claims.

## Non-Goals

- Implementing the ingestion adapter itself (`docling-ingestion-adapter`).
- Implementing exhibit semantics (`exhibit-semantics-foundation`).
- Weakening privacy, network, or model-download gates.

## Capabilities

### New Capabilities

- `skill-workflow-layout-aware-routing`: skill-level routing and disclosure that detects layout-aware vs plain-OCR paths, gates scanned-exhibit ingestion on consent, and requires source anchors before exhibit claims are trusted.

### Modified Capabilities

<!-- Modifies SKILL.md workflow behavior; the change is to skill routing/disclosure, authored as the capability spec when implemented. -->

## Impact

- Touches `SKILL.md` workflow and capability-detection guidance.
- Depends on stable ingestion (`docling-ingestion-adapter`), validation (`source-document-schema-validation`), and source-ref (`case-spec-source-refs`) contracts.
- Preserves all existing privacy/network/model-download gates.
