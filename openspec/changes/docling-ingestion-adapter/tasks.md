## 1. Adapter scaffold and CLI

- [x] 1.1 Create `scripts/ingest_with_docling.py` with the CLI flags from the Implementation Contract (`input`, `--output-dir`, `--docling-executable`, `--from`, `--ocr/--no-ocr`, `--ocr-lang`, `--table-mode`, `--device`, `--document-timeout`, `--allow-outside-workspace`, `--allow-network`, `--allow-model-downloads`). Behavior: running with `--help` lists every flag with documented defaults (`accurate`, `cpu`, `180`, `en`). Verify: `python3 scripts/ingest_with_docling.py --help` exits zero and shows all flags.
- [x] 1.2 Implement Subprocess invocation over Python import: build and run the Docling command in a child process under the resolved pyenv executable. Behavior: the exact command string is captured into `source.docling_command`. Verify: unit test asserts the recorded command matches the constructed argv.

## 2. Executable resolution and environment gate

- [x] 2.1 Implement the Executable resolution chain with explicit override and the Docling executable discovery and environment gate: resolve flag → pyenv versioned path → pyenv shim → `PATH`, then probe versions. Behavior: a missing or unrunnable executable exits non-zero naming the searched paths; a failed version probe exits non-zero before extraction. Verify: unit tests for the no-executable and version-probe-fail scenarios assert non-zero exit and message content.
- [x] 2.2 Record the environment gate into `ingestion_manifest.json`: `docling_executable` plus the four version fields, `ocr_*`, `table_mode`, `device`, `document_timeout_seconds`. Behavior: a successful run produces a manifest containing every required gate field. Verify: unit test loads the manifest and asserts presence of each field.

## 3. Normalization and fail-fast gating

- [x] 3.1 Implement Normalize into source-document/v1, never re-expose raw schema, satisfying the Normalized source-document output requirement: map Docling pages/blocks/tables/figures/notes into the `source-document/v1` field contract. Behavior: output contains all required top-level, page, and block fields and no business interpretation. Verify: unit test asserts required fields present on a fixture; a missing-field case exits non-zero naming the field.
- [x] 3.2 Enforce the Raw Docling JSON stays a local debug artifact requirement: write `docling/raw.json` beside the normalized output but never embed it. Behavior: `raw.json` exists as a separate file and `source_document.json` does not embed the raw schema. Verify: unit test asserts the two files exist and the normalized output omits raw-schema keys.
- [x] 3.3 Implement Fail-fast gating with a manifest record for the Privacy, network, and model-download gate: disable network and model downloads by default, record their state, and fail with an actionable error when a model is needed but downloads are disabled. Behavior: default run records `network_allowed: false` and `model_downloads_allowed: false`; blocked model download exits non-zero with enable instructions. Verify: unit tests for the default-flags manifest values and the blocked-download scenario.

## 4. Output safety and size budget

- [x] 4.1 Implement the Output-path containment and artifact-size budget requirement: reuse the existing generators' containment pattern, require `--allow-outside-workspace` to escape it, forbid default base64 page images, and emit size warnings at the 25 MB / 10 MB / 100 MB thresholds. Behavior: an out-of-workspace `--output-dir` without the override exits non-zero before writing; default output embeds no base64 and references figure images by path. Verify: unit tests for the containment-block and no-base64 scenarios.

## 5. Acceptance and regression

- [x] 5.1 Add a generated multi-element PDF fixture (header, section title, indented paragraph, caption, table, footer) and a smoke test that runs the adapter end to end. Behavior: the fixture produces `docling/raw.json`, `source_document.json`, and `ingestion_manifest.json`. Verify: smoke test asserts all three artifacts exist and `source_document.json` validates against the required-field set. (Fixture is repo-owned and deterministic per `ROADMAP.md` verification plan.) **Deviation:** the smoke test injects a deterministic DoclingDocument JSON fixture via the module's runner seam instead of running real Docling on a generated PDF, because real Docling cannot run deterministically in CI (pyenv-only, model downloads). Real-PDF + real-Docling runs stay exploratory/manual per `ROADMAP.md` and `docs/adr/0002`.
- [x] 5.2 Run the existing suite to confirm no regression. Behavior: prior generator tests remain green after adding the adapter. Verify: `python3 -m unittest discover -s tests` exits OK.
