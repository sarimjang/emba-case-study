## Context

`source_document.json` (facts) and `exhibit_semantics.json` (interpretation) are cross-linked by `self_ref`/`source_refs` anchors but never materialized into a single reading flow. Human reading and RAG both need structure + semantics + relatedness interleaved. This design was prototyped and tested on two real scanned EMBA cases (Benihana EN, pet-shop ZH) before formalization; the numbers below are measured, not hypothetical.

## Decision 1: A derived third layer, not mutation of the canonical files

The composition is a new regenerable artifact computed from both canonical files. It does not write back into them.

| Option | Verdict |
| --- | --- |
| Embed exhibit structure into `source_document` | Rejected: violates the facts/interpretation separation; dual-write drift. |
| Embed full prose into `exhibit_semantics` | Rejected: interpretation layer responsibility explodes. |
| Derived composition layer (chosen) | Two canonical files stay untouched; output is regenerable and never authoritative. |

The relationship anchors already exist; the composition materializes a join, it does not invent new authority.

## Decision 2: Native-order spine, not bbox geometry

Linearization uses Docling's native block order (blocks are emitted in reading order) as the spine. Exhibits are inserted as placeholders at their `caption_refs` position, with a bbox-top fallback when an exhibit has no caption. A naive bbox-top re-sort was tried first and scrambled collage pages (7 charts + fragments interleaved nonsensically); native order is far more robust.

## Decision 3: Conservative deduplication

Docling can emit an exhibit's cell text both as table cells and as loose prose blocks. A prose block is suppressed only when BOTH hold: its text exactly equals a table cell on the same page, AND its bbox center sits inside that table's bbox. Text-only matching is unsafe — on the pet case, `texts/41-50` share the boilerplate suffix but are a different, undetected table (発放記録表), not duplicates of the detected one.

## Decision 4: Placeholder convention

Every exhibit appears in the linear stream as a single stable anchor token (for example `⟦exhibit-1⟧`), never as duplicated cell text. Human and RAG projections both read the placeholder; the exhibit structure exists once and is referenced by the anchor. This is also what makes dedup coherent: the stream carries the placeholder, not the table body.

## Decision 5: Confidence-tiered Exhibit Identity Registry

Each exhibit self-registers a number from resources already in the data. Every resulting link carries a confidence from the fixed vocabulary. `unresolved` is a valid, honest outcome — the layer never hard-binds a reference to the geometrically nearest exhibit.

| Tier | Rule | Confidence |
| --- | --- | --- |
| A | The exhibit's own caption/title literally contains "Exhibit N". | `verified` |
| B | Prose description bridge: near an "Exhibit N" occurrence, a preceding-biased window contains the exhibit's distinctive caption head (caption minus boilerplate suffix). Single unambiguous match binds. | `inferred` |
| Label-anchor | A bare "Exhibit N" label block binds to the nearest exhibit object on the same page, subject to the anti-binding guards below. | `hint` |
| D | Document order matched to the ascending Exhibit-number sequence when counts align. | `hint` |

Tested recall on the pet case: Tier B recovered Exhibit 6 (correctly binding the detected 会員基本資料表 table and correctly leaving the undetected Exhibit 5 unresolved); label-anchor recovered Exhibit I and Exhibit 2 on the collage page. Combined 3 of 6 resolved with 100 percent precision (0 false links).

## Decision 6: Anti-binding guards (mandatory with label-anchor)

Label-anchor geometry alone produces false links; three guards are required.

- Separation ratio: the nearest object binds only when its distance is below `SEP_RATIO` times the runner-up distance (default 0.6). Rejects genuinely ambiguous collage labels (Exhibit 3, nearest 99 vs runner-up 101).
- Relative distance cap: reject when the nearest object is farther than a fraction of the label's page height (default 0.20, resolution-independent). Rejects the sole-object-on-page trap (Exhibit 5 label at 303 units on an 842-point page). A prior absolute cap of 150 units was replaced by the page-height fraction to stay resolution-independent.
- Number conflict: an object already bound to number M cannot be bound to a different number N. Independently kills the Exhibit-5-onto-Exhibit-6-table mis-bind.

## Decision 7: Dual-type phantom signalling

A reference resolving to a number with no registered exhibit becomes a phantom record, of one of two types:

- `mentioned-only`: the number appears only in prose, no label block, no object.
- `label-detected-object-undetected`: a label block names the exhibit but Docling detected no object (for example the borderless 発放記録表 for Exhibit 5). This is the stronger re-extraction target: it gives a labelled region to re-scan.

## Deferred (ADR-gated, recorded for a later change)

Analyzed via an adversarial pass; deferred because they are non-deterministic or approach chart digitization:

- Sub-figure segmentation of collage pages (image processing; risks ADR-0002 and CI determinism).
- Phantom-triggered second-pass OCR of a labelled region (the most promising visual method for undetected borderless tables; adds a render+OCR dependency).
- Chart-type classification (visual; scope creep).
- VLM adjudication over cropped page regions (non-deterministic; only viable as an opt-in fallback with mandatory abstention and saved evidence).

## Open decisions

- The `SEP_RATIO` (0.6) and page-height fraction (0.20) coefficients hold on two cases with wide separation margins; they need validation across more cases before being treated as stable.
- The precise trigger boundary for phantom-driven re-extraction (which phantom types, which region bounds) is left to the deferred second-pass-OCR change.
- Whether Tier D ever binds without page/type/local-label corroboration — current stance is hint-only, never a final bind alone.

## Risks

- Threshold coefficients tuned on two cases may not generalize; mitigation is that the discriminating signal is physical separation (near hit vs far mis-bind), not a brittle threshold.
- Tier B caption-head splitting on boilerplate markers can over-truncate Chinese noun phrases into generic nouns; mitigation is a minimum-length and distinctiveness check before a head is used to bind.
