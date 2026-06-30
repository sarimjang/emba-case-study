## 1. Evidence-item validation helper

- [x] 1.1 Implement Extend validation with an evidence-item helper, not a new schema, satisfying the Backward-compatible structured evidence requirement: add `_expect_evidence_list(value, label)` to `scripts/case_spec_utils.py` that accepts each item as a legacy string or a structured object, and use it for the eight evidence/appendix fields. Behavior: an all-string field still validates; a mixed string+object field validates; an item that is neither string nor object is rejected naming the field path. Verify: unit tests for legacy-string, coexist, and non-string-non-object scenarios.

## 2. Structured object shape

- [x] 2.1 Implement the Structured evidence object shape requirement: require non-empty `text`; when present, `source_refs` is an array of non-empty strings and `confidence` is in {observed, inferred, verified, hint, rejected}. Behavior: a valid object passes; empty `text` and out-of-vocabulary `confidence` are rejected naming the field path. Verify: unit tests for valid-object, empty-text, and invalid-confidence scenarios.

## 3. Source reference rule and layout guard

- [x] 3.1 Implement Source Reference Rule enforced by anchor-shape inspection, satisfying the Source Reference Rule enforcement requirement: an object marked `evidence_type=="exhibit_interpretation"` or `interprets_exhibit: true` must cite at least one exhibit-semantics anchor; observed facts may cite source-document anchors. Behavior: an interpretation object citing only source-document anchors is rejected; an observed-fact object citing a source-document anchor passes. Verify: unit tests for the interpretation-requires-exhibit-anchor and observed-fact scenarios.
- [x] 3.2 Implement the Layout/OCR denylist on evidence objects: reject reserved layout keys (`bbox`, `cells`, `page_number`, `self_ref`) inside evidence objects. Behavior: an evidence object carrying `bbox` or `cells` is rejected naming the disallowed key. Verify: unit test for the embedded-layout-rejected scenario.

## 4. Regression

- [x] 4.1 Confirm backward compatibility and no regression: the existing all-string `tests/test_case_spec_utils.py` suite stays green and existing case specs validate unchanged. Behavior: legacy specs continue to validate and render-relevant fields are untouched. Verify: `python3 -m unittest discover -s tests` exits OK.
