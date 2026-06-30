## Context

`exhibit-semantics-foundation` already creates a coarse `chart` exhibit per figure but records only a classification hint — it drops the caption, OCR-readable labels, the figure reference, and the extraction status. This change enriches chart exhibits to preserve the figure and its readable labels conservatively, per `docs/adr/0002-defer-chart-digitization.md`: preserve, never digitize.
Inputs are `source-document/v1` figures (which carry `self_ref`, `caption_refs`, `data_extraction_status`) and page text blocks that may hold OCR-readable labels.

## Goals / Non-Goals

**Goals:**

- Preserve each figure as a `chart` exhibit with an `image_ref` and an associated caption title.
- Record OCR-readable labels (title/axis/series) and source/note text as source-anchored hints.
- Always set `data_extraction_status: image_preserved_only`; never fabricate plotted values.

**Non-Goals:**

- Estimating plotted numeric series from images; populating `case_spec.evidence.chart_data` from an image.
- Full chart digitization (a future separately verified module).
- Exporter or `case_spec.json` changes.

## Decisions

### Standalone chart_semantics module enriching the figure path

Add `scripts/chart_semantics.py` with `chart_exhibit_fields(figure, captions_by_ref)` returning the enrichment (image_ref, title, label/source hints, status), and call it from the extractor's figure loop.
Rationale: isolates the conservative preservation logic and keeps it independently testable; mirrors `table_semantics`/`hierarchy_semantics`.
Alternative considered: inline in the extractor — rejected for consistency and testability.

### Caption text as the readable-label source in first scope

Resolve a figure's `caption_refs` against page block text to set `title`, and treat caption text as the primary OCR-readable label source; explicit axis/series labels are recorded only when present in the source document. No image is OCR'd inside this module.
Rationale: the source document already holds Docling-extracted block text; this change associates it, it does not run new OCR. Keeps the change deterministic and avoids fabricating labels.

### Status pinned to image_preserved_only

Every chart exhibit's `data_extraction_status` is `image_preserved_only` regardless of available labels; no numeric series field is ever added.
Rationale: ADR-0002 — quantitative chart claims must remain tentative; preservation must not be mistaken for digitization.

## Implementation Contract

- **Behavior**: for each source figure, the chart exhibit gains `image_ref` (the figure `self_ref`), `title` (from an associated caption when resolvable), chart-label/source hints (each with `source_refs` + confidence), and `data_extraction_status: image_preserved_only`. No numeric series is emitted.
- **Interface / data shape**: `chart_semantics.chart_exhibit_fields(figure, captions_by_ref) -> dict` with keys `image_ref`, `title`, `semantic_hints` (kinds `chart_label`/`chart_source`, confidence `observed` for caption-derived text else `hint`), `data_extraction_status`. The extractor merges these into the figure-derived exhibit.
- **Failure modes**: no caption → `title` is None and no caption hint; no labels → only the classification + image preservation, status still `image_preserved_only`; never raises on a well-formed figure.
- **Acceptance criteria**: spec scenarios hold against hand-built figure fixtures (figure + caption; figure without caption); the chart exhibit never contains a numeric series; `python3 -m unittest discover -s tests` passes.
- **Scope boundaries**: in scope — chart_semantics module, figure-path enrichment, tests. Out of scope — image OCR, digitization, exporters, case_spec.

## Risks / Trade-offs

- [Caption association picks the wrong nearby text] → use the figure's explicit `caption_refs` resolved against block text; when absent, leave `title` None rather than guessing.
- [Downstream mistakes preservation for digitization] → status pinned to `image_preserved_only` and no numeric field is ever added; ADR-0002 reaffirmed.

## Migration Plan

Additive — new module, figure-path enrichment, new tests. Existing table/hierarchy exhibits and the chart classification are unchanged except for the added fields. Rollback is removing the module and the enrichment call.

## Open Questions

- True per-pixel axis/series OCR and digitization remain a future, separately verified module; this change only preserves and associates already-extracted text.
