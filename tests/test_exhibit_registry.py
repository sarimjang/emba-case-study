#!/usr/bin/env python3
"""Tests for scripts/exhibit_registry.py: tiered Exhibit reference resolution
(tasks 2.1 Tier A/B, 2.2 label-anchor + anti-binding guards, 2.3 phantoms)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import exhibit_registry as er  # noqa: E402


def block(ref, text, *, label="text", bbox=None, page=1):
    return {
        "id": ref.lstrip("#/"),
        "self_ref": ref,
        "type": "text",
        "label": label,
        "text": text,
        "page_number": page,
        "bbox": bbox,
        "parent_ref": "#/body",
        "child_refs": [],
        "confidence": None,
    }


def obj(ref, *, page=1, bbox=None, caption_refs=None):
    return {
        "id": ref.lstrip("#/"),
        "self_ref": ref,
        "page_number": page,
        "bbox": bbox,
        "caption_refs": caption_refs or [],
        "cells": [],
    }


def exhibit(eid, *, source_refs, title=None):
    return {"id": eid, "type": "grid_table", "source_refs": source_refs, "title": title}


def make_doc(pages, tables=None, figures=None):
    return {
        "schema_version": "source-document/v1",
        "pages": pages,
        "tables": tables or [],
        "figures": figures or [],
        "notes": [],
    }


def page(pages_blocks, *, number=1, height=792):
    return {
        "page_number": number,
        "width": 612,
        "height": height,
        "blocks": pages_blocks,
    }


class TestTierA(unittest.TestCase):
    def test_caption_number_binds_verified(self):
        doc = make_doc(
            [
                page(
                    [
                        block(
                            "#/texts/0",
                            "Exhibit 5: Product Profitability",
                            label="caption",
                        )
                    ]
                )
            ],
            tables=[obj("#/tables/0", caption_refs=["#/texts/0"])],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1",
                    source_refs=["#/tables/0"],
                    title="Exhibit 5: Product Profitability",
                )
            ]
        }
        result = er.resolve(doc, sem)
        self.assertEqual(result["bindings"]["5"]["exhibit_id"], "exhibit-1")
        self.assertEqual(result["bindings"]["5"]["tier"], "verified")


class TestTierB(unittest.TestCase):
    def test_correct_bridge_binds_inferred(self):
        # Prose: "cost summary Exhibit 5 details" with the exhibit's
        # distinctive caption head ("cost summary") immediately preceding
        # the "Exhibit 5" mention, inside the default preceding-biased window.
        doc = make_doc(
            [page([block("#/texts/0", "cost summary Exhibit 5 details.")])],
            tables=[obj("#/tables/0", caption_refs=[])],
        )
        sem = {
            "exhibits": [
                exhibit("exhibit-1", source_refs=["#/tables/0"], title="cost summary")
            ]
        }
        result = er.resolve(doc, sem)
        self.assertEqual(result["bindings"]["5"]["exhibit_id"], "exhibit-1")
        self.assertEqual(result["bindings"]["5"]["tier"], "inferred")

    def test_boilerplate_trap_rejected(self):
        # Two exhibits share a generic head after boilerplate-marker splitting
        # ("記錄表" is on the generic-noun stop list) -> Tier B must not bind
        # on that non-distinctive head.
        doc = make_doc(
            [page([block("#/texts/0", "如記錄表之詳細內容 Exhibit 6 所示")])],
            tables=[obj("#/tables/0", caption_refs=[])],
        )
        sem = {
            "exhibits": [
                exhibit("exhibit-1", source_refs=["#/tables/0"], title="記錄表")
            ]
        }
        result = er.resolve(doc, sem, generic_noun_stoplist=frozenset({"記錄表"}))
        self.assertNotIn("6", result["bindings"])

    def test_too_short_head_rejected(self):
        doc = make_doc(
            [page([block("#/texts/0", "如表之詳細 Exhibit 7 所示")])],
            tables=[obj("#/tables/0", caption_refs=[])],
        )
        sem = {
            "exhibits": [exhibit("exhibit-1", source_refs=["#/tables/0"], title="表")]
        }
        result = er.resolve(doc, sem)
        self.assertNotIn("7", result["bindings"])


class TestLabelAnchorGuards(unittest.TestCase):
    def test_separated_bind(self):
        doc = make_doc(
            [
                page(
                    [
                        block("#/texts/0", "Exhibit 3", bbox=[100, 100, 150, 90]),
                    ],
                    height=800,
                )
            ],
            tables=[
                obj("#/tables/0", bbox=[100, 95, 150, 85]),  # near
                obj("#/tables/1", bbox=[500, 500, 550, 490]),  # far
            ],
        )
        sem = {
            "exhibits": [
                exhibit("exhibit-1", source_refs=["#/tables/0"]),
                exhibit("exhibit-2", source_refs=["#/tables/1"]),
            ]
        }
        result = er.resolve(doc, sem)
        self.assertEqual(result["bindings"]["3"]["exhibit_id"], "exhibit-1")
        self.assertEqual(result["bindings"]["3"]["tier"], "hint")

    def test_sole_distant_reject(self):
        doc = make_doc(
            [
                page(
                    [block("#/texts/0", "Exhibit 5", bbox=[10, 800, 60, 790])],
                    height=842,
                )
            ],
            tables=[obj("#/tables/0", bbox=[10, 480, 60, 470])],  # far: >20% of 842
        )
        sem = {"exhibits": [exhibit("exhibit-1", source_refs=["#/tables/0"])]}
        result = er.resolve(doc, sem)
        self.assertNotIn("5", result["bindings"])

    def test_ambiguous_reject(self):
        doc = make_doc(
            [
                page(
                    [
                        block("#/texts/0", "Exhibit 3", bbox=[100, 5, 150, -5])
                    ],  # center y=0
                    height=800,
                )
            ],
            tables=[
                obj("#/tables/0", bbox=[100, -94, 150, -104]),  # center y=-99, dist=99
                obj(
                    "#/tables/1", bbox=[100, 106, 150, 96]
                ),  # center y=101, dist=101, ratio ~0.98 > 0.6
            ],
        )
        sem = {
            "exhibits": [
                exhibit("exhibit-1", source_refs=["#/tables/0"]),
                exhibit("exhibit-2", source_refs=["#/tables/1"]),
            ]
        }
        result = er.resolve(doc, sem)
        self.assertNotIn("3", result["bindings"])

    def test_object_conflict_reject(self):
        # #/tables/0 already bound to "6" via Tier A; a distant "Exhibit 5"
        # label whose nearest object is that same table must not rebind it.
        doc = make_doc(
            [
                page(
                    [
                        block("#/texts/0", "Exhibit 6: Title", label="caption"),
                        block("#/texts/1", "Exhibit 5", bbox=[100, 100, 150, 90]),
                    ],
                    height=800,
                )
            ],
            tables=[
                obj("#/tables/0", bbox=[100, 99, 150, 89], caption_refs=["#/texts/0"])
            ],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1", source_refs=["#/tables/0"], title="Exhibit 6: Title"
                )
            ]
        }
        result = er.resolve(doc, sem)
        self.assertNotIn("5", result["bindings"])
        self.assertEqual(result["bindings"]["6"]["exhibit_id"], "exhibit-1")

    def test_number_already_resolved_reject(self):
        # Exhibit 6 already resolved (Tier A) to a DIFFERENT object than the
        # one nearest to a same-numbered bare label elsewhere -> must not
        # let label-anchor rebind number 6 to a second object.
        doc = make_doc(
            [
                page(
                    [
                        block("#/texts/0", "Exhibit 6: Title", label="caption"),
                        block("#/texts/1", "Exhibit 6", bbox=[400, 400, 450, 390]),
                    ],
                    height=800,
                )
            ],
            tables=[
                obj("#/tables/0", bbox=[10, 10, 60, 5], caption_refs=["#/texts/0"]),
                obj(
                    "#/tables/1", bbox=[400, 399, 450, 389]
                ),  # new unbound object, close to label
            ],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1", source_refs=["#/tables/0"], title="Exhibit 6: Title"
                ),
                exhibit("exhibit-2", source_refs=["#/tables/1"]),
            ]
        }
        result = er.resolve(doc, sem)
        self.assertEqual(result["bindings"]["6"]["exhibit_id"], "exhibit-1")
        self.assertEqual(result["bindings"]["6"]["object_ref"], "#/tables/0")

    def test_tier_order_prevents_rebind(self):
        # Description bridge (Tier B) resolves "Exhibit 6"; label-anchor later
        # evaluates "Exhibit 5" whose nearest object is that same table.
        doc = make_doc(
            [
                page(
                    [
                        block("#/texts/0", "distinctive head Exhibit 6 shown."),
                        block("#/texts/1", "distinctive head", label="caption"),
                        block("#/texts/2", "Exhibit 5", bbox=[100, 100, 150, 90]),
                    ],
                    height=800,
                )
            ],
            tables=[
                obj("#/tables/0", bbox=[100, 99, 150, 89], caption_refs=["#/texts/1"])
            ],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1", source_refs=["#/tables/0"], title="distinctive head"
                )
            ]
        }
        result = er.resolve(doc, sem)
        self.assertEqual(result["bindings"]["6"]["tier"], "inferred")
        self.assertNotIn("5", result["bindings"])


class TestPhantoms(unittest.TestCase):
    def test_label_detected_object_undetected(self):
        doc = make_doc(
            [
                page(
                    [block("#/texts/0", "Exhibit 5", bbox=[10, 800, 60, 790])],
                    height=842,
                )
            ]
        )
        sem = {"exhibits": []}
        result = er.resolve(doc, sem)
        phantom = next(p for p in result["phantoms"] if p["number"] == "5")
        self.assertEqual(phantom["type"], "label-detected-object-undetected")
        self.assertEqual(phantom["source_anchor"], "#/texts/0")

    def test_mentioned_only(self):
        doc = make_doc(
            [page([block("#/texts/0", "As discussed in Exhibit 9 previously.")])]
        )
        sem = {"exhibits": []}
        result = er.resolve(doc, sem)
        phantom = next(p for p in result["phantoms"] if p["number"] == "9")
        self.assertEqual(phantom["type"], "mentioned-only")


if __name__ == "__main__":
    unittest.main()
