## Why

EMBA exhibits lose document structure today because extraction collapses straight into the analysis schema, discarding pages, tables, captions, bounding boxes, and provenance (see `ROADMAP.md` "Problem statement").
This change adds the bottom layer of the staged pipeline so later semantic and analysis work has a stable, repo-owned source-document contract to build on.

## What Changes

- Add `scripts/ingest_with_docling.py`: invoke the local Docling executable and emit three artifacts under `outputs/<case-slug>/ingestion/`: `docling/raw.json`, `source_document.json`, `ingestion_manifest.json`.
- Normalize Docling output into the repo-owned `source_document.json` contract (`schema-version: source-document/v1`): pages, blocks, tables, figures, notes, bbox values, captions, cell metadata, and page provenance — observed facts only, no business interpretation.
- Enforce the Docling environment gate, privacy gate, network gate, model-download gate, and artifact-size budget defaults (`ROADMAP.md` "Docling environment gate", "Privacy, network, and model-download gate", "Performance and artifact-size budget").
- Discover the Docling executable via explicit flag → `~/.pyenv/versions/3.12.0/bin/docling` → `~/.pyenv/shims/docling` → `PATH`, and reuse the existing generators' output-path containment / `--allow-outside-workspace` safety pattern.
- Keep Docling raw JSON as a local debug/audit artifact only (`docs/adr/0001-keep-docling-raw-json-out-of-public-contract.md`).

## Non-Goals

- Exhibit business semantics, case analysis, and exporter changes — owned by downstream changes (`exhibit-semantics-foundation`, `case-spec-source-refs`, `export-source-ref-rendering`).
- Chart digitization — deferred (`docs/adr/0002-defer-chart-digitization.md`).
- Any downstream code reading Docling raw JSON directly — forbidden by ADR-0001.
- Schema-validation helpers and fixtures for `source_document.json` — owned by the dependent change `source-document-schema-validation`; this change only defines the first normalized shape.
- Embedding base64 page images into canonical normalized output by default.

## Capabilities

### New Capabilities

- `docling-ingestion-adapter`: a local, gated ingestion CLI that converts a source document into Docling raw JSON plus a normalized repo-owned `source_document.json` and an `ingestion_manifest.json` gate record, establishing the adapter boundary that contains provider-specific schema drift.

### Modified Capabilities

<!-- None. This change introduces a new pipeline layer and does not alter existing case_spec.json or exporter requirements. -->

## Impact

- New file: `scripts/ingest_with_docling.py`. New output tree: `outputs/<case-slug>/ingestion/`.
- New repo-owned schema contract `source-document/v1` that all downstream changes (2–9) depend on; its anchor format must stabilize here before dependents leave draft.
- Runtime dependency on a locally installed Docling (`docling 2.14.0` surface confirmed in `ROADMAP.md` "Confirmed local Docling surface"); not added to repo dependency manifests.
- No change to existing `case_spec.json`, generators, or `SKILL.md` behavior.
