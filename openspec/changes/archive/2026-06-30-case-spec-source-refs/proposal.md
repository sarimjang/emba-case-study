## Why

`case_spec.json` evidence is currently free-form strings with no traceable link to the exhibits it claims about; analysis cannot be audited back to observed facts or interpretations (`ROADMAP.md` Phase 8, `CONTEXT.md` "Source Reference Rule").
This change adds optional structured evidence with source references while keeping existing exports working.

> Maturity: draft. Dependencies: `source-document-schema-validation`, `exhibit-semantics-foundation`. Do not implement until `source_document.json` and `exhibit_semantics.json` anchor formats are stable.

## What Changes

- Add optional structured evidence objects with `text`, `source_refs`, `confidence`, and `evidence_type` to `case_spec.json`, alongside the existing string-array evidence fields.
- Preserve backward compatibility: legacy string items remain valid and render exactly as today.
- Enforce the Source Reference Rule: direct observed facts may cite `source_document.json` anchors; interpreted exhibit claims MUST cite `exhibit_semantics.json` anchors.
- Validate that structured objects have non-empty `text` and that list items are not mixed non-string/non-object.

## Non-Goals

- Moving layout data into `case_spec.json` (layout stays in `source_document.json`, interpretation in `exhibit_semantics.json`).
- Backfilling all legacy evidence strings.
- Making exporter formatting the canonical evidence model (`export-source-ref-rendering` handles rendering).

## Capabilities

### New Capabilities

- `case-spec-source-refs`: an additive, backward-compatible structured-evidence model for `case_spec.json` that lets evidence cite source-document or exhibit-semantics anchors under the Source Reference Rule.

### Modified Capabilities

<!-- Modifies the case_spec.json evidence contract additively; recorded as a delta spec when authored. Check openspec/specs/ for an existing case-spec capability before implementing. -->

## Impact

- Touches the `case_spec.json` schema and its validator; legacy compatibility behavior is explicit (`ROADMAP.md` Phase 8 migration rules).
- Unblocks `export-source-ref-rendering`.
- Existing MD/DOCX/PPTX exports must keep working unchanged for legacy specs.
