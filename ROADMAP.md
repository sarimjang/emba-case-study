# EMBA Case Study Skill Roadmap

## Current target

Target: build a layout-aware EMBA case ingestion pipeline that preserves source document structure before analysis.

This proposal is: mixed, with destination work in the ingestion layer and foundation work in the export layer.

After completion, will we actually have the target architecture/runtime?

Yes for structure-preserving local ingestion of common EMBA exhibits, if the Docling adapter and exhibit semantic parser are implemented and verified against representative case pages.

If no, what will still be missing?

Chart digitization and highly degraded scans may still require specialized OCR, image preprocessing, or manual review before their numeric data can be treated as reliable.

## Problem statement

The current skill can produce useful EMBA case analysis, but its intermediate `case_spec.json` is an analysis schema rather than a source-document schema.

That means OCR and extraction results are reduced too early into strings, bullet lists, Markdown tables, or generated report tables.

This loses document semantics such as paragraph grouping, table boundaries, page provenance, captions, footers, page numbers, indentation, hierarchy, column grouping, alignment, subtotal lines, and chart/source/note relationships.

Markdown tables are allowed as an export format, but they must not be the canonical representation of OCR or exhibit structure.

## Architectural direction

The repo should move from a single canonical analysis spec to a staged document pipeline.

```text
source file
  -> Docling raw JSON
  -> source_document.json
  -> exhibit_semantics.json
  -> case_spec.json
  -> md / docx / pptx / html
```

`source_document.json` should preserve source structure.

`exhibit_semantics.json` should interpret business exhibit semantics.

`case_spec.json` should remain the decision-analysis schema and should cite source anchors instead of embedding raw OCR text.

## Spectra proposal decomposition map

This roadmap should decompose into separate Spectra proposals at stable contract boundaries.

Each proposal must be small enough to implement and verify independently while preserving the staged pipeline:

```text
source file
  -> Docling raw JSON
  -> source_document.json
  -> exhibit_semantics.json
  -> case_spec.json
  -> md / docx / pptx / html
```

### Proposal: `docling-ingestion-adapter`

Maturity: implementation-ready.

Dependencies: none beyond the confirmed local Docling executable surface and existing output-path safety patterns.

Scope:

- Add `scripts/ingest_with_docling.py`.
- Produce local Docling raw JSON, normalized `source_document.json`, and `ingestion_manifest.json`.
- Enforce the Docling environment gate, privacy gate, network gate, model-download gate, and artifact-size defaults.
- Normalize pages, blocks, tables, figures, notes, bbox values, captions, cell metadata, and page provenance into the repo-owned `source_document.json` contract.
- Keep Docling raw JSON as a local debug artifact only.

Out of scope:

- Exhibit business semantics.
- Case analysis.
- Exporter changes.
- Chart digitization.
- Direct downstream dependence on Docling raw JSON.

### Proposal: `source-document-schema-validation`

Maturity: implementation-ready after `docling-ingestion-adapter` defines the first normalized shape.

Dependencies:

- `docling-ingestion-adapter`

Scope:

- Add shared validation helpers for `source_document.json`.
- Add deterministic fixtures for pages, blocks, bbox values, table cells, captions, headers, footers, and source notes.
- Verify that `source_document.json` preserves source-document facts without business interpretation.

Out of scope:

- Exhibit semantic inference.
- Case evidence migration.
- Export formatting.

### Proposal: `exhibit-semantics-foundation`

Maturity: draft until `source_document.json` anchors and minimum table or figure shapes are stable.

Dependencies:

- `source-document-schema-validation`

Scope:

- Add `scripts/extract_exhibit_semantics.py`.
- Read `source_document.json`, not Docling raw JSON.
- Emit `exhibit_semantics.json`.
- Classify exhibits as `grid_table`, `matrix_table`, `financial_statement`, `hierarchy_table`, `chart`, or `mixed`.
- Preserve source references for every semantic claim.
- Use the semantic confidence vocabulary: `observed`, `inferred`, `verified`, `hint`, and `rejected`.

Out of scope:

- Full table semantics.
- Full hierarchy parsing.
- Chart digitization.
- Exporter migration.

### Proposal: `table-semantics`

Maturity: draft until `exhibit_semantics.json` exhibit anchors and confidence fields are stable.

Dependencies:

- `exhibit-semantics-foundation`

Scope:

- Implement grouped-header table support.
- Classify column group headers, column headers, row headers, and data cells.
- Preserve long text cells, merged headers, blank-cell handling, row and column spans, and nested column hierarchy.
- Parse currency, percentages, ranges, commas, and parenthesized negatives.
- Detect subtotal and total candidates.
- Emit arithmetic validation results where formulas are explicit or inferable.

Out of scope:

- No-grid hierarchy inference.
- Chart and figure handling.
- Case-spec exporter rendering.

### Proposal: `hierarchy-no-grid-semantics`

Maturity: draft until bbox normalization and source-note anchoring are stable.

Dependencies:

- `source-document-schema-validation`
- `exhibit-semantics-foundation`

Scope:

- Infer indentation levels from horizontal bbox clusters.
- Map category headings to child rows.
- Support percentage ranges and value ranges.
- Associate footnotes and source notes with the nearest exhibit.
- Keep uncertain hierarchy assignments as semantic hints rather than hard facts.

Out of scope:

- Financial arithmetic validation unless already provided by `table-semantics`.
- Chart digitization.
- Exporter migration.

### Proposal: `chart-figure-preservation`

Maturity: draft until figure anchors, caption anchors, and nearby text association are stable.

Dependencies:

- `source-document-schema-validation`
- `exhibit-semantics-foundation`

Scope:

- Detect figure blocks and nearby exhibit captions.
- Extract OCR-readable chart titles, axis labels, visible series labels, source text, and note text.
- Preserve the chart image or artifact reference for human verification.
- Mark chart data extraction status as `image_preserved_only` unless a separately verified digitization module exists.

Out of scope:

- Estimating plotted values from visual appearance.
- Populating `case_spec.evidence.chart_data` from unverified chart images.
- Full chart digitization.

### Proposal: `case-spec-source-refs`

Maturity: draft until `source_document.json` and `exhibit_semantics.json` anchor formats are stable.

Dependencies:

- `source-document-schema-validation`
- `exhibit-semantics-foundation`

Scope:

- Add optional structured evidence objects with `source_refs` to `case_spec.json`.
- Preserve backward compatibility with existing string-array fields.
- Enforce the source reference rule: direct observed facts may cite `source_document.json`; interpreted exhibit claims must cite `exhibit_semantics.json`.

Out of scope:

- Moving layout data into `case_spec.json`.
- Requiring all legacy evidence strings to be backfilled.
- Making exporter formatting canonical.

### Proposal: `export-source-ref-rendering`

Maturity: dependent draft until `case-spec-source-refs` is accepted.

Dependencies:

- `case-spec-source-refs`

Scope:

- Update Markdown, DOCX, and PPTX generators to render structured evidence text and source references where available.
- Keep legacy string evidence rendering unchanged.
- Run existing generator compatibility tests.

Out of scope:

- Changing the canonical evidence model beyond the accepted case-spec migration.
- Reading Docling raw JSON from exporters.

### Proposal: `skill-workflow-layout-aware-routing`

Maturity: dependent draft until ingestion and source-ref contracts are stable.

Dependencies:

- `docling-ingestion-adapter`
- `source-document-schema-validation`
- `case-spec-source-refs`

Scope:

- Update `SKILL.md` capability detection to distinguish plain OCR from layout-aware extraction.
- Tell users when a path preserves structure and when it loses structure.
- Route scanned exhibits through Docling-backed ingestion before EMBA analysis when consent is given.
- Require source anchors before trusting exhibit claims.

Out of scope:

- Implementing the ingestion adapter itself.
- Implementing exhibit semantics.
- Weakening privacy, network, or model-download gates.

## Proposal readiness criteria

A Spectra proposal is implementation-ready only when all of the following are true:

- Its upstream schema inputs are named and stable enough for tests.
- Its output contract is stated in repo-owned terms, not provider-native terms.
- Its required anchors are defined well enough that downstream proposals can cite them.
- Its pass/fail assertions can be verified with deterministic, repo-owned fixtures.
- Its privacy, network, model-download, and artifact-size behavior is explicit when it touches source documents or extraction artifacts.
- Its legacy compatibility behavior is explicit when it touches `case_spec.json` or exporters.
- Its out-of-scope items are explicit enough to prevent proposal creep.

A proposal remains draft when any of the following are true:

- It depends on an upstream schema shape that is still changing.
- It requires anchor formats that have not been accepted.
- It depends on semantic confidence fields that have not been accepted.
- It would require downstream code to read Docling raw JSON directly.
- Its acceptance tests require real EMBA case PDFs instead of deterministic repo-owned fixtures.
- It would require chart digitization before a separate verification plan exists.

A proposal is dependent when it is conceptually clear but must not be implemented before one or more upstream proposals stabilize their schemas, anchors, or migration rules.

## Maturity and dependency policy

Draft proposals must not be implemented until their upstream schemas, anchors, and confidence vocabulary are stable enough to support deterministic tests.

Implementation order should follow contract stability:

1. Stabilize local ingestion and `source_document.json`.
2. Validate `source_document.json` with deterministic fixtures.
3. Stabilize `exhibit_semantics.json` anchors and confidence fields.
4. Add table, hierarchy, and chart-preservation semantics.
5. Add structured case-spec source references.
6. Update exporters and skill workflow routing.

A dependent proposal may be written before its dependencies are complete, but it must stay in draft status and must not introduce code that assumes unstable upstream fields.

No proposal may bypass an unstable upstream contract by depending directly on Docling raw JSON, Markdown tables, rendered exports, or visual chart estimates.

## Confirmed local Docling surface

Docling is available on this machine through pyenv, but it is not currently visible through the default shell `PATH`.

Known executable paths are:

- `~/.pyenv/versions/3.12.0/bin/docling`
- `~/.pyenv/shims/docling`

The checked local versions are:

- `docling 2.14.0`
- `docling-core 2.12.1`
- `docling-parse 3.0.0`
- `docling-ibm-models 3.1.0`

The checked CLI supports JSON export, OCR, forced OCR, OCR engine selection, OCR language selection, PDF backend selection, table mode selection, device selection, and document timeout control.

Useful CLI shape:

```bash
~/.pyenv/versions/3.12.0/bin/docling input.pdf \
  --from pdf \
  --to json \
  --output outputs/docling \
  --ocr \
  --table-mode accurate \
  --device cpu \
  --document-timeout 180
```

For large documents, avoid embedding page images in the canonical repo schema unless visual debug output is explicitly requested.

## Docling environment gate

Before running ingestion, the adapter must write an environment gate result to `ingestion_manifest.json`.

Required gate fields:

- `docling_executable`
- `docling_version`
- `docling_core_version`
- `docling_parse_version`
- `docling_ibm_models_version`
- `ocr_enabled`
- `ocr_language`
- `table_mode`
- `device`
- `document_timeout_seconds`
- `model_downloads_allowed`
- `network_allowed`
- `raw_json_path`
- `source_document_path`

Default local gate values:

- executable: `~/.pyenv/versions/3.12.0/bin/docling`
- version: must be readable before ingestion starts
- OCR language: `en` unless explicitly overridden
- table mode: `accurate` for acceptance fixtures
- device: `cpu`
- timeout: `180`
- model downloads allowed: false unless explicitly enabled
- network allowed: false unless explicitly enabled

The adapter must fail fast when the executable path is missing, the version command fails, or requested model/network behavior is not allowed by the gate.

## Privacy, network, and model-download gate

Docling ingestion must be treated as local processing by default.

Required behavior:

- Do not upload source documents, raw Docling artifacts, normalized JSON, extracted images, or OCR text to external services.
- Do not allow network access or model downloads during fixture tests.
- Do not permit first-run model downloads unless the user or test explicitly enables `--allow-model-downloads`.
- Record whether network/model download permission was enabled in `ingestion_manifest.json`.
- If Docling requires a missing model and downloads are disabled, fail with an actionable error instead of silently switching behavior.
- Keep raw Docling JSON in local output only.
- Do not embed raw Docling JSON into `case_spec.json`.
- Treat extracted page images and figure crops as local artifacts with explicit paths, not embedded base64, unless a debug flag enables embedding.

## What Docling can cover

Docling is a good default local provider for the first ingestion layer.

It can preserve or expose document structure such as:

- document pages
- page numbers
- page size
- text blocks
- section headers
- page headers
- page footers
- captions
- tables
- table cells
- row and column indexes
- row spans and column spans
- column header hints
- bounding boxes
- source provenance

Local probing confirmed that a generated PDF with a header, section title, indented paragraph, caption, table, cell grid, and footer produced Docling JSON with page provenance, block labels, table metadata, cell metadata, and bounding boxes.

## What Docling should not be expected to solve alone

Docling should not be treated as the full EMBA exhibit intelligence layer.

It can see structure, but it should not be expected to understand every business, accounting, or chart semantic automatically.

The repo still needs its own adapter and semantic parsers for:

- accounting subtotal and total rows
- parenthesized negative values
- financial statement sections
- indentation-derived hierarchy
- right-aligned amount columns
- borderless or weakly bordered tables
- multi-row and grouped headers
- source and note association
- chart axis labels
- chart series labels
- chart data digitization status
- exhibit-level numeric checks

## Exhibit classes to support

### Grid table

This class includes clear row and column boundaries.

Examples include product profitability tables and service comparison tables.

Expected support:

- preserve table cells
- preserve long text inside cells
- preserve row labels
- preserve column labels
- preserve captions
- preserve page provenance

### Matrix table with grouped headers

This class includes column groups that span multiple subcolumns.

Examples include driver-hours tables with grouped headers such as `1 to 15 hours/week`, `16 to 34`, `35 to 49`, and `Over 50`.

Expected support:

- represent header cells with `col_span`
- classify cells as `column_group_header`, `column_header`, `row_header`, or `data`
- preserve nested column hierarchy
- avoid flattening grouped headers into ambiguous Markdown columns

### Financial statement table

This class includes accounting rows, subtotals, totals, signs, underlines, and amount columns.

Examples include Wilkerson income statements and overhead breakdowns.

Expected support:

- infer amount columns from alignment and bbox clusters
- parse parenthesized amounts as negative values
- detect subtotal and total candidates
- preserve horizontal rule or underline hints when available
- attach arithmetic validation results

### Hierarchy table without full grid lines

This class includes category headings, indented child rows, and value ranges.

Examples include traditional restaurant economics exhibits with revenue, cost, operating expense, fixed cost, and range percentage sections.

Expected support:

- infer indentation levels from bbox positions
- preserve parent-child row relationships
- classify section headers and leaf rows
- parse value ranges such as `70.0-80.0`
- preserve notes and sources near the exhibit

### Chart or figure exhibit

This class includes visual charts, axes, gridlines, series labels, notes, and sources.

Examples include line charts of active Uber drivers by service type.

Expected support:

- preserve the figure area as a block
- extract chart title and exhibit caption when OCR can read them
- extract x-axis and y-axis labels when OCR can read them
- extract visible series labels when OCR can read them
- associate source and note text with the figure
- mark numeric data extraction as `image_preserved_only`, `partially_digitized`, or `fully_digitized`

Chart digitization should be opt-in or separately verified.

The skill must not fabricate chart data from the visual alone.

## Proposed canonical structures

### `source_document.json`

`source_document.json` should preserve stable source-document structure independent of Docling's native schema.

Suggested top-level shape:

```json
{
  "schema_version": "source-document/v1",
  "source": {
    "path": "case.pdf",
    "mime_type": "application/pdf",
    "provider": "docling",
    "provider_version": "2.14.0"
  },
  "pages": [
    {
      "page_number": 1,
      "width": 612.0,
      "height": 792.0,
      "blocks": []
    }
  ],
  "tables": [],
  "figures": [],
  "notes": []
}
```

Each block should keep a stable `id`, source `self_ref`, block `type`, label, text, page number, bbox, parent reference, child references, and confidence if available.

Each table should keep caption references, cell grid, row spans, column spans, header flags, bbox values, and page provenance.

Each figure should keep caption references, page provenance, bbox values, nearby source text, nearby note text, and data extraction status.

### `exhibit_semantics.json`

`exhibit_semantics.json` should interpret source blocks as EMBA exhibits.

Suggested top-level shape:

```json
{
  "schema_version": "exhibit-semantics/v1",
  "exhibits": [
    {
      "id": "exhibit-5",
      "title": "A Comparison of a Subset of the Different Uber Services",
      "type": "grid_table",
      "source_refs": ["docling:#/tables/0"],
      "semantic_hints": {},
      "checks": []
    }
  ]
}
```

The semantic layer should support `grid_table`, `matrix_table`, `financial_statement`, `hierarchy_table`, `chart`, and `mixed` exhibit types.

### `case_spec.json`

`case_spec.json` should stay focused on EMBA analysis.

It should gain source references rather than raw layout data.

Suggested additive shape:

```json
{
  "evidence": {
    "quantitative_signals": [
      {
        "claim": "UberX driver growth accelerates after 2014.",
        "source_refs": ["exhibit-7"]
      }
    ]
  }
}
```

Existing generators can continue accepting legacy string arrays during migration.

## Cross-proposal contracts

These contracts apply across all Spectra proposals created from this roadmap.

- Docling raw JSON is a local debug and audit artifact only.
- Downstream repo-owned steps must depend on `source_document.json` or later repo-owned schemas, not Docling raw JSON.
- `source_document.json` records observed source-document facts only: pages, block labels, raw text, bounding boxes, table cells, captions, headers, footers, parent and child references, provider provenance, and nearby notes or sources.
- `source_document.json` must not contain business interpretation, accounting interpretation, chart digitization conclusions, subtotal meaning, or EMBA analysis claims.
- `exhibit_semantics.json` records interpretation over source-document facts and must preserve source references for every inferred claim.
- Semantic confidence must distinguish `observed`, `inferred`, `verified`, `hint`, and `rejected`.
- `case_spec.json` remains the EMBA decision-analysis schema and must not become the canonical layout or OCR representation.
- `case_spec.json` may cite `source_document.json` anchors only for direct textual or observed facts.
- Claims that interpret an exhibit must cite `exhibit_semantics.json` anchors.
- Examples of exhibit interpretation include subtotal meaning, table ranking, row role, grouped header meaning, financial metric derivation, chart trend interpretation, and arithmetic validation.
- Exporters may render source references, but export formatting must not become the canonical evidence structure.
- Markdown tables are allowed as an export format but must not be the canonical representation of OCR or exhibit structure.
- Chart figures may be preserved and labeled in the first chart scope, but plotted numeric values must not be estimated from visual appearance.
- `case_spec.evidence.chart_data` may only come from explicit table numbers, explicit numeric labels, verified external or source data, or a future separately verified chart digitization module.

## Development phases

### Phase 1: Docling adapter foundation

Add a script such as `scripts/ingest_with_docling.py`.

Phase 1 implementation contract:

CLI:

```bash
python3 scripts/ingest_with_docling.py INPUT \
  --output-dir outputs/<case-slug>/ingestion \
  --docling-executable ~/.pyenv/versions/3.12.0/bin/docling \
  --from pdf \
  --ocr \
  --ocr-lang en \
  --table-mode accurate \
  --device cpu \
  --document-timeout 180
```

Required arguments:

- `input`: source document path.
- `--output-dir`: directory for ingestion artifacts.
- `--docling-executable`: explicit Docling executable path, with auto-discovery fallback to `~/.pyenv/versions/3.12.0/bin/docling`, `~/.pyenv/shims/docling`, then `PATH`.
- `--from`: source format when needed by Docling.
- `--ocr` / `--no-ocr`: explicit OCR choice.
- `--ocr-lang`: OCR language code, default `en`.
- `--table-mode`: `fast` or `accurate`, default `accurate` for exhibit-heavy acceptance fixtures.
- `--device`: default `cpu`.
- `--document-timeout`: default `180`.
- `--allow-outside-workspace`: same safety override pattern as existing generators.

Required output paths:

- `outputs/<case-slug>/ingestion/docling/raw.json`
- `outputs/<case-slug>/ingestion/source_document.json`
- `outputs/<case-slug>/ingestion/ingestion_manifest.json`

Minimum `source_document.json` fields:

- `schema_version`
- `source.path`
- `source.mime_type`
- `source.provider`
- `source.provider_version`
- `source.ingested_at`
- `source.docling_command`
- `pages[].page_number`
- `pages[].width`
- `pages[].height`
- `pages[].blocks[]`
- `tables[]`
- `figures[]`
- `notes[]`

Minimum block fields:

- `id`
- `self_ref`
- `type`
- `label`
- `text`
- `page_number`
- `bbox`
- `parent_ref`
- `child_refs`
- `confidence`

Phase 1 pass/fail assertions:

- Fails if Docling executable cannot be found or version cannot be read.
- Fails if output path is outside the workspace or source directory unless `--allow-outside-workspace` is passed.
- Fails if `source_document.json` omits required top-level fields.
- Fails if any page lacks `page_number`, `width`, or `height`.
- Fails if a detected table has no page provenance or cell list.
- Fails if canonical normalized output embeds base64 page images by default.
- Passes when the generated PDF fixture produces raw Docling JSON, normalized `source_document.json`, and an ingestion manifest.

The script should call local Docling through the known pyenv path or a discovered executable path.

The script should output Docling raw JSON and a normalized `source_document.json`.

The script should support PDF, image, DOCX, PPTX, HTML, Markdown, and XLSX when Docling supports them.

The script should default to safe local output paths using the existing output-path containment approach.

The script should allow `--table-mode accurate` for exhibit-heavy cases.

The script should allow OCR language configuration.

The script should avoid embedding base64 page images into canonical normalized output by default.

### Phase 2: Source document schema and validation

Add shared validation helpers for `source_document.json`.

Add fixture-driven tests for pages, blocks, bbox values, table cells, captions, headers, footers, and source notes.

Add one generated PDF fixture with a title, section header, paragraph, table, caption, page header, and page footer.

Add one image fixture for a scanned exhibit-style table if licensing and repo size allow it.

### Phase 3: Exhibit semantic parser

Add `scripts/extract_exhibit_semantics.py`.

Start with deterministic rules over normalized Docling structure.

Classify exhibit blocks into `grid_table`, `matrix_table`, `financial_statement`, `hierarchy_table`, `chart`, or `mixed`.

Preserve all source references back to `source_document.json`.

Emit semantic hints instead of overclaiming certainty.

### Phase 4: Table semantics

Implement grouped-header table support first.

Implement row-header and column-header role detection.

Implement long text cell preservation.

Implement merged header and blank-cell handling.

Implement financial amount parsing for currency, percentages, ranges, commas, and parenthesized negatives.

Implement subtotal and total candidate detection.

Add arithmetic validation for financial exhibits where formulas are explicit or inferable.

### Phase 5: Hierarchy and no-grid exhibits

Infer indentation levels from horizontal bbox clusters.

Map category headings to child rows.

Support percentage ranges and value ranges.

Associate footnotes and source notes with the nearest exhibit.

Keep uncertain hierarchy assignments as hints rather than hard facts.

### Phase 6: Chart and figure support

Detect figure blocks and nearby exhibit captions.

Extract chart title, axis labels, visible series labels, source, and note text when OCR can read them.

Preserve the chart image or a reference to it for human verification.

Do not digitize line or bar values by default.

The first chart implementation only preserves figure areas, OCR-readable labels, captions, source text, and note text.

`case_spec.evidence.chart_data` may only be populated from explicit table numbers, explicit numeric labels, verified external or source data, or a future separately verified chart digitization module.

Agents must not estimate chart data by visually guessing from a plotted line or bar.

Add optional chart digitization only after a separate verification plan exists.

See `docs/adr/0002-defer-chart-digitization.md`.

### Phase 7: Skill workflow update

Update `SKILL.md` capability detection to distinguish plain OCR from layout-aware extraction.

Tell users when the current path can preserve structure and when it will lose structure.

Route scanned exhibits through Docling-backed ingestion before EMBA analysis when consent is given.

Require source anchors from `source_document.json` or `exhibit_semantics.json` before trusting exhibit claims.

### Phase 8: Case spec and export compatibility

Add optional structured evidence objects with `source_refs` to `case_spec.json`.

Keep backward compatibility with existing string-array evidence fields while generators are migrated.

Migration rules for evidence fields:

Existing generators currently expect string arrays such as:

- `evidence.quantitative_signals`
- `evidence.internal_checks`
- `evidence.external_checks`
- `evidence.open_issues`
- `case.source_notes`
- `appendix.references`
- `appendix.assumptions`
- `appendix.discussion_questions`

During migration, each field may accept either legacy strings or structured evidence objects.

Structured evidence object shape:

```json
{
  "text": "Revenue growth accelerates after the new segment launch.",
  "source_refs": ["source-document/v1#/tables/table-3/cells/r2c4"],
  "confidence": "medium",
  "evidence_type": "quantitative_signal"
}
```

Migration rules:

- Legacy string items remain valid and render exactly as today.
- Structured evidence objects must contain non-empty `text`.
- `source_refs` must be an array of source anchors when available.
- `case_spec.json` may cite `source_document.json` anchors only for direct textual or observed facts.
- Claims that interpret an exhibit must cite `exhibit_semantics.json` anchors.
- Examples of exhibit interpretation include subtotal meaning, table ranking, row role, grouped header meaning, financial metric derivation, chart trend interpretation, and arithmetic validation.
- Exporters render `text` first and append source references where supported.
- Validators should reject mixed non-string, non-object list items.
- New ingestion-backed analysis should prefer structured objects.
- Do not require all legacy string evidence to be backfilled before existing MD, DOCX, and PPTX exports continue working.
- Do not move layout data into `case_spec.json`; keep layout in `source_document.json` and exhibit interpretation in `exhibit_semantics.json`.

Update Markdown, DOCX, and PPTX generators to render source references where available.

Do not let export formatting become the canonical evidence structure.

## Roadmap planning stop condition

Stop decomposing this roadmap when the Spectra proposals cover the stable contract boundaries and no proposal needs to know implementation details from a non-adjacent pipeline layer.

The roadmap should not become a full proposal spec for every phase.

Detailed implementation belongs in individual Spectra proposals once their dependencies are stable.

Planning is sufficient when each proposal has:

- a name
- maturity status
- dependencies
- scope
- out-of-scope items
- upstream inputs
- downstream outputs
- acceptance fixture expectations
- cross-proposal contracts it must preserve

If adding more roadmap detail would duplicate proposal-level task lists, test cases, or file-by-file implementation steps, stop and move that detail into the relevant Spectra proposal instead.

## Verification plan

Acceptance fixtures must map directly to exhibit classes:

Acceptance fixtures must be deterministic and repo-owned.

Generated or repo-owned fixtures are required for CI acceptance.

Real EMBA case PDFs may be used as exploratory evaluation or manual-review corpora, but they must not be required for the first implementation's pass/fail acceptance tests.

Each acceptance fixture should isolate one exhibit class rather than trying to reproduce a full case packet.

- `fixtures/exhibits/grid_table.pdf`: clear grid with caption, long text cell, row labels, column labels, source note.
- It must produce one `grid_table` exhibit with table cells, caption refs, source refs, and page provenance.
- `fixtures/exhibits/grouped_matrix_table.pdf`: grouped column headers with spans such as `1 to 15 hours/week`, `16 to 34`, `35 to 49`, and `Over 50`.
- It must preserve `col_span`, classify group headers separately from leaf headers, and avoid Markdown-only flattening.
- `fixtures/exhibits/financial_statement.pdf`: accounting-style rows with subtotal, total, parenthesized negative, percentage or currency values, and underline or rule cues where available.
- It must parse negative values, mark subtotal and total candidates, and emit arithmetic check results.
- `fixtures/exhibits/hierarchy_no_grid_table.pdf`: borderless or weak-grid hierarchy with section rows, indented child rows, value ranges, footnotes, and source notes.
- It must infer indentation levels and preserve uncertain parent-child mappings as semantic hints.
- `fixtures/exhibits/chart_figure.pdf`: chart or figure with title, caption, visible axis labels, visible series labels, source, and note.
- It must preserve the figure area and mark data extraction as `image_preserved_only` unless explicit digitization is implemented and verified.

Run unit tests for schema validation and adapter normalization.

Run Docling adapter smoke tests with a generated local PDF fixture.

Run at least one table-heavy exhibit test with grouped headers.

Run at least one financial-statement exhibit test with parenthesized values and totals.

Run at least one chart exhibit test that verifies caption, axis labels, source, and note extraction without claiming digitized values.

Run existing generator tests after each schema change.

Current fast verification command:

```bash
python3 -m unittest discover -s tests
```

## Non-goals for the first implementation

Do not promise perfect OCR for degraded scans.

Do not promise full chart data digitization.

Do not make Markdown the source of truth for tables.

Do not mix Docling raw schema directly into EMBA analysis output.

Do not remove the existing `case_spec.json` export path until compatibility tests cover legacy and structured evidence.

## Open implementation notes

## Performance and artifact-size budget

Initial implementation budget:

- Acceptance fixtures: max 5 pages each.
- Smoke-test source document: max 2 MB.
- General Phase 1 default document budget: max 50 pages or 25 MB unless explicitly overridden.
- Default document timeout: 180 seconds.
- Accurate table-mode timeout warning threshold: 60 seconds.
- Raw Docling JSON warning threshold: 25 MB.
- Normalized `source_document.json` warning threshold: 10 MB.
- Canonical `case_spec.json` remains subject to the existing 5 MB validation limit.
- Extracted images must be file references by default.
- Individual image warning threshold: 5 MB.
- Total ingestion artifact warning threshold: 100 MB.

`--table-mode accurate` should be the acceptance-test default for exhibit-heavy fixtures, but the adapter must warn that it may be materially slower than fast mode on large documents.

The current shell uses `/opt/homebrew/bin/python3`, which does not have Docling installed.

Docling currently needs the pyenv Python environment at `~/.pyenv/versions/3.12.0/bin/python`.

The adapter should either discover Docling executables robustly or document the required environment path.

The first PDF Docling run may be slow because model and transformer caches can initialize or migrate.

`--table-mode accurate` is preferable for difficult EMBA exhibit tables, but it has higher runtime cost.
