"""Tests for table semantics (change: table-semantics)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_exhibit_semantics as ees  # noqa: E402
import table_semantics as ts  # noqa: E402


def _cell(
    text, row, col, *, col_span=1, row_span=1, column_header=False, row_header=False
):
    return {
        "text": text,
        "row": row,
        "col": col,
        "col_span": col_span,
        "row_span": row_span,
        "column_header": column_header,
        "row_header": row_header,
    }


class CellRoleTests(unittest.TestCase):
    def test_grouped_column_header(self):
        table = {"cells": [_cell("Hours/week", 0, 0, col_span=4, column_header=True)]}
        roled = ts.classify_cell_roles(table)
        self.assertEqual(roled[0]["role"], "column_group_header")
        self.assertEqual(roled[0]["col_span"], 4)

    def test_leaf_header_and_data(self):
        table = {
            "cells": [
                _cell("Revenue", 0, 1, column_header=True),
                _cell("2000", 1, 1),
            ]
        }
        roled = ts.classify_cell_roles(table)
        self.assertEqual(roled[0]["role"], "column_header")
        self.assertEqual(roled[1]["role"], "data")

    def test_blank_cell_preserved_as_data(self):
        table = {"cells": [_cell("", 1, 1)]}
        roled = ts.classify_cell_roles(table)
        self.assertEqual(len(roled), 1)
        self.assertEqual(roled[0]["role"], "data")
        self.assertEqual(roled[0]["text"], "")


class AmountParsingTests(unittest.TestCase):
    def test_parenthesized_negative(self):
        self.assertEqual(ts.parse_amount("(500)"), {"kind": "number", "value": -500.0})

    def test_currency_with_commas(self):
        self.assertEqual(ts.parse_amount("$2,000"), {"kind": "number", "value": 2000.0})

    def test_percent(self):
        self.assertEqual(ts.parse_amount("15%"), {"kind": "percent", "value": 15.0})

    def test_range(self):
        self.assertEqual(
            ts.parse_amount("70.0-80.0"), {"kind": "range", "low": 70.0, "high": 80.0}
        )

    def test_non_amount_returns_none(self):
        self.assertIsNone(ts.parse_amount("Operating margin commentary"))
        self.assertIsNone(ts.parse_amount(""))


class SubtotalTotalTests(unittest.TestCase):
    def test_total_row_marked(self):
        cells = [
            _cell("Total", 2, 0, row_header=True),
            _cell("Valves", 0, 0, row_header=True),
        ]
        roled = ts.classify_cell_roles({"cells": cells})
        hints = ts.detect_subtotal_total_candidates(roled, "#/tables/0")
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]["kind"], "subtotal_total_candidate")
        self.assertEqual(hints[0]["confidence"], "hint")
        self.assertEqual(hints[0]["source_refs"], ["#/tables/0"])


class ArithmeticCheckTests(unittest.TestCase):
    def _roled(self, rows):
        cells = []
        for r, (label, val) in enumerate(rows):
            cells.append(_cell(label, r, 0, row_header=True))
            cells.append(_cell(val, r, 1))
        return ts.classify_cell_roles({"cells": cells})

    def test_matching_total_verified(self):
        roled = self._roled([("Valves", "1200"), ("Pumps", "800"), ("Total", "2000")])
        checks = ts.arithmetic_checks(roled, "#/tables/0")
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0]["confidence"], "verified")

    def test_mismatched_total_rejected(self):
        roled = self._roled([("Valves", "1200"), ("Pumps", "800"), ("Total", "9999")])
        checks = ts.arithmetic_checks(roled, "#/tables/0")
        self.assertEqual(checks[0]["confidence"], "rejected")

    def test_unparseable_column_no_check(self):
        roled = self._roled([("Valves", "n/a"), ("Pumps", "800"), ("Total", "800")])
        checks = ts.arithmetic_checks(roled, "#/tables/0")
        self.assertEqual(checks, [])


class IntegrationTests(unittest.TestCase):
    def test_financial_exhibit_enriched(self):
        cells = []
        for r, (label, val) in enumerate(
            [("Valves", "$1,200"), ("Pumps", "$800"), ("Total", "$2,000")]
        ):
            cells.append(_cell(label, r, 0, row_header=True))
            cells.append(_cell(val, r, 1))
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
            "pages": [{"page_number": 1, "width": 1.0, "height": 1.0, "blocks": []}],
            "tables": [
                {
                    "id": "tables/0",
                    "self_ref": "#/tables/0",
                    "page_number": 1,
                    "cells": cells,
                    "caption_refs": [],
                }
            ],
            "figures": [],
            "notes": [],
        }
        out = ees.extract_exhibit_semantics(doc)
        ex = out["exhibits"][0]
        self.assertEqual(ex["type"], "financial_statement")
        self.assertIn("roled_cells", ex)
        kinds = {h["kind"] for h in ex["semantic_hints"]}
        self.assertIn("subtotal_total_candidate", kinds)
        self.assertTrue(ex["checks"])
        self.assertEqual(ex["checks"][0]["confidence"], "verified")
        # Confidence vocabulary preserved across all hints/checks.
        for h in ex["semantic_hints"]:
            self.assertIn(h["confidence"], ees.CONFIDENCE_VOCAB)
        for c in ex["checks"]:
            self.assertIn(c["confidence"], ees.CONFIDENCE_VOCAB)


if __name__ == "__main__":
    unittest.main()
