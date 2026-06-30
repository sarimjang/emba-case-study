# Domain Context

## Glossary

### Source Document

A normalized representation of observed source-document facts.

It records what extraction observed, such as pages, block labels, raw text, bounding boxes, table cells, captions, headers, footers, parent and child references, and provider provenance.

It must not contain business interpretation, accounting interpretation, chart digitization conclusions, subtotal meaning, or EMBA analysis claims.

### Exhibit Semantics

An interpretation layer over a Source Document that explains what an exhibit appears to mean.

It may classify table type, row roles, column groups, subtotal candidates, negative amount parsing, chart labels, source and note association, and arithmetic checks.

It must preserve source references back to the Source Document for every inferred claim.

### Case Spec

The canonical EMBA analysis contract consumed by report exporters.

It records decision-pivot analysis, evidence claims, options, recommendations, appendix material, and source references that connect analysis back to Exhibit Semantics or Source Document anchors.

It must not become the canonical layout or OCR representation.

### Semantic Confidence

The confidence vocabulary used by Exhibit Semantics to separate source facts from interpretation strength.

`observed` means the value is copied from Source Document facts.

`inferred` means a parser derived the value from layout, proximity, labels, or formatting.

`verified` means the inference is supported by arithmetic, structural rules, or explicit human review.

`hint` means the inference may help analysis but cannot independently support a Case Spec evidence claim.

`rejected` means a candidate interpretation was considered and ruled out.

### Source Reference Rule

Case Spec evidence may cite Source Document anchors only for direct textual or observed facts.

Any claim that interprets an exhibit must cite Exhibit Semantics anchors.

Examples of exhibit interpretation include subtotal meaning, table ranking, row role, grouped header meaning, financial metric derivation, chart trend interpretation, and arithmetic validation.
