## 1. Chart semantics module

- [x] 1.1 Create the Standalone chart_semantics module enriching the figure path (`scripts/chart_semantics.py`) with `chart_exhibit_fields(figure, captions_by_ref)`, satisfying the Figure preservation with caption association requirement: return `image_ref` (the figure `self_ref`) and a `title` from an associated caption when resolvable. Behavior: a figure yields an `image_ref` to its `self_ref`; a figure with a resolvable caption_ref yields that caption as `title`; no caption leaves `title` None. Verify: unit tests for the image-ref and caption-as-title scenarios.

## 2. Label preservation and status

- [x] 2.1 Implement Caption text as the readable-label source in first scope, satisfying the OCR-readable label preservation without digitization requirement: record caption/source text as `chart_label`/`chart_source` hints with `source_refs` (confidence `observed` for caption-derived text else `hint`). Behavior: available labels are preserved as source-anchored hints; absent labels add no hint. Verify: unit test asserting label hints carry source_refs and valid confidence.
- [x] 2.2 Implement Status pinned to image_preserved_only: every chart exhibit sets `data_extraction_status` to `image_preserved_only` and carries no numeric series. Behavior: the chart exhibit's status is `image_preserved_only` and contains no plotted values. Verify: unit tests for the status and no-numeric-series scenarios.

## 3. Integration and regression

- [x] 3.1 Enrich the `extract_exhibit_semantics` figure path by merging `chart_exhibit_fields` into the chart exhibit. Behavior: a source figure produces a chart exhibit with image_ref, optional title, label hints, and `image_preserved_only` status; table/hierarchy exhibits are unchanged. Verify: an extractor unit test on a figure-bearing document asserts the enriched chart exhibit, and `python3 -m unittest discover -s tests` exits OK.
