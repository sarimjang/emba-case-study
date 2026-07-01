## Why

The pipeline produces two canonical artifacts that are single-responsibility and already cross-linked by anchors: `source_document.json` (facts: prose blocks with bbox/label, plus `tables[]`/`figures[]`) and `exhibit_semantics.json` (interpretation: exhibit type, roled cells, confidence, `source_refs`). But nothing materializes the join. Two downstream consumers both need structure, semantics, and relatedness in one interleaved form — human reading and RAG retrieval — and today they would each have to re-derive the join. Prose references to "Exhibit N" are also never linked to the exhibit they name, because Docling captions do not carry the exhibit number.

This change adds a derived composition layer that linearizes prose and exhibits into one reading order and resolves "Exhibit N" references with confidence-tiered binding, validated against two real scanned cases (`ROADMAP.md` layout-aware ingestion goals).

> Maturity: draft. Dependencies: `source-document/v1`, `exhibit-semantics/v1`. Do not implement until those anchors and confidence fields are stable (they are, as of the archived layout-aware changes).

## What Changes

- Add a derived composition layer that reads both canonical artifacts and never mutates them, emitting two projections: a human `reading_view` (interleaved prose + exhibit placeholders + cross-reference links) and a `rag_chunks` set (structure-aware chunks carrying source anchors, exhibit structure, and bidirectional relatedness edges).
- Linearize using Docling native block order as the spine; insert each exhibit as a stable placeholder at its caption position, with a bbox fallback when no caption exists.
- Suppress duplicate prose blocks conservatively: only when a block's text exactly equals a table cell AND its bbox center sits inside that table's bbox.
- Build a confidence-tiered Exhibit Identity Registry that binds "Exhibit N" references to exhibits using resources already in the data, tagging every link with a confidence from the fixed vocabulary and leaving genuinely ambiguous references unresolved.
- Emit dual-type phantom records for referenced-but-undetected exhibits, distinguishing `mentioned-only` from `label-detected-object-undetected`.

## Non-Goals

- Mutating `source_document.json` or `exhibit_semantics.json` (the composition layer is purely derived and regenerable).
- Chart digitization or estimating plotted values (`docs/adr/0002-defer-chart-digitization`).
- Visual/vision-model binding methods (sub-figure segmentation, second-pass page OCR, chart-type classification, VLM adjudication) — deferred as ADR-gated, non-deterministic, or out of scope; recorded in the design for a later change.

## Capabilities

### New Capabilities

- `composition-linearization`: a derived layer that interleaves facts and interpretation into a native-order reading stream with exhibit placeholders, conservative deduplication, confidence-tiered "Exhibit N" reference resolution with anti-binding guards, and dual-type phantom signalling, projected into a human reading view and RAG chunks that preserve source references.

### Modified Capabilities

<!-- May extend exhibit-semantics phantom signalling during implementation; recorded as a delta then if behavior changes. -->

## Impact

- Reads `source-document/v1` and `exhibit-semantics/v1`; writes only new derived artifacts.
- Provides the interleaved structure/semantics/relatedness surface that RAG indexing and human review both consume.
- No change to the canonical artifacts, `case_spec.json`, or existing exporters.
