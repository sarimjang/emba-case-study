## Context

This change adds the bottom layer of the staged pipeline described in `ROADMAP.md` ("Architectural direction"): `source file -> Docling raw JSON -> source_document.json`.
Docling is installed only under pyenv (`~/.pyenv/versions/3.12.0/bin/docling`, `docling 2.14.0`) and is not on the active shell `PATH` (`ROADMAP.md` "Confirmed local Docling surface").
The repo already has an output-path containment / `--allow-outside-workspace` safety pattern in `scripts/generate_case_*.py` that this adapter reuses.
The binding constraints are ADR-0001 (raw JSON out of the public contract) and the privacy/network/model-download and artifact-size gates in `ROADMAP.md`.

## Goals / Non-Goals

**Goals:**

- Produce a stable, repo-owned `source-document/v1` contract that downstream changes 2–9 depend on.
- Contain all provider-specific schema drift inside this adapter (ADR-0001).
- Make every gate (environment, privacy, network, model-download, size) observable in `ingestion_manifest.json`.

**Non-Goals:**

- Exhibit semantics, case analysis, exporter changes, chart digitization (downstream changes / ADR-0002).
- Schema-validation helpers and deterministic fixtures (owned by `source-document-schema-validation`).
- Adding Docling to repo dependency manifests.

## Decisions

### Subprocess invocation over Python import

Invoke Docling as a CLI subprocess rather than importing `docling` in-process.
Rationale: Docling lives in a different Python environment (pyenv 3.12.0) than the active shell `python3` (`/opt/homebrew/bin/python3`, no Docling). A subprocess boundary lets the adapter run under the repo's interpreter while delegating extraction to the pyenv executable, and keeps Docling out of repo dependency manifests.
Alternative considered: import Docling directly — rejected because it forces the repo onto the pyenv interpreter and couples the test suite to a heavy optional dependency.

### Executable resolution chain with explicit override

Resolve in order: `--docling-executable` flag, pyenv versioned path, pyenv shim, then `PATH`.
Rationale: the confirmed install is invisible to `PATH`; auto-discovery avoids forcing every caller to pass the flag while still allowing override.
Alternative considered: require the flag always — rejected as poor ergonomics for the known-good local default.

### Normalize into source-document/v1, never re-expose raw schema

The adapter is the single ADR-0001 boundary: it reads Docling raw JSON and emits the repo-owned contract. Raw JSON is persisted beside the normalized output for audit but is never embedded.
Alternative considered: pass Docling raw JSON downstream — rejected by ADR-0001 (spreads provider coupling).

### Fail-fast gating with a manifest record

Every gate decision (environment, network, model-download) is both enforced and written to `ingestion_manifest.json` before/around extraction, so a run is auditable after the fact.
Alternative considered: enforce silently — rejected because the privacy posture must be inspectable.

## Implementation Contract

- **Behavior**: `python3 scripts/ingest_with_docling.py INPUT --output-dir DIR [...]` produces, under `outputs/<case-slug>/ingestion/`: `docling/raw.json`, `source_document.json`, `ingestion_manifest.json`. On any gate failure the command exits non-zero with an actionable message and writes no normalized output.
- **Interface / data shape**:
  - CLI flags: `input` (positional), `--output-dir`, `--docling-executable`, `--from`, `--ocr`/`--no-ocr`, `--ocr-lang` (default `en`), `--table-mode` (`fast`|`accurate`, default `accurate`), `--device` (default `cpu`), `--document-timeout` (default `180`), `--allow-outside-workspace`, `--allow-network`, `--allow-model-downloads`.
  - `source_document.json`: `schema_version` = `source-document/v1`; `source.{path,mime_type,provider,provider_version,ingested_at,docling_command}`; `pages[].{page_number,width,height,blocks[]}`; `blocks[].{id,self_ref,type,label,text,page_number,bbox,parent_ref,child_refs,confidence}`; top-level `tables[]`, `figures[]`, `notes[]`.
  - `ingestion_manifest.json`: gate fields per `ROADMAP.md` "Docling environment gate" (`docling_executable`, four version fields, `ocr_enabled`, `ocr_language`, `table_mode`, `device`, `document_timeout_seconds`, `model_downloads_allowed`, `network_allowed`, `raw_json_path`, `source_document_path`).
- **Failure modes**: missing/unrunnable executable → non-zero, names searched paths; version probe fails → non-zero; required field missing → non-zero, names field; table without provenance/cells → non-zero; output outside workspace without override → non-zero; model needed but downloads disabled → non-zero with enable instructions. All failures surface; none silently degrade.
- **Acceptance criteria**: a generated multi-element PDF fixture yields all three artifacts; the spec scenarios in `specs/docling-ingestion-adapter/spec.md` hold; `python3 -m unittest discover -s tests` stays green.
- **Scope boundaries**: in scope — invocation, normalization, gating, size warnings, raw-JSON persistence. Out of scope — schema-validation helpers/fixtures (change 2), any semantic interpretation, exporter or `case_spec.json` changes.

## Risks / Trade-offs

- [First Docling run is slow due to model/cache init] → document expected latency; keep `--document-timeout` default at 180s; warn when `accurate` table mode exceeds the 60s threshold.
- [Docling native schema drift across versions] → containment in this adapter plus recorded `provider_version` limits blast radius; downstream never sees raw schema.
- [pyenv path hard-coded as a default] → mitigated by the resolution chain and explicit `--docling-executable` override.

## Migration Plan

Additive only — new script and new output tree. No existing artifact, generator, or `case_spec.json` path changes. Rollback is deletion of the new script and outputs.

## Open Questions

- Exact normalization mapping for figure `notes`/`source` proximity is finalized when the first Docling fixture output is inspected; this does not block the `source-document/v1` field contract above.
