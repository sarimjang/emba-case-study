#!/usr/bin/env python3
"""Regression-locked synthetic fixtures for the measured pet/Benihana scenarios
(task 4.2) and the never-fired true-duplicate dedup branch (task 4.3).

Real EMBA PDFs are never committed (see handoff hard constraints); these
fixtures are small synthetic reproductions of the scenario shapes.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import compose_layout as cl  # noqa: E402
import exhibit_registry as er  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestDescriptionBridgeRegression(unittest.TestCase):
    def test_description_bridge_binds_as_measured(self):
        fixture = load("regression_description_bridge.json")
        result = er.resolve(fixture["source_document"], fixture["exhibit_semantics"])
        for number, expected in fixture["expected"]["bindings"].items():
            self.assertEqual(
                result["bindings"][number]["exhibit_id"], expected["exhibit_id"]
            )
            self.assertEqual(result["bindings"][number]["tier"], expected["tier"])


class TestCollageLabelAnchorRegression(unittest.TestCase):
    def test_collage_label_anchor_binds_as_measured(self):
        fixture = load("regression_collage_label_anchor.json")
        result = er.resolve(fixture["source_document"], fixture["exhibit_semantics"])
        for number, expected in fixture["expected"]["bindings"].items():
            self.assertEqual(
                result["bindings"][number]["exhibit_id"], expected["exhibit_id"]
            )
            self.assertEqual(result["bindings"][number]["tier"], expected["tier"])


class TestSoleDistantRejectRegression(unittest.TestCase):
    def test_sole_distant_label_stays_unresolved_and_phantom(self):
        fixture = load("regression_sole_distant_reject.json")
        result = er.resolve(fixture["source_document"], fixture["exhibit_semantics"])
        for number in fixture["expected"]["unresolved"]:
            self.assertNotIn(number, result["bindings"])
        phantom_by_number = {p["number"]: p["type"] for p in result["phantoms"]}
        for number, expected_type in fixture["expected"]["phantom_types"].items():
            self.assertEqual(phantom_by_number[number], expected_type)


class TestDualTypePhantomRegression(unittest.TestCase):
    def test_both_phantom_types_emitted(self):
        fixture = load("regression_dual_type_phantom.json")
        result = er.resolve(fixture["source_document"], fixture["exhibit_semantics"])
        phantom_by_number = {p["number"]: p["type"] for p in result["phantoms"]}
        for number, expected_type in fixture["expected"]["phantom_types"].items():
            self.assertEqual(phantom_by_number[number], expected_type)


class TestTrueDuplicateRegression(unittest.TestCase):
    def test_true_duplicate_suppressed_near_miss_preserved(self):
        fixture = load("regression_true_duplicate.json")
        stream = cl.linearize(fixture["source_document"], fixture["exhibit_semantics"])
        text_refs = {item["self_ref"] for item in stream if item["kind"] == "text"}
        for ref in fixture["expected"]["suppressed_refs"]:
            self.assertNotIn(ref, text_refs)
        for ref in fixture["expected"]["preserved_refs"]:
            self.assertIn(ref, text_refs)


if __name__ == "__main__":
    unittest.main()
