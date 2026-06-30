## 1. Capability detection and ingest routing

- [x] 1.1 Implement Edit existing workflow sections rather than add a parallel flow for the Capability detection distinguishes layout-aware extraction requirement: extend `SKILL.md` Step 0/1 to name a layout-aware Docling path distinct from plain OCR and disclose that the plain path loses structure while the layout-aware path preserves it via `source_document.json`. Behavior: the capability brief offers the layout-aware option with its structure trade-off. Verify: a content test asserts `SKILL.md` references `ingest_with_docling.py`, `source_document.json`, and the structure-preservation disclosure.
- [x] 1.2 Implement Reference the pipeline by path, reuse the existing consent/checkpoint pattern for the Consent-gated layout-aware ingestion of scanned exhibits requirement: extend `SKILL.md` Step 1 to route scanned/image-only exhibits through `scripts/ingest_with_docling.py` only after consent, reusing `references/delivery-and-consent.md`, without weakening gates. Behavior: the workflow requires explicit consent before adapter ingestion and preserves privacy/network/model-download gates. Verify: a content test asserts the consent requirement and that the text does not instruct relaxing gates.

## 2. Source-anchor requirement

- [x] 2.1 Implement the Source anchors required before trusting exhibit claims requirement: extend `SKILL.md` Step 5 to require a `source_document.json` or `exhibit_semantics.json` anchor before an exhibit interpretation is trusted, stating that interpretations cite `exhibit_semantics.json` and observed facts cite `source_document.json`. Behavior: an unanchored exhibit interpretation is not treated as validated evidence. Verify: a content test asserts `SKILL.md` Step 5 references both anchor types and the anchor-before-trust rule.

## 3. Verification

- [x] 3.1 Add a deterministic content test for the `SKILL.md` routing guidance and confirm no regression. Behavior: the test pins the layout-aware disclosure, consent-gated adapter routing, and source-anchor requirement; the full suite stays green. Verify: `python3 -m unittest discover -s tests` exits OK.
