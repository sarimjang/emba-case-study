"""Tests for the source-document/v1 validator (change: source-document-schema-validation).

All fixtures are deterministic and repo-owned; no real EMBA case PDF is used.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import source_document_schema as sds  # noqa: E402

REAL_FIXTURE = FIXTURES / "source_document_v1_real.json"


def _minimal_doc() -> dict:
    return {
        "schema_version": "source-document/v1",
        "source": dict.fromkeys(sds.REQUIRED_SOURCE_FIELDS, "x"),
        "pages": [
            {
                "page_number": 1,
                "width": 612.0,
                "height": 792.0,
                "blocks": [
                    {
                        "id": "texts/0",
                        "self_ref": "#/texts/0",
                        "type": "text",
                        "label": "section_header",
                        "text": "Exhibit 5",
                        "page_number": 1,
                        "bbox": [1.0, 2.0, 3.0, 4.0],
                        "parent_ref": "#/body",
                        "child_refs": [],
                        "confidence": None,
                    }
                ],
            }
        ],
        "tables": [
            {"id": "tables/0", "page_number": 1, "cells": [{"row": 0, "col": 0}]}
        ],
        "figures": [],
        "notes": [],
    }


class StructuralValidationTests(unittest.TestCase):
    def test_valid_document_passes(self):
        result = sds.validate_source_document(_minimal_doc())
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.errors, [])

    def test_missing_page_height_named(self):
        doc = _minimal_doc()
        del doc["pages"][0]["height"]
        result = sds.validate_source_document(doc)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("pages[0].height" in e for e in result.errors), result.errors
        )

    def test_missing_block_field_named(self):
        doc = _minimal_doc()
        del doc["pages"][0]["blocks"][0]["self_ref"]
        result = sds.validate_source_document(doc)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("blocks[0].self_ref" in e for e in result.errors), result.errors
        )

    def test_missing_top_level_named(self):
        doc = _minimal_doc()
        del doc["notes"]
        result = sds.validate_source_document(doc)
        self.assertFalse(result.ok)
        self.assertTrue(
            any(e.startswith("notes") for e in result.errors), result.errors
        )

    def test_table_without_cells_named(self):
        doc = _minimal_doc()
        doc["tables"][0]["cells"] = []
        result = sds.validate_source_document(doc)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("tables[0].cells" in e for e in result.errors), result.errors
        )


class FactsOnlyConstraintTests(unittest.TestCase):
    def test_interpretation_key_rejected(self):
        doc = _minimal_doc()
        doc["tables"][0]["subtotal_meaning"] = "operating total"
        result = sds.validate_source_document(doc)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("subtotal_meaning" in e for e in result.errors), result.errors
        )

    def test_nested_interpretation_key_rejected(self):
        doc = _minimal_doc()
        doc["pages"][0]["blocks"][0]["exhibit_type"] = "financial_statement"
        result = sds.validate_source_document(doc)
        self.assertFalse(result.ok)
        self.assertTrue(any("exhibit_type" in e for e in result.errors), result.errors)

    def test_observed_facts_allowed(self):
        result = sds.validate_source_document(_minimal_doc())
        self.assertTrue(result.ok, result.errors)


class RealFixtureTests(unittest.TestCase):
    def test_real_source_document_validates(self):
        doc = json.loads(REAL_FIXTURE.read_text(encoding="utf-8"))
        result = sds.validate_source_document(doc)
        self.assertTrue(result.ok, result.errors)

    def test_generated_pdf_fixture_coverage(self):
        # The fixture is the source_document produced by ingesting a generated PDF
        # (title, section header, paragraph, table, caption, footer) through the
        # real Docling adapter. It must exercise pages, a table with cells, and a
        # caption reference.
        doc = json.loads(REAL_FIXTURE.read_text(encoding="utf-8"))
        self.assertTrue(doc["pages"])
        self.assertTrue(doc["pages"][0]["blocks"])
        self.assertTrue(doc["tables"][0]["cells"])
        self.assertTrue(doc["tables"][0]["caption_refs"])

    def test_fixtures_are_committed_json_not_real_pdfs(self):
        # Deterministic-fixtures requirement: validation rests on a committed,
        # repo-owned JSON fixture (parseable, not a real EMBA case PDF), and no
        # *.pdf fixture is required for acceptance.
        self.assertTrue(REAL_FIXTURE.is_file())
        self.assertEqual(REAL_FIXTURE.suffix, ".json")
        json.loads(REAL_FIXTURE.read_text(encoding="utf-8"))  # parses
        self.assertEqual(list(FIXTURES.glob("*.pdf")), [])


class CliTests(unittest.TestCase):
    def _run(self, path: Path):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "source_document_schema.py"),
                str(path),
            ],
            capture_output=True,
            text=True,
        )

    def test_cli_valid_exits_zero(self):
        proc = self._run(REAL_FIXTURE)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_cli_invalid_exits_nonzero_with_field(self):
        import tempfile

        bad = _minimal_doc()
        del bad["pages"][0]["height"]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(bad, fh)
            bad_path = Path(fh.name)
        try:
            proc = self._run(bad_path)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("pages[0].height", proc.stderr)
        finally:
            bad_path.unlink()


if __name__ == "__main__":
    unittest.main()
