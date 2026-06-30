## 1. Shared rendering helper

- [x] 1.1 Implement Single shared helper in case_spec_utils, applied at the bullet layer, satisfying the Shared evidence rendering helper requirement: add `evidence_item_text(item)` to `scripts/case_spec_utils.py`. Behavior implementing Strings pass through untouched; objects get a reference suffix — a string returns verbatim; a structured object returns its `text` then a `(sources: ...)` suffix when `source_refs` is non-empty, and only `text` when absent. Verify: unit tests for string-unchanged, object-with-refs, and object-without-refs scenarios.

## 2. Generators render via the helper

- [x] 2.1 Route the Markdown generator's `bullets` rendering through `evidence_item_text`, satisfying Generators render structured evidence across formats for Markdown. Behavior: a structured evidence item renders its text then its reference; an all-string spec renders unchanged. Verify: unit test asserting the structured item's text + ref appear in the Markdown output and a string-only render is unchanged.
- [x] 2.2 Route the DOCX generator's `add_bullets` rendering through `evidence_item_text`. Behavior: structured evidence text and reference appear in the DOCX paragraphs; legacy strings unchanged. Verify: unit test inspecting the rendered DOCX paragraph text for the item text and ref.
- [x] 2.3 Route the PPTX generator's `add_bullets` rendering through `evidence_item_text`. Behavior: structured evidence text and reference appear in PPTX bullet text; legacy strings unchanged. Verify: unit test inspecting the rendered PPTX text frames for the item text and ref.

## 3. Compatibility and regression

- [x] 3.1 Confirm legacy spec output is unchanged and no Docling raw JSON is read by the generators. Behavior: an all-string case spec renders identically across MD/DOCX/PPTX after the change. Verify: unit test comparing a string-only render against the expected legacy output, and `python3 -m unittest discover -s tests` exits OK.
