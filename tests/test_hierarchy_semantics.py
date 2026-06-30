"""Tests for hierarchy (no-grid) semantics (change: hierarchy-no-grid-semantics)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import extract_exhibit_semantics as ees  # noqa: E402
import hierarchy_semantics as hs  # noqa: E402

REAL_FIXTURE = FIXTURES / "source_document_v1_real.json"


def _block(bid, left, text="", label="text"):
    return {
        "id": bid,
        "self_ref": f"#/{bid}",
        "label": label,
        "text": text,
        "bbox": None if left is None else [left, 100.0, left + 50.0, 90.0],
    }


class IndentLevelTests(unittest.TestCase):
    def test_two_levels_detected(self):
        blocks = [_block("texts/0", 72, "Revenue"), _block("texts/1", 96, "Food")]
        levels = hs.infer_indent_levels(blocks)
        self.assertEqual(levels["texts/0"], 0)
        self.assertEqual(levels["texts/1"], 1)

    def test_missing_bbox_defaults_zero(self):
        blocks = [_block("texts/0", None, "X")]
        self.assertEqual(hs.infer_indent_levels(blocks)["texts/0"], 0)


class ParentChildTests(unittest.TestCase):
    def test_child_mapped_to_heading(self):
        blocks = [
            _block("texts/0", 72, "Revenue"),
            _block("texts/1", 96, "Food 70.0-80.0"),
        ]
        levels = hs.infer_indent_levels(blocks)
        pc = {
            p["block_id"]: p["parent_id"] for p in hs.build_parent_child(blocks, levels)
        }
        self.assertIsNone(pc["texts/0"])
        self.assertEqual(pc["texts/1"], "texts/0")


class RangeParseTests(unittest.TestCase):
    def test_percentage_range(self):
        self.assertEqual(
            hs.parse_range("70.0-80.0"), {"kind": "range", "low": 70.0, "high": 80.0}
        )

    def test_prose_none(self):
        self.assertIsNone(hs.parse_range("Operating expenses commentary"))


class NoteAssociationTests(unittest.TestCase):
    def test_note_attached_to_preceding_block(self):
        blocks = [
            _block("texts/0", 72, "Revenue"),
            _block("texts/1", 72, "Source: filings", label="footnote"),
        ]
        assoc = hs.associate_notes(blocks)
        self.assertEqual(assoc, [{"note_id": "texts/1", "exhibit_id": "texts/0"}])


class ExhibitConstructionTests(unittest.TestCase):
    def test_hierarchy_built_from_value_rows(self):
        blocks = [
            _block("texts/0", 72, "Revenue"),
            _block("texts/1", 96, "Food cost 70.0-80.0"),
            _block("texts/2", 96, "Labor 15.0-20.0"),
        ]
        ex = hs.hierarchy_exhibit_from_blocks(blocks, "#/pages/1")
        self.assertIsNotNone(ex)
        self.assertEqual(ex["type"], "hierarchy_table")
        kinds = {h["kind"] for h in ex["semantic_hints"]}
        self.assertIn("indent_hierarchy", kinds)
        for h in ex["semantic_hints"]:
            self.assertEqual(h["confidence"], "hint")
            self.assertTrue(h["source_refs"])

    def test_prose_page_no_exhibit(self):
        blocks = [
            _block("texts/0", 72, "This is a paragraph of prose."),
            _block("texts/1", 72, "Another flat prose line."),
        ]
        self.assertIsNone(hs.hierarchy_exhibit_from_blocks(blocks, "#/pages/1"))


class IntegrationRegressionTests(unittest.TestCase):
    def test_real_grid_fixture_yields_no_hierarchy_exhibit(self):
        doc = json.loads(REAL_FIXTURE.read_text(encoding="utf-8"))
        out = ees.extract_exhibit_semantics(doc)
        self.assertFalse(
            any(ex["type"] == "hierarchy_table" for ex in out["exhibits"]),
            "grid-table fixture must not produce a spurious hierarchy exhibit",
        )

    def test_extractor_emits_hierarchy_for_indented_page(self):
        doc = {
            "schema_version": "source-document/v1",
            "source": dict.fromkeys(
                [
                    "path",
                    "mime_type",
                    "provider",
                    "provider_version",
                    "ingested_at",
                    "docling_command",
                ],
                "x",
            ),
            "pages": [
                {
                    "page_number": 1,
                    "width": 612.0,
                    "height": 792.0,
                    "blocks": [
                        _block("texts/0", 72, "Revenue"),
                        _block("texts/1", 96, "Food cost 70.0-80.0"),
                        _block("texts/2", 96, "Labor 15.0-20.0"),
                    ],
                }
            ],
            "tables": [],
            "figures": [],
            "notes": [],
        }
        out = ees.extract_exhibit_semantics(doc)
        self.assertTrue(any(ex["type"] == "hierarchy_table" for ex in out["exhibits"]))


if __name__ == "__main__":
    unittest.main()
