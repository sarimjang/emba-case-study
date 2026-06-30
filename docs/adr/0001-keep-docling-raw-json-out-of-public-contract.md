# ADR-0001: Keep Docling raw JSON out of the public contract

## Status

Accepted

## Context

The roadmap introduces a staged ingestion pipeline:

```text
source file
  -> Docling raw JSON
  -> source_document.json
  -> exhibit_semantics.json
  -> case_spec.json
```

Docling raw JSON is valuable for debugging and audit because it preserves provider-specific extraction output.

However, Docling's native schema is an upstream provider schema, not a stable contract owned by this repo.

If exhibit parsing, case analysis, or exporters depend directly on Docling raw JSON, future Docling upgrades or provider changes would create broad breakage across the system.

## Decision

Docling raw JSON is a local debug and audit artifact only.

It is not a public contract for this repo.

All downstream repo-owned steps must depend on `source_document.json` or later repo-owned schemas.

`source_document.json` is the adapter boundary that normalizes provider output into the stable source-document contract.

## Consequences

`scripts/ingest_with_docling.py` may read and write Docling raw JSON.

Adapter tests may inspect Docling raw JSON only to verify normalization behavior.

`scripts/extract_exhibit_semantics.py` must read `source_document.json`, not Docling raw JSON.

`case_spec.json` may cite `source_document.json` or `exhibit_semantics.json` anchors, but must not embed or depend on Docling raw schema.

Exporters must not read Docling raw JSON.

Provider-specific schema drift is contained inside the ingestion adapter.

## Alternatives considered

### Let every downstream parser read Docling raw JSON

Rejected because it spreads provider-specific coupling across exhibit semantics, analysis, and export code.

### Use Docling raw JSON as the only canonical source document

Rejected because the repo needs a stable provider-neutral contract and may later support another extractor.
