"""Tests for the Docling ingestion adapter.

No real Docling install is required: the subprocess invocation is injected via a
fake runner that writes a deterministic ``DoclingDocument`` fixture.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import ingest_with_docling as ing  # noqa: E402


# Minimal DoclingDocument-shaped fixture: one page, a title text block, and a
# table with provenance and cells.
DOCLING_FIXTURE = {
    "schema_name": "DoclingDocument",
    "version": "1.0.0",
    "pages": {
        "1": {"page_no": 1, "size": {"width": 612.0, "height": 792.0}},
    },
    "texts": [
        {
            "self_ref": "#/texts/0",
            "label": "section_header",
            "text": "Exhibit 5",
            "prov": [
                {"page_no": 1, "bbox": {"l": 72.0, "t": 700.0, "r": 540.0, "b": 680.0}}
            ],
            "parent": {"$ref": "#/body"},
            "children": [],
        }
    ],
    "tables": [
        {
            "self_ref": "#/tables/0",
            "prov": [
                {"page_no": 1, "bbox": {"l": 72.0, "t": 600.0, "r": 540.0, "b": 400.0}}
            ],
            "captions": [{"$ref": "#/texts/0"}],
            "data": {
                "num_rows": 2,
                "num_cols": 2,
                "table_cells": [
                    {"row": 0, "col": 0, "text": "A"},
                    {"row": 0, "col": 1, "text": "B"},
                ],
            },
        }
    ],
    "pictures": [],
}


def _proc(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["docling"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _make_args(tmp: Path, source: Path, **over):
    base = dict(
        input=str(source),
        output_dir=str(tmp / "ingestion"),
        docling_executable=str(_fake_executable(tmp)),
        from_format=None,
        ocr=True,
        ocr_lang="en",
        table_mode="accurate",
        device="cpu",
        document_timeout=180,
        allow_outside_workspace=True,  # tmp is outside cwd in tests
        allow_network=False,
        allow_model_downloads=False,
    )
    base.update(over)
    return argparse.Namespace(**base)


def _fake_executable(tmp: Path) -> Path:
    exe = tmp / "docling"
    if not exe.exists():
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
    return exe


def _fixture_runner(tmp: Path, *, fail_with: str | None = None):
    """Runner that answers --version and writes the fixture on extraction."""

    def runner(cmd):
        if "--version" in cmd:
            return _proc(stdout="Docling version: 2.14.0\ndocling-core 2.12.1\n")
        if fail_with is not None:
            return _proc(returncode=1, stderr=fail_with)
        # extraction: find --output dir, write fixture raw.json
        out = Path(cmd[cmd.index("--output") + 1])
        out.mkdir(parents=True, exist_ok=True)
        (out / "raw.json").write_text(json.dumps(DOCLING_FIXTURE), encoding="utf-8")
        return _proc(returncode=0)

    return runner


class ExecutableResolutionTests(unittest.TestCase):
    def test_no_executable_resolvable_raises(self):
        # Isolate from any real pyenv/PATH Docling on the host.
        from unittest import mock

        missing = Path("/nonexistent/docling")
        with (
            mock.patch.object(ing, "PYENV_DOCLING", missing),
            mock.patch.object(ing, "PYENV_SHIM_DOCLING", missing),
            mock.patch.object(ing.shutil, "which", return_value=None),
            self.assertRaises(ing.IngestionError) as ctx,
        ):
            ing.discover_docling_executable("/nonexistent/path/docling")
        self.assertIn("Could not find", str(ctx.exception))

    def test_explicit_executable_resolves(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            exe = _fake_executable(Path(d))
            self.assertEqual(ing.discover_docling_executable(str(exe)), exe)

    def test_version_probe_failure_raises(self):
        exe = Path("/bin/true")
        with self.assertRaises(ing.IngestionError) as ctx:
            ing.probe_versions(
                exe, runner=lambda cmd: _proc(returncode=2, stderr="boom")
            )
        self.assertIn("version probe failed", str(ctx.exception))

    def test_version_probe_success_records_versions(self):
        exe = Path("/bin/true")
        v = ing.probe_versions(
            exe,
            runner=lambda cmd: _proc(
                stdout="Docling version: 2.14.0\ndocling-core 2.12.1\n"
            ),
        )
        self.assertEqual(v["docling_version"], "2.14.0")
        self.assertEqual(v["docling_core_version"], "2.12.1")


class NormalizationTests(unittest.TestCase):
    def test_required_fields_present(self):
        meta = {
            "path": "case.pdf",
            "mime_type": "application/pdf",
            "provider": "docling",
            "provider_version": "2.14.0",
            "ingested_at": "2026-06-30T00:00:00+00:00",
            "docling_command": "docling case.pdf",
        }
        doc = ing.normalize_source_document(DOCLING_FIXTURE, meta)
        ing.validate_source_document_minimum(doc)  # must not raise
        self.assertEqual(doc["schema_version"], "source-document/v1")
        self.assertEqual(doc["pages"][0]["page_number"], 1)
        self.assertEqual(doc["pages"][0]["width"], 612.0)
        self.assertEqual(doc["tables"][0]["page_number"], 1)
        self.assertTrue(doc["tables"][0]["cells"])

    def test_missing_page_height_rejected(self):
        doc = {
            "schema_version": "source-document/v1",
            "source": {k: "x" for k in ing.REQUIRED_SOURCE_FIELDS},
            "pages": [{"page_number": 1, "width": 1.0}],
            "tables": [],
            "figures": [],
            "notes": [],
        }
        with self.assertRaises(ing.IngestionError) as ctx:
            ing.validate_source_document_minimum(doc)
        self.assertIn("pages[0].height", str(ctx.exception))

    def test_table_without_cells_rejected(self):
        doc = {
            "schema_version": "source-document/v1",
            "source": {k: "x" for k in ing.REQUIRED_SOURCE_FIELDS},
            "pages": [{"page_number": 1, "width": 1.0, "height": 1.0}],
            "tables": [{"page_number": 1, "cells": []}],
            "figures": [],
            "notes": [],
        }
        with self.assertRaises(ing.IngestionError) as ctx:
            ing.validate_source_document_minimum(doc)
        self.assertIn("no cells", str(ctx.exception))

    def test_no_embedded_base64(self):
        meta = {k: "x" for k in ing.REQUIRED_SOURCE_FIELDS}
        doc = ing.normalize_source_document(DOCLING_FIXTURE, meta)
        ing.assert_no_embedded_base64(doc)  # must not raise
        doc["pages"][0]["image"] = "data:image/png;base64,AAAA"
        with self.assertRaises(ing.IngestionError):
            ing.assert_no_embedded_base64(doc)

    def test_figure_marked_image_preserved_only(self):
        raw = dict(DOCLING_FIXTURE)
        raw["pictures"] = [
            {
                "self_ref": "#/pictures/0",
                "prov": [{"page_no": 1, "bbox": {"l": 1, "t": 2, "r": 3, "b": 4}}],
            }
        ]
        doc = ing.normalize_source_document(
            raw, {k: "x" for k in ing.REQUIRED_SOURCE_FIELDS}
        )
        self.assertEqual(
            doc["figures"][0]["data_extraction_status"], "image_preserved_only"
        )


class OutputContainmentTests(unittest.TestCase):
    def test_outside_workspace_blocked(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "out"
            with self.assertRaises(ing.OutputPathError):
                ing.prepare_output_dir(
                    target, allowed_roots=[Path.cwd()], allow_outside_workspace=False
                )

    def test_outside_workspace_allowed_with_flag(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "out"
            got = ing.prepare_output_dir(
                target, allowed_roots=[Path.cwd()], allow_outside_workspace=True
            )
            self.assertTrue(got.is_dir())


class SizeBudgetTests(unittest.TestCase):
    def test_warnings_emitted_over_threshold(self):
        warns = ing.size_warnings(
            ing.RAW_JSON_WARN_BYTES + 1,
            ing.SOURCE_DOC_WARN_BYTES + 1,
            ing.TOTAL_ARTIFACT_WARN_BYTES + 1,
        )
        self.assertEqual(len(warns), 3)

    def test_no_warnings_under_threshold(self):
        self.assertEqual(ing.size_warnings(1, 1, 1), [])


class EndToEndTests(unittest.TestCase):
    def test_smoke_produces_three_artifacts(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = tmp / "case.pdf"
            source.write_bytes(b"%PDF-1.4 fake")
            args = _make_args(tmp, source)
            out = ing.run_ingestion(args, runner=_fixture_runner(tmp))
            self.assertTrue(Path(out["raw_json_path"]).exists())
            self.assertTrue(Path(out["source_document_path"]).exists())
            self.assertTrue(Path(out["manifest_path"]).exists())
            doc = json.loads(Path(out["source_document_path"]).read_text())
            ing.validate_source_document_minimum(doc)

    def test_manifest_records_gate_defaults(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = tmp / "case.pdf"
            source.write_bytes(b"%PDF-1.4 fake")
            args = _make_args(tmp, source)
            out = ing.run_ingestion(args, runner=_fixture_runner(tmp))
            manifest = json.loads(Path(out["manifest_path"]).read_text())
            self.assertFalse(manifest["network_allowed"])
            self.assertFalse(manifest["model_downloads_allowed"])
            self.assertEqual(manifest["docling_version"], "2.14.0")
            self.assertEqual(manifest["table_mode"], "accurate")

    def test_raw_json_separate_and_not_embedded(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = tmp / "case.pdf"
            source.write_bytes(b"%PDF-1.4 fake")
            args = _make_args(tmp, source)
            out = ing.run_ingestion(args, runner=_fixture_runner(tmp))
            self.assertTrue(Path(out["raw_json_path"]).name == "raw.json")
            doc = json.loads(Path(out["source_document_path"]).read_text())
            self.assertNotIn("schema_name", doc)  # raw DoclingDocument key not embedded

    def test_docling_command_recorded_in_source_document(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = tmp / "case.pdf"
            source.write_bytes(b"%PDF-1.4 fake")
            args = _make_args(tmp, source)
            out = ing.run_ingestion(args, runner=_fixture_runner(tmp))
            doc = json.loads(Path(out["source_document_path"]).read_text())
            recorded = doc["source"]["docling_command"]
            self.assertIn("--table-mode accurate", recorded)
            self.assertIn("--ocr-lang en", recorded)
            self.assertIn("--to json", recorded)

    def test_blocked_model_download_raises_actionable(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = tmp / "case.pdf"
            source.write_bytes(b"%PDF-1.4 fake")
            args = _make_args(tmp, source)
            runner = _fixture_runner(
                tmp, fail_with="Could not download model from huggingface"
            )
            with self.assertRaises(ing.IngestionError) as ctx:
                ing.run_ingestion(args, runner=runner)
            self.assertIn("--allow-model-downloads", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
