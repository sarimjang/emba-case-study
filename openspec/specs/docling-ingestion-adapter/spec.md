# docling-ingestion-adapter Specification

## Purpose

TBD - created by archiving change 'docling-ingestion-adapter'. Update Purpose after archive.

## Requirements

### Requirement: Docling executable discovery and environment gate

The adapter SHALL resolve a Docling executable before processing and SHALL fail fast when no usable executable or version is available.
Resolution order MUST be: the `--docling-executable` flag, then `~/.pyenv/versions/3.12.0/bin/docling`, then `~/.pyenv/shims/docling`, then `PATH`.
The adapter MUST record the resolved executable and the Docling, docling-core, docling-parse, and docling-ibm-models versions into `ingestion_manifest.json` before extraction begins.

#### Scenario: No Docling executable resolvable

- **WHEN** none of the flag, pyenv paths, or `PATH` yields a runnable Docling executable
- **THEN** the adapter exits non-zero with an actionable error naming the searched locations
- **AND** no `source_document.json` is written

#### Scenario: Version probe fails

- **WHEN** a Docling executable is found but its version command returns non-zero
- **THEN** the adapter exits non-zero before extraction
- **AND** the failure message names the executable that failed the version probe

#### Scenario: Successful gate record

- **WHEN** a Docling executable resolves and its version reads successfully
- **THEN** `ingestion_manifest.json` contains `docling_executable`, `docling_version`, `docling_core_version`, `docling_parse_version`, and `docling_ibm_models_version`

---
### Requirement: Normalized source-document output

The adapter SHALL emit a repo-owned `source_document.json` (`schema_version: source-document/v1`) that records observed source-document facts only and MUST NOT contain business interpretation, accounting interpretation, chart digitization conclusions, subtotal meaning, or EMBA analysis claims.
The document MUST include `schema_version`, `source.path`, `source.mime_type`, `source.provider`, `source.provider_version`, `source.ingested_at`, `source.docling_command`, a `pages` array, and `tables`, `figures`, and `notes` arrays.
Each page MUST include `page_number`, `width`, and `height`.
Each block MUST include `id`, `self_ref`, `type`, `label`, `text`, `page_number`, `bbox`, `parent_ref`, `child_refs`, and `confidence`.

#### Scenario: Required top-level fields present

- **WHEN** ingestion completes on a valid source document
- **THEN** `source_document.json` contains every required top-level field
- **AND** validation exits zero

#### Scenario: Missing required field rejected

- **WHEN** normalized output omits a required top-level field or a page lacks `page_number`, `width`, or `height`
- **THEN** the adapter exits non-zero and names the missing field

#### Scenario: Detected table carries provenance

- **WHEN** Docling reports a table on a page
- **THEN** the normalized table records page provenance and a non-empty cell list
- **AND** the adapter exits non-zero if either is absent

---
### Requirement: Privacy, network, and model-download gate

The adapter SHALL treat ingestion as local processing by default and MUST NOT upload source documents, raw Docling artifacts, normalized JSON, extracted images, or OCR text to any external service.
Network access and model downloads MUST be disabled unless explicitly enabled by `--allow-network` or `--allow-model-downloads`, and the enabled state MUST be recorded in `ingestion_manifest.json`.
When Docling requires a missing model and downloads are disabled, the adapter MUST fail with an actionable error rather than silently changing behavior.

#### Scenario: Model download blocked by default

- **WHEN** Docling needs to download a model and `--allow-model-downloads` was not passed
- **THEN** the adapter exits non-zero with an error explaining how to enable downloads
- **AND** `ingestion_manifest.json` records `model_downloads_allowed: false`

#### Scenario: Gate flags recorded

- **WHEN** ingestion runs with default flags
- **THEN** `ingestion_manifest.json` records `network_allowed: false` and `model_downloads_allowed: false`

---
### Requirement: Output-path containment and artifact-size budget

The adapter SHALL contain all output under the workspace or source directory using the existing generators' containment pattern, and MUST require `--allow-outside-workspace` to write elsewhere.
Canonical normalized output MUST NOT embed base64 page images by default; extracted images MUST be written as file references.
The adapter MUST warn when raw Docling JSON exceeds 25 MB, when `source_document.json` exceeds 10 MB, or when total ingestion artifacts exceed 100 MB.

#### Scenario: Output outside workspace blocked

- **WHEN** `--output-dir` resolves outside the workspace and source directory and `--allow-outside-workspace` is absent
- **THEN** the adapter exits non-zero before writing artifacts

#### Scenario: No embedded base64 by default

- **WHEN** ingestion completes without a debug-embedding flag
- **THEN** `source_document.json` contains no base64 page-image payloads
- **AND** figures reference image files by path

---
### Requirement: Raw Docling JSON stays a local debug artifact

The adapter MAY read and write Docling raw JSON at `outputs/<case-slug>/ingestion/docling/raw.json`, but raw JSON MUST remain a local debug and audit artifact and MUST NOT be embedded into `source_document.json` or any downstream contract.

#### Scenario: Raw JSON written but not embedded

- **WHEN** ingestion completes
- **THEN** `docling/raw.json` exists as a separate file
- **AND** `source_document.json` does not embed the raw Docling schema
