## 1. Linearization spine

- [ ] 1.1 Create `scripts/compose_layout.py` with `linearize(source_doc, semantics)` that walks pages in order and blocks in native Docling order, inserting each exhibit as a placeholder at its `caption_refs` position with a bbox-top fallback. Behavior: a captioned table appears adjacent to its caption; an uncaptioned figure is placed by bbox; prose keeps native order. Verify: unit tests for captioned-insertion, uncaptioned-fallback, and native-order-preserved scenarios.
- [ ] 1.2 Implement conservative dedup: suppress a prose block only when its text exactly equals a same-page table cell AND its bbox center lies inside that table's bbox. Behavior: a true duplicate is suppressed; boilerplate-suffix-sharing blocks outside the table bbox are preserved. Verify: unit tests for the true-duplicate and distinct-content scenarios.

## 2. Exhibit Identity Registry

- [ ] 2.1 Implement Tier A + Tier B binding in `scripts/exhibit_registry.py`: Tier A when an exhibit caption/title contains "Exhibit N" (`verified`); Tier B prose description bridge using a preceding-biased window and a distinctive caption head with a minimum-length and non-generic guard (`inferred`). Behavior: the bridge binds the correct table and leaves a same-suffix undetected exhibit unresolved. Verify: unit tests for caption-number, correct-bridge, and boilerplate-trap-rejected scenarios.
- [ ] 2.2 Implement label-anchor geometric binding (`hint`) with the three anti-binding guards: separation ratio, page-height distance fraction, and number conflict. Behavior: a well-separated near label binds; a sole distant label and a number-conflict label are both rejected. Verify: unit tests for the separated-bind, sole-distant-reject, ambiguous-reject, and number-conflict-reject scenarios.
- [ ] 2.3 Implement dual-type phantom emission: `mentioned-only` versus `label-detected-object-undetected`, the latter carrying the label's region reference. Behavior: a labelled-but-undetected exhibit yields a `label-detected-object-undetected` phantom. Verify: unit tests for both phantom types.

## 3. Projections

- [ ] 3.1 Implement the human `reading_view` renderer: interleaved prose with label-aware formatting, exhibit placeholders with rendered table bodies, and cross-reference links annotated as resolved (with confidence) or unresolved. Behavior: a resolved reference shows its target and confidence; an unresolved reference is marked unresolved. Verify: unit test asserting both annotations appear.
- [ ] 3.2 Implement the `rag_chunks` emitter: one chunk per prose section and per exhibit, each carrying source anchors, exhibit structure, bidirectional relatedness edges, and reading-order neighbors. Behavior: a prose chunk and the exhibit it resolves reference each other. Verify: unit test asserting the bidirectional edge and neighbor edges.

## 4. Integration and regression

- [ ] 4.1 Add a CLI entry that reads the two canonical artifacts and writes the two projections without mutating the inputs, using committed deterministic fixtures (no real PDFs). Behavior: canonical inputs are byte-identical after a run; both projections are produced. Verify: unit test on committed fixtures asserts inputs unchanged and `python3 -m unittest discover -s tests` exits OK.
- [ ] 4.2 Add trimmed synthetic fixtures that reproduce the tested scenarios (description-bridge bind, collage label-anchor with separation, sole-distant reject, dual-type phantom) so the measured pet/Benihana behavior is regression-locked without committing copyrighted PDFs. Behavior: the fixtures reproduce 100 percent precision with the expected resolved/unresolved split. Verify: unit tests over the synthetic fixtures.
