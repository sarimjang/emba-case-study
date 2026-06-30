## Why

Charts are important EMBA evidence, but scan quality makes automatic value extraction unreliable, so the first scope must preserve the figure and its readable labels without fabricating plotted numbers (`docs/adr/0002-defer-chart-digitization.md`).
This change adds figure/chart preservation as exhibit semantics.

> Maturity: draft. Dependencies: `source-document-schema-validation`, `exhibit-semantics-foundation`. Do not implement until figure anchors, caption anchors, and nearby-text association are stable.

## What Changes

- Detect figure blocks and nearby exhibit captions.
- Extract OCR-readable chart titles, axis labels, visible series labels, source text, and note text when OCR can read them.
- Preserve the chart image or an artifact reference for human verification.
- Mark chart data extraction status as `image_preserved_only` unless a separately verified digitization module exists.

## Non-Goals

- Estimating plotted values from visual appearance (forbidden by ADR-0002).
- Populating `case_spec.evidence.chart_data` from unverified chart images.
- Full chart digitization.

## Capabilities

### New Capabilities

- `chart-figure-preservation`: figure/chart exhibit interpretation that preserves the figure area and reference, captures OCR-readable labels/captions/source/notes, and records a conservative `image_preserved_only` data-extraction status with source references.

### Modified Capabilities

<!-- None; conservative figure interpretation layer over exhibit-semantics anchors. -->

## Impact

- Depends on stable figure/caption anchors in `source-document/v1` and `exhibit-semantics/v1`.
- Establishes the evidence standard that keeps quantitative chart claims tentative downstream.
- No exporter or `case_spec.json` change in this change.
