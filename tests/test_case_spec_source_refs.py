"""Tests for structured case-spec evidence + Source Reference Rule (change: case-spec-source-refs)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import case_spec_utils as csu  # noqa: E402


def _evidence(items):
    """Minimal valid spec whose evidence.quantitative_signals holds `items`."""
    return {
        "case": {"title": "Wilkerson"},
        "decision_pivot": {
            "decision_owner": "CEO",
            "decision_question": "What to do?",
            "urgency": "high",
            "delay_cost": "margin erosion",
        },
        "company_industry_context": {},
        "core_dilemma": {
            "surface_problem": "x",
            "root_problem": "y",
            "key_tension": "z",
        },
        "evidence": {"quantitative_signals": items},
        "options": [{"title": "A", "how": "h", "why": "w", "trade_off": "t"}],
    }


class BackwardCompatTests(unittest.TestCase):
    def test_legacy_strings_valid(self):
        csu.validate_spec(_evidence(["Revenue grew 10%.", "Margins fell."]))

    def test_string_and_object_coexist(self):
        items = [
            "legacy note",
            {"text": "Structured note", "source_refs": ["#/texts/0"]},
        ]
        csu.validate_spec(_evidence(items))

    def test_non_string_non_object_rejected(self):
        with self.assertRaises(csu.SpecValidationError) as ctx:
            csu.validate_spec(_evidence(["ok", 42]))
        self.assertIn("evidence.quantitative_signals[1]", str(ctx.exception))


class StructuredShapeTests(unittest.TestCase):
    def test_valid_object_accepted(self):
        items = [
            {"text": "Signal", "source_refs": ["#/tables/0"], "confidence": "observed"}
        ]
        csu.validate_spec(_evidence(items))

    def test_empty_text_rejected(self):
        with self.assertRaises(csu.SpecValidationError) as ctx:
            csu.validate_spec(_evidence([{"text": "  "}]))
        self.assertIn("text", str(ctx.exception))

    def test_invalid_confidence_rejected(self):
        with self.assertRaises(csu.SpecValidationError) as ctx:
            csu.validate_spec(_evidence([{"text": "x", "confidence": "very-sure"}]))
        self.assertIn("confidence", str(ctx.exception))

    def test_non_string_source_refs_rejected(self):
        with self.assertRaises(csu.SpecValidationError):
            csu.validate_spec(_evidence([{"text": "x", "source_refs": [123]}]))


class SourceReferenceRuleTests(unittest.TestCase):
    def test_interpretation_requires_exhibit_anchor(self):
        item = {
            "text": "Valves carry the highest margin (ranking).",
            "evidence_type": "exhibit_interpretation",
            "source_refs": ["#/tables/0"],  # source-document anchor only
        }
        with self.assertRaises(csu.SpecValidationError) as ctx:
            csu.validate_spec(_evidence([item]))
        self.assertIn("exhibit_semantics", str(ctx.exception))

    def test_interpretation_with_exhibit_anchor_ok(self):
        item = {
            "text": "Valves carry the highest margin (ranking).",
            "evidence_type": "exhibit_interpretation",
            "source_refs": ["exhibit-1"],
        }
        csu.validate_spec(_evidence([item]))

    def test_observed_fact_with_source_document_anchor_ok(self):
        item = {"text": "Reported revenue was $2,000.", "source_refs": ["#/tables/0"]}
        csu.validate_spec(_evidence([item]))

    def test_interprets_flag_also_enforced(self):
        item = {
            "text": "Subtotal means operating income.",
            "interprets_exhibit": True,
            "source_refs": ["#/texts/3"],
        }
        with self.assertRaises(csu.SpecValidationError):
            csu.validate_spec(_evidence([item]))


class LayoutDenylistTests(unittest.TestCase):
    def test_embedded_bbox_rejected(self):
        with self.assertRaises(csu.SpecValidationError) as ctx:
            csu.validate_spec(_evidence([{"text": "x", "bbox": [1, 2, 3, 4]}]))
        self.assertIn("bbox", str(ctx.exception))

    def test_embedded_cells_rejected(self):
        with self.assertRaises(csu.SpecValidationError) as ctx:
            csu.validate_spec(_evidence([{"text": "x", "cells": []}]))
        self.assertIn("cells", str(ctx.exception))


class AppendixAndNotesTests(unittest.TestCase):
    def test_appendix_and_source_notes_accept_structured(self):
        spec = _evidence(["legacy"])
        spec["case"]["source_notes"] = [{"text": "Note", "source_refs": ["#/texts/0"]}]
        spec["appendix"] = {
            "references": [{"text": "Ref", "source_refs": ["exhibit-2"]}]
        }
        csu.validate_spec(spec)


if __name__ == "__main__":
    unittest.main()
