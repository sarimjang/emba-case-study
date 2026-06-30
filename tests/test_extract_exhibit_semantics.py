"""Tests for the exhibit-semantics foundation (change: exhibit-semantics-foundation)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import extract_exhibit_semantics as ees  # noqa: E402

REAL_FIXTURE = FIXTURES / "source_document_v1_real.json"


def _doc_with(tables=None, figures=None):
    return {
        "schema_version": "source-document/v1",
        "source": {
            "path": "x",
            "mime_type": "x",
            "provider": "x",
            "provider_version": "x",
            "ingested_at": "x",
            "docling_command": "x",
        },
        "pages": [{"page_number": 1, "width": 1.0, "height": 1.0, "blocks": []}],
        "tables": tables or [],
        "figures": figures or [],
        "notes": [],
    }


def _table(self_ref="#/tables/0", cells=None, caption_refs=None):
    return {
        "id": "tables/0",
        "self_ref": self_ref,
        "page_number": 1,
        "cells": cells if cells is not None else [{"row": 0, "col": 0, "text": "A"}],
        "caption_refs": caption_refs or [],
    }


class InputGateTests(unittest.TestCase):
    def test_non_conforming_input_raises(self):
        bad = _doc_with()
        del bad["notes"]
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(bad, fh)
            p = Path(fh.name)
        try:
            with self.assertRaises(ees.ExtractionError):
                ees.load_and_extract(p)
        finally:
            p.unlink()

    def test_conforming_real_fixture_extracts(self):
        out = ees.load_and_extract(REAL_FIXTURE)
        self.assertEqual(out["schema_version"], "exhibit-semantics/v1")
        self.assertTrue(out["exhibits"])


class ClassificationTests(unittest.TestCase):
    def test_grid_table_classification(self):
        doc = _doc_with(tables=[_table()])
        out = ees.extract_exhibit_semantics(doc)
        ex = out["exhibits"][0]
        self.assertEqual(ex["type"], "grid_table")
        self.assertEqual(ex["source_refs"], ["#/tables/0"])

    def test_matrix_table_via_span(self):
        cells = [{"row": 0, "col": 0, "text": "Group", "col_span": 2}]
        out = ees.extract_exhibit_semantics(_doc_with(tables=[_table(cells=cells)]))
        self.assertEqual(out["exhibits"][0]["type"], "matrix_table")

    def test_financial_statement_via_cues(self):
        cells = [
            {"row": 0, "col": 0, "text": "Revenue $2,000"},
            {"row": 1, "col": 0, "text": "(500)"},
        ]
        out = ees.extract_exhibit_semantics(_doc_with(tables=[_table(cells=cells)]))
        self.assertEqual(out["exhibits"][0]["type"], "financial_statement")

    def test_figure_classified_as_chart_without_values(self):
        fig = {
            "id": "pictures/0",
            "self_ref": "#/pictures/0",
            "page_number": 1,
            "caption_refs": [],
        }
        out = ees.extract_exhibit_semantics(_doc_with(figures=[fig]))
        ex = out["exhibits"][0]
        self.assertEqual(ex["type"], "chart")
        self.assertNotIn("values", json.dumps(ex))  # no fabricated numeric series

    def test_type_always_in_vocabulary(self):
        out = ees.load_and_extract(REAL_FIXTURE)
        for ex in out["exhibits"]:
            self.assertIn(ex["type"], ees.EXHIBIT_TYPES)


class SourceRefAndConfidenceTests(unittest.TestCase):
    def test_every_hint_has_source_ref_and_valid_confidence(self):
        out = ees.load_and_extract(REAL_FIXTURE)
        for ex in out["exhibits"]:
            self.assertTrue(ex["source_refs"])
            for hint in ex["semantic_hints"]:
                self.assertTrue(hint["source_refs"])
                self.assertIn(hint["confidence"], ees.CONFIDENCE_VOCAB)

    def test_anchorless_table_suppressed(self):
        out = ees.extract_exhibit_semantics(_doc_with(tables=[_table(self_ref=None)]))
        self.assertEqual(out["exhibits"], [])

    def test_empty_table_downgraded_to_mixed(self):
        out = ees.extract_exhibit_semantics(_doc_with(tables=[_table(cells=[])]))
        ex = out["exhibits"][0]
        self.assertEqual(ex["type"], "mixed")
        self.assertEqual(ex["semantic_hints"][0]["confidence"], "hint")


class CliTests(unittest.TestCase):
    def _run(self, src: Path, out: Path):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "extract_exhibit_semantics.py"),
                str(src),
                "--output",
                str(out),
            ],
            capture_output=True,
            text=True,
        )

    def test_cli_valid_writes_output(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "exhibit_semantics.json"
            proc = self._run(REAL_FIXTURE, out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(out.read_text())
            self.assertEqual(data["schema_version"], "exhibit-semantics/v1")

    def test_cli_invalid_exits_nonzero(self):
        import tempfile

        bad = _doc_with()
        del bad["pages"][0]["height"]
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "bad.json"
            src.write_text(json.dumps(bad))
            out = Path(d) / "exhibit_semantics.json"
            proc = self._run(src, out)
            self.assertEqual(proc.returncode, 1)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
