#!/usr/bin/env python3
"""Tests for scripts/compose_layout.py: linearization spine + dedup (tasks 1.1, 1.2, 2.4)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import compose_layout as cl  # noqa: E402


def block(ref, text, *, label="text", bbox, page=1):
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


def table(ref, *, page=1, bbox, caption_refs=None, cells=None):
    return {
        "id": ref.lstrip("#/"),
        "self_ref": ref,
        "page_number": page,
        "bbox": bbox,
        "caption_refs": caption_refs or [],
        "cells": cells if cells is not None else [{"text": "a", "row": 0, "col": 0}],
    }


def exhibit(eid, *, source_refs, etype="grid_table", title=None):
    return {"id": eid, "type": etype, "source_refs": source_refs, "title": title}


def make_doc(pages):
    return {
        "schema_version": "source-document/v1",
        "pages": pages,
        "tables": [],
        "figures": [],
        "notes": [],
    }


class TestLinearizeCaptionedInsertion(unittest.TestCase):
    def test_table_placed_adjacent_to_its_caption(self):
        doc = make_doc(
            [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [
                        block("#/texts/0", "intro prose", bbox=[0, 700, 100, 690]),
                        block(
                            "#/texts/1",
                            "Table 1. Caption",
                            label="caption",
                            bbox=[0, 680, 100, 670],
                        ),
                        block("#/texts/2", "trailing prose", bbox=[0, 600, 100, 590]),
                    ],
                }
            ]
        )
        doc["tables"] = [
            table("#/tables/0", bbox=[0, 660, 100, 610], caption_refs=["#/texts/1"])
        ]
        sem = {"exhibits": [exhibit("exhibit-1", source_refs=["#/tables/0"])]}

        stream = cl.linearize(doc, sem)
        kinds = [(s["kind"], s.get("self_ref")) for s in stream]
        self.assertEqual(
            kinds,
            [
                ("text", "#/texts/0"),
                ("text", "#/texts/1"),
                ("exhibit", "#/tables/0"),
                ("text", "#/texts/2"),
            ],
        )

    def test_surrounding_prose_keeps_native_order(self):
        doc = make_doc(
            [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [
                        block("#/texts/0", "first", bbox=[0, 700, 100, 690]),
                        block("#/texts/1", "second", bbox=[0, 680, 100, 670]),
                        block("#/texts/2", "third", bbox=[0, 660, 100, 650]),
                    ],
                }
            ]
        )
        sem = {"exhibits": []}
        stream = cl.linearize(doc, sem)
        texts = [s["text"] for s in stream if s["kind"] == "text"]
        self.assertEqual(texts, ["first", "second", "third"])


class TestLinearizeUncaptionedFallback(unittest.TestCase):
    def test_uncaptioned_exhibit_placed_by_bbox(self):
        doc = make_doc(
            [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [
                        block("#/texts/0", "above", bbox=[0, 700, 100, 690]),
                        block("#/texts/1", "below", bbox=[0, 600, 100, 590]),
                    ],
                }
            ]
        )
        # No caption_refs; bbox top sits between the two text blocks.
        doc["tables"] = [table("#/tables/0", bbox=[0, 650, 100, 620], caption_refs=[])]
        sem = {"exhibits": [exhibit("exhibit-1", source_refs=["#/tables/0"])]}

        stream = cl.linearize(doc, sem)
        kinds = [(s["kind"], s.get("self_ref")) for s in stream]
        self.assertEqual(
            kinds,
            [
                ("text", "#/texts/0"),
                ("exhibit", "#/tables/0"),
                ("text", "#/texts/1"),
            ],
        )

    def test_exhibit_with_no_bbox_and_no_caption_placed_after_last_block(self):
        # source-document/v1 does not require bbox on tables. With neither a
        # caption nor a bbox there is no positional information at all, so
        # the exhibit deliberately lands after the last block on the page.
        doc = make_doc(
            [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [
                        block("#/texts/0", "first", bbox=[0, 700, 100, 690]),
                        block("#/texts/1", "second", bbox=[0, 600, 100, 590]),
                    ],
                }
            ]
        )
        doc["tables"] = [table("#/tables/0", bbox=None, caption_refs=[])]
        sem = {"exhibits": [exhibit("exhibit-1", source_refs=["#/tables/0"])]}

        stream = cl.linearize(doc, sem)
        kinds = [(s["kind"], s.get("self_ref")) for s in stream]
        self.assertEqual(
            kinds,
            [
                ("text", "#/texts/0"),
                ("text", "#/texts/1"),
                ("exhibit", "#/tables/0"),
            ],
        )


class TestConservativeDedup(unittest.TestCase):
    def test_true_duplicate_suppressed(self):
        doc = make_doc(
            [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [
                        # bbox center (50, 55) lies inside table bbox [0,100,100,0].
                        block("#/texts/0", "cell value", bbox=[40, 60, 60, 50]),
                    ],
                }
            ]
        )
        doc["tables"] = [
            table(
                "#/tables/0",
                bbox=[0, 100, 100, 0],
                cells=[{"text": "cell value", "row": 0, "col": 0}],
            )
        ]
        sem = {"exhibits": [exhibit("exhibit-1", source_refs=["#/tables/0"])]}
        stream = cl.linearize(doc, sem)
        kinds = [(s["kind"], s.get("self_ref")) for s in stream]
        self.assertEqual(kinds, [("exhibit", "#/tables/0")])

    def test_boilerplate_suffix_sharing_block_outside_bbox_preserved(self):
        doc = make_doc(
            [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [
                        # Same text as a table cell, but bbox center is far outside
                        # the table's bbox -> must be preserved, not deduped.
                        block("#/texts/0", "cell value", bbox=[500, 780, 520, 770]),
                    ],
                }
            ]
        )
        doc["tables"] = [
            table(
                "#/tables/0",
                bbox=[0, 100, 100, 0],
                cells=[{"text": "cell value", "row": 0, "col": 0}],
            )
        ]
        sem = {"exhibits": [exhibit("exhibit-1", source_refs=["#/tables/0"])]}
        stream = cl.linearize(doc, sem)
        kinds = [(s["kind"], s.get("self_ref")) for s in stream]
        self.assertIn(("text", "#/texts/0"), kinds)


class TestCollageNativeOrder(unittest.TestCase):
    def test_collage_page_linearizes_in_intended_reading_order(self):
        # A collage page: two figures with interleaved prose fragments, native
        # block order is authoritative even though bbox geometry is scattered.
        doc = make_doc(
            [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [
                        block(
                            "#/texts/0",
                            "Fragment A",
                            label="caption",
                            bbox=[0, 700, 50, 690],
                        ),
                        block(
                            "#/texts/1",
                            "Fragment B",
                            label="caption",
                            bbox=[300, 300, 350, 290],
                        ),
                        block(
                            "#/texts/2",
                            "Fragment C",
                            bbox=[100, 100, 150, 90],
                        ),
                    ],
                }
            ]
        )
        doc["figures"] = [
            table(
                "#/figures/0",
                bbox=[0, 690, 50, 500],
                caption_refs=["#/texts/0"],
                cells=[],
            ),
            table(
                "#/figures/1",
                bbox=[300, 290, 350, 200],
                caption_refs=["#/texts/1"],
                cells=[],
            ),
        ]
        sem = {
            "exhibits": [
                exhibit("exhibit-1", source_refs=["#/figures/0"], etype="chart"),
                exhibit("exhibit-2", source_refs=["#/figures/1"], etype="chart"),
            ]
        }
        stream = cl.linearize(doc, sem)
        kinds = [(s["kind"], s.get("self_ref")) for s in stream]
        self.assertEqual(
            kinds,
            [
                ("text", "#/texts/0"),
                ("exhibit", "#/figures/0"),
                ("text", "#/texts/1"),
                ("exhibit", "#/figures/1"),
                ("text", "#/texts/2"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
