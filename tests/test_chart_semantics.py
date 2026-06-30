"""Tests for chart/figure preservation (change: chart-figure-preservation)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import chart_semantics as cs  # noqa: E402
import extract_exhibit_semantics as ees  # noqa: E402


def _figure(self_ref="#/pictures/0", caption_refs=None):
    return {
        "id": "pictures/0",
        "self_ref": self_ref,
        "page_number": 1,
        "caption_refs": caption_refs or [],
    }


CAPTIONS = {
    "#/texts/3": "Exhibit 7: Active Uber drivers by service type",
    "#/texts/4": "Source: company data, 2015",
}


class ChartFieldsTests(unittest.TestCase):
    def test_image_ref_preserved(self):
        fields = cs.chart_exhibit_fields(_figure(), {})
        self.assertEqual(fields["image_ref"], "#/pictures/0")

    def test_caption_used_as_title(self):
        fields = cs.chart_exhibit_fields(_figure(caption_refs=["#/texts/3"]), CAPTIONS)
        self.assertEqual(fields["title"], CAPTIONS["#/texts/3"])

    def test_no_caption_leaves_title_none(self):
        self.assertIsNone(cs.chart_exhibit_fields(_figure(), CAPTIONS)["title"])

    def test_labels_carry_source_refs_and_confidence(self):
        fields = cs.chart_exhibit_fields(
            _figure(caption_refs=["#/texts/3", "#/texts/4"]), CAPTIONS
        )
        self.assertTrue(fields["semantic_hints"])
        for h in fields["semantic_hints"]:
            self.assertTrue(h["source_refs"])
            self.assertEqual(h["confidence"], "observed")
        kinds = {h["kind"] for h in fields["semantic_hints"]}
        self.assertIn("chart_label", kinds)
        self.assertIn("chart_source", kinds)  # "Source: ..." classified as source

    def test_status_image_preserved_only(self):
        fields = cs.chart_exhibit_fields(_figure(), {})
        self.assertEqual(fields["data_extraction_status"], "image_preserved_only")

    def test_no_numeric_series(self):
        fields = cs.chart_exhibit_fields(_figure(caption_refs=["#/texts/3"]), CAPTIONS)
        self.assertNotIn("values", json.dumps(fields))
        self.assertNotIn("series", json.dumps(fields))


class ExtractorIntegrationTests(unittest.TestCase):
    def _doc(self, figure):
        return {
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
                    "width": 1.0,
                    "height": 1.0,
                    "blocks": [
                        {
                            "id": "texts/3",
                            "self_ref": "#/texts/3",
                            "label": "caption",
                            "text": CAPTIONS["#/texts/3"],
                            "bbox": [72.0, 100.0, 500.0, 90.0],
                            "type": "text",
                            "page_number": 1,
                            "parent_ref": None,
                            "child_refs": [],
                            "confidence": None,
                        }
                    ],
                }
            ],
            "tables": [],
            "figures": [figure],
            "notes": [],
        }

    def test_chart_exhibit_enriched(self):
        out = ees.extract_exhibit_semantics(
            self._doc(_figure(caption_refs=["#/texts/3"]))
        )
        charts = [ex for ex in out["exhibits"] if ex["type"] == "chart"]
        self.assertEqual(len(charts), 1)
        ex = charts[0]
        self.assertEqual(ex["image_ref"], "#/pictures/0")
        self.assertEqual(ex["title"], CAPTIONS["#/texts/3"])
        self.assertEqual(ex["data_extraction_status"], "image_preserved_only")
        self.assertNotIn("values", json.dumps(ex))


if __name__ == "__main__":
    unittest.main()
