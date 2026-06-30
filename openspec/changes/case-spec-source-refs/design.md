## Context

`case_spec.json` evidence is validated today by `scripts/case_spec_utils.py` (`validate_spec`), which requires plain string arrays for evidence and appendix fields. The exhibit-semantics layer (changes 3–4) now produces source-anchored, confidence-tagged claims, but `case_spec.json` has no way to cite them.
This change adds optional structured evidence objects with `source_refs` while keeping every existing string-array spec valid and rendering identically (`ROADMAP.md` Phase 8). It modifies the validator only; exporter rendering is change 8.

## Goals / Non-Goals

**Goals:**

- Accept structured evidence objects alongside legacy strings in the eight evidence/appendix fields, with no behavior change for existing specs.
- Enforce the structured-object shape, the confidence vocabulary, and the Source Reference Rule mechanically.
- Keep layout/OCR data out of `case_spec.json`.

**Non-Goals:**

- Exporter rendering of structured evidence (change 8).
- Backfilling legacy string evidence.
- Producing the structured evidence (that is the ingestion/analysis path); this change only validates it.

## Decisions

### Extend validation with an evidence-item helper, not a new schema

Add `_expect_evidence_list(value, label)` that accepts each item as either a legacy string or a structured object, replacing `_expect_list_of_str` for the eight evidence/appendix fields only.
Rationale: minimal, backward-compatible change to the existing pure-stdlib validator; other fields (titles, milestones, etc.) keep strict string validation.
Alternative considered: a separate evidence schema module — rejected as over-engineering for an additive field-shape change.

### Source Reference Rule enforced by anchor-shape inspection

An evidence object that marks itself as interpreting an exhibit (`evidence_type == "exhibit_interpretation"` or `interprets_exhibit: true`) must include at least one `source_refs` entry recognizable as an exhibit-semantics anchor (an `exhibit-…` id or a ref containing `exhibit-semantics`). Observed-fact objects may cite source-document anchors freely.
Rationale: mechanically enforces the `CONTEXT.md` rule without resolving cross-file references at validation time.
Alternative considered: resolve refs against the actual exhibit_semantics.json — rejected; the validator must work on `case_spec.json` alone.

### Layout/OCR denylist on evidence objects

Reject reserved layout keys (`bbox`, `cells`, `page_number`, `self_ref`) inside evidence objects, mirroring the facts-only guard in `source_document_schema`.
Rationale: keeps `case_spec.json` from becoming a layout representation (`ROADMAP.md` cross-proposal contracts).

## Implementation Contract

- **Behavior**: `validate_spec` continues to accept every existing all-string case spec unchanged, and now also accepts the eight evidence/appendix fields carrying structured evidence objects. Invalid structured objects, invalid confidence, interpretation claims lacking an exhibit anchor, embedded layout keys, and non-string/non-object items all raise `SpecValidationError` naming the field path.
- **Interface / data shape**: a structured evidence object is `{text: str (non-empty), source_refs?: [str], confidence?: observed|inferred|verified|hint|rejected, evidence_type?: str, interprets_exhibit?: bool}`. The eight fields are `evidence.{quantitative_signals,internal_checks,external_checks,open_issues}`, `case.source_notes`, `appendix.{references,assumptions,discussion_questions}`.
- **Failure modes**: empty/missing `text`, non-list `source_refs` or empty ref strings, out-of-vocabulary `confidence`, interpretation object without an exhibit anchor, reserved layout key present, or a list item that is neither string nor object — each raises `SpecValidationError` with the field path; nothing is silently dropped.
- **Acceptance criteria**: spec scenarios in `specs/case-spec-source-refs/spec.md` hold; the existing `tests/test_case_spec_utils.py` suite stays green (legacy specs unchanged); `python3 -m unittest discover -s tests` passes.
- **Scope boundaries**: in scope — validator changes in `case_spec_utils.py` and tests. Out of scope — generator/exporter rendering (change 8), evidence production, SKILL routing (change 9).

## Risks / Trade-offs

- [Anchor-shape heuristic misjudges an exhibit ref format] → keep the recognizer permissive (accept `exhibit-` ids and `exhibit-semantics` substrings); refine when change 8 renders real refs. Observed-fact path is unaffected.
- [A field both legacy-rendered and structured could confuse exporters] → change 8 owns rendering; this change guarantees only that both shapes validate.

## Migration Plan

Additive and backward-compatible: `_expect_list_of_str` is replaced by `_expect_evidence_list` only on the eight evidence/appendix fields. All existing all-string specs validate exactly as before. Rollback is reverting the helper swap.

## Open Questions

- The precise `evidence_type` vocabulary beyond `exhibit_interpretation` is finalized when change 8 renders evidence; this change only special-cases the interpretation marker and otherwise treats `evidence_type` as a free-form label.
