## Context

Changes 1–8 built and merged the layout-aware pipeline (Docling adapter → validated `source_document.json` → `exhibit_semantics.json` → source-anchored `case_spec.json` → exports). `SKILL.md` still describes only plain text/OCR ingestion and does not route scanned exhibits through the new adapter or require source anchors.
This change updates `SKILL.md` so the skill actually uses the pipeline and discloses structure-preserving vs lossy paths. It is the final piece of the primary spine; it touches documentation/workflow only, not code.

## Goals / Non-Goals

**Goals:**

- Make `SKILL.md` distinguish plain OCR from layout-aware (Docling) extraction and disclose the structure trade-off.
- Route scanned/image-only exhibits through `scripts/ingest_with_docling.py` after consent, preserving the existing gates.
- Require `source_document.json` / `exhibit_semantics.json` anchors before exhibit claims are trusted.

**Non-Goals:**

- Implementing the adapter, validator, or semantics (changes 1–4, already merged).
- Weakening privacy/network/model-download gates.
- Hierarchy (change 5) and chart-preservation (change 6) depth.

## Decisions

### Edit existing workflow sections rather than add a parallel flow

Extend Step 0 (capability detection) and Step 1 (ingest by format) with the layout-aware option and consent gate, and Step 5 (validate exhibits) with the source-anchor requirement, instead of adding a separate workflow branch.
Rationale: keeps one coherent workflow; the layout-aware path is an escalation of the existing ingest step, gated by consent like OCR/export already are.
Alternative considered: a new top-level section — rejected; fragments the workflow and duplicates the consent pattern.

### Reference the pipeline by path, reuse the existing consent/checkpoint pattern

Point at `scripts/ingest_with_docling.py`, `source_document.json`, and `exhibit_semantics.json` by name, and reuse `references/delivery-and-consent.md` for the consent gate rather than inventing a new mechanism.
Rationale: matches how `SKILL.md` already handles OCR/export consent; no new contract surface.

## Implementation Contract

- **Behavior**: a reader of `SKILL.md` learns (a) that layout-aware Docling ingestion is a distinct, structure-preserving option vs plain OCR, (b) that scanned exhibits are routed through `scripts/ingest_with_docling.py` only after consent and without weakening gates, and (c) that exhibit interpretations require `source_document.json`/`exhibit_semantics.json` anchors before being trusted.
- **Interface / data shape**: documentation edits to `SKILL.md` Steps 0, 1, and 5 (and the Reference Files list as needed). No code or schema changes. Named artifacts: `scripts/ingest_with_docling.py`, `source_document.json`, `exhibit_semantics.json`.
- **Failure modes**: none at runtime; this is guidance. The guidance MUST NOT instruct relaxing gates and MUST NOT instruct reading Docling raw JSON downstream.
- **Acceptance criteria**: the spec scenarios hold as content checks — `SKILL.md` contains the layout-aware-vs-plain disclosure, the consent-gated adapter routing, and the source-anchor requirement; a deterministic test asserts these are present; `python3 -m unittest discover -s tests` passes.
- **Scope boundaries**: in scope — `SKILL.md` workflow edits and a content-assertion test. Out of scope — code, schemas, gates, hierarchy/chart depth.

## Risks / Trade-offs

- [Doc guidance drifts from the actual adapter CLI] → reference the adapter by path and keep CLI specifics in the change-1 design; the content test pins the key references so drift is caught.
- [Over-prescribing the workflow] → keep edits to escalation points (Steps 0/1/5) and reuse the existing consent pattern.

## Migration Plan

Documentation-only and additive: existing workflow steps remain; the layout-aware option and anchor requirement are added. Rollback is reverting the `SKILL.md` edits.

## Open Questions

- None blocking. Hierarchy/chart-specific routing notes can be added when changes 5 and 6 land.
