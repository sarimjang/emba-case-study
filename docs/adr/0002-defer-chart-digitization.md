# ADR-0002: Defer chart digitization from the first ingestion scope

## Status

Accepted

## Context

EMBA cases often use charts as important evidence.

A chart image may contain axes, labels, source notes, and trend lines, but scan quality, skew, compression, and missing numeric annotations can make automatic value extraction unreliable.

The roadmap already distinguishes chart or figure preservation from chart data extraction.

## Decision

The first chart implementation will preserve chart figures, OCR-readable labels, captions, sources, and notes, but will not digitize chart series values by default.

`case_spec.evidence.chart_data` may only be populated from explicit table numbers, explicit numeric labels, verified external or source data, or a future separately verified chart digitization module.

Agents must not estimate chart data by visually guessing from a plotted line or bar.

## Consequences

Chart evidence can still support qualitative analysis when the source and visible labels are preserved.

Quantitative chart claims must remain tentative unless backed by explicit numbers or a verified digitization workflow.

The roadmap preserves room for future chart digitization without weakening the first implementation's evidence standard.

## Alternatives considered

### Digitize charts in the first implementation

Rejected because chart scan quality varies and unverified image-derived numbers would create false precision.

### Ignore charts entirely

Rejected because chart captions, labels, sources, and notes are still important case evidence even when numeric digitization is deferred.
