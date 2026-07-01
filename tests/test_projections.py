#!/usr/bin/env python3
"""Tests for the reading_view and rag_chunks projections (tasks 3.1, 3.2)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import compose_layout as cl  # noqa: E402
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


def table(ref, *, page=1, bbox=None, caption_refs=None, cells=None):
    return {
        "id": ref.lstrip("#/"),
        "self_ref": ref,
        "page_number": page,
        "bbox": bbox,
        "caption_refs": caption_refs or [],
        "cells": cells if cells is not None else [{"text": "a", "row": 0, "col": 0}],
    }


def exhibit(eid, *, source_refs, etype="grid_table", title=None, roled_cells=None):
    ex = {"id": eid, "type": etype, "source_refs": source_refs, "title": title}
    if roled_cells is not None:
        ex["roled_cells"] = roled_cells
    return ex


def make_doc(pages, tables=None, figures=None):
    return {
        "schema_version": "source-document/v1",
        "pages": pages,
        "tables": tables or [],
        "figures": figures or [],
        "notes": [],
    }


def page(blocks, *, number=1, height=792):
    return {"page_number": number, "width": 612, "height": height, "blocks": blocks}


class TestReadingView(unittest.TestCase):
    def test_resolved_and_unresolved_references_both_annotated(self):
        doc = make_doc(
            [
                page(
                    [
                        block(
                            "#/texts/0",
                            "See Exhibit 5: Margins",
                            label="caption",
                        ),
                        block(
                            "#/texts/1",
                            "Compare Exhibit 5 against Exhibit 9 for context.",
                        ),
                    ]
                )
            ],
            tables=[table("#/tables/0", caption_refs=["#/texts/0"])],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1",
                    source_refs=["#/tables/0"],
                    roled_cells=[{"row": 0, "col": 0, "text": "a"}],
                )
            ]
        }
        stream = cl.linearize(doc, sem)
        resolution = er.resolve(doc, sem)
        rendered = cl.render_reading_view(stream, resolution)
        self.assertIn("exhibit-1", rendered)
        self.assertIn("verified", rendered)
        self.assertIn("unresolved", rendered)

    def test_hierarchy_table_without_roled_cells_not_labeled_as_chart(self):
        # hierarchy_table exhibits never get roled_cells (only grid_table /
        # matrix_table / financial_statement do) but they are real detected
        # tables, not charts, so the placeholder body must not say "chart".
        doc = make_doc(
            [page([block("#/texts/0", "Exhibit 5: Org Chart", label="caption")])],
            tables=[table("#/tables/0", caption_refs=["#/texts/0"])],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1", source_refs=["#/tables/0"], etype="hierarchy_table"
                )
            ]
        }
        stream = cl.linearize(doc, sem)
        resolution = er.resolve(doc, sem)
        rendered = cl.render_reading_view(stream, resolution)
        self.assertNotIn("chart", rendered)


class TestRagChunks(unittest.TestCase):
    def test_bidirectional_edge_between_prose_and_exhibit(self):
        doc = make_doc(
            [
                page(
                    [
                        block("#/texts/0", "Exhibit 5: Margins", label="caption"),
                        block("#/texts/1", "Discussed further in Exhibit 5."),
                    ]
                )
            ],
            tables=[table("#/tables/0", caption_refs=["#/texts/0"])],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1",
                    source_refs=["#/tables/0"],
                    roled_cells=[{"row": 0, "col": 0, "text": "a"}],
                )
            ]
        }
        stream = cl.linearize(doc, sem)
        resolution = er.resolve(doc, sem)
        chunks = cl.build_rag_chunks(stream, resolution)

        prose_chunk = next(
            c for c in chunks if c["kind"] == "prose" and "Discussed" in c["text"]
        )
        exhibit_chunk = next(c for c in chunks if c["kind"] == "exhibit")

        self.assertIn(exhibit_chunk["chunk_id"], prose_chunk["related_refs"])
        self.assertIn(prose_chunk["chunk_id"], exhibit_chunk["related_refs"])

    def test_chunks_carry_source_anchors_and_neighbor_edges(self):
        doc = make_doc(
            [
                page(
                    [
                        block("#/texts/0", "intro"),
                        block("#/texts/1", "Exhibit 5: Margins", label="caption"),
                    ]
                )
            ],
            tables=[table("#/tables/0", caption_refs=["#/texts/1"])],
        )
        sem = {
            "exhibits": [
                exhibit(
                    "exhibit-1",
                    source_refs=["#/tables/0"],
                    roled_cells=[{"row": 0, "col": 0, "text": "a"}],
                )
            ]
        }
        stream = cl.linearize(doc, sem)
        resolution = er.resolve(doc, sem)
        chunks = cl.build_rag_chunks(stream, resolution)

        self.assertTrue(all(c.get("source_anchors") for c in chunks))
        self.assertIsNone(chunks[0]["prev_chunk"])
        self.assertEqual(chunks[0]["next_chunk"], chunks[1]["chunk_id"])
        self.assertEqual(chunks[1]["prev_chunk"], chunks[0]["chunk_id"])
        self.assertIsNone(chunks[-1]["next_chunk"])


if __name__ == "__main__":
    unittest.main()
