# chart-figure-preservation Specification

## Purpose

TBD - created by archiving change 'chart-figure-preservation'. Update Purpose after archive.

## Requirements

### Requirement: Figure preservation with caption association

The chart layer SHALL preserve each figure block as a `chart` exhibit that keeps a reference to the figure artifact and associates a nearby exhibit caption when one exists.
The exhibit MUST record an `image_ref` pointing at the figure's source anchor (its `self_ref`), and MUST set a `title` from an associated caption when available.

#### Scenario: Figure preserved with image reference

- **WHEN** a source figure is processed
- **THEN** the chart exhibit records an `image_ref` to the figure's `self_ref`

#### Scenario: Caption associated as title

- **WHEN** a figure has a caption reference resolvable to caption text
- **THEN** the chart exhibit's `title` is that caption text

---
### Requirement: OCR-readable label preservation without digitization

The chart layer SHALL preserve OCR-readable chart labels (title, axis labels, visible series labels) and source/note text when they are available from the source document, recording them as hints with source references, and MUST set the exhibit's `data_extraction_status` to `image_preserved_only`.
The chart layer MUST NOT estimate or emit plotted numeric series values, and MUST NOT populate `case_spec.evidence.chart_data` from a chart image (`docs/adr/0002-defer-chart-digitization.md`).

#### Scenario: Labels preserved as hints

- **WHEN** OCR-readable labels are available near the figure
- **THEN** they are recorded as chart-label hints with source references

#### Scenario: Extraction status is image-preserved-only

- **WHEN** a chart exhibit is produced
- **THEN** its `data_extraction_status` is `image_preserved_only`

#### Scenario: No plotted values fabricated

- **WHEN** a chart exhibit is produced from an image with no explicit numbers
- **THEN** the exhibit contains no numeric series values
