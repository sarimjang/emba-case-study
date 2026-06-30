## Context

`case-spec-source-refs` (change 7) lets `case_spec.json` evidence fields carry structured objects with `source_refs` alongside legacy strings. The three generators (`generate_case_md.py`, `generate_case_docx.py`, `generate_case_pptx.py`) currently iterate evidence items as plain strings (`bullets` / `add_bullets`), so a structured object would render as a Python dict repr.
This change makes the generators render structured evidence text and references while keeping legacy string output byte-identical. It is rendering only; the evidence model is owned by change 7.

## Goals / Non-Goals

**Goals:**

- One shared rendering helper so all three formats behave consistently.
- Structured objects render `text` first, then `source_refs`; legacy strings render unchanged.
- No change to canonical evidence structure; no Docling raw JSON reads.

**Non-Goals:**

- Changing the evidence model or validator (change 7).
- Producing structured evidence (ingestion/analysis path).
- SKILL workflow routing (change 9).

## Decisions

### Single shared helper in case_spec_utils, applied at the bullet layer

Add `evidence_item_text(item) -> str` to `scripts/case_spec_utils.py` and route every generator's bullet/list rendering through it.
Rationale: the validator already lives there; one helper guarantees identical MD/DOCX/PPTX behavior and a single place to evolve ref formatting. Applying it at the existing `bullets`/`add_bullets` layer also covers plain-string fields (milestones, backgrounds) safely, because strings pass through unchanged.
Alternative considered: per-generator rendering — rejected; risks divergent output and duplicated ref formatting.

### Strings pass through untouched; objects get a reference suffix

`evidence_item_text` returns a plain string verbatim. For a structured object it returns `text` plus, when `source_refs` is non-empty, a suffix `(sources: ref1, ref2)`. An object without refs renders only its `text`.
Rationale: satisfies "render text first, append references where supported" and guarantees legacy specs render identically (the helper is the identity function on strings).

## Implementation Contract

- **Behavior**: rendering an all-string spec produces output identical to today. Rendering a spec with a structured evidence item shows the item's `text` followed by its references in MD, DOCX, and PPTX. Generators never read Docling raw JSON.
- **Interface / data shape**: `evidence_item_text(item: str | dict) -> str`. For `str`, returns it unchanged. For `dict`, returns `text` optionally followed by `(sources: <comma-joined source_refs>)`. The md `bullets`, docx `add_bullets`, and pptx `add_bullets` map each item through it.
- **Failure modes**: a structured object is assumed already validated by change 7; the helper reads `text`/`source_refs` defensively (missing `source_refs` → no suffix). No exceptions are introduced into the render path for valid specs.
- **Acceptance criteria**: spec scenarios in `specs/export-source-ref-rendering/spec.md` hold; a legacy-spec render is unchanged (asserted by comparing output for a string-only spec); a structured-item render contains the text and ref in all three formats; `python3 -m unittest discover -s tests` passes.
- **Scope boundaries**: in scope — `evidence_item_text` helper and the three generators' bullet rendering. Out of scope — evidence model/validator, evidence production, SKILL routing.

## Risks / Trade-offs

- [Reference suffix formatting may not suit every surface (e.g. dense PPTX bullets)] → keep the suffix compact and identical across formats now; format-specific styling can refine later without changing the contract.
- [Applying the helper to plain-string list fields] → safe by construction: the helper is the identity on strings, so non-evidence string fields are unaffected.

## Migration Plan

Additive and backward-compatible: the helper is the identity on strings, so every existing all-string spec renders identically. Rollback is reverting the generators to call the raw item and removing the helper.

## Open Questions

- None blocking. Per-format visual styling of references (footnote vs inline) can be revisited when real structured specs are exported.
