#!/usr/bin/env python3
"""Tests for the compose_layout CLI entry (task 4.1): reads the two canonical
artifacts and writes the two projections without mutating the inputs."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import compose_layout as cl  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SOURCE_DOC = FIXTURES / "composition_source_document.json"
EXHIBIT_SEMANTICS = FIXTURES / "composition_exhibit_semantics.json"


class TestCLI(unittest.TestCase):
    def test_canonical_inputs_unchanged_and_projections_written(self):
        before_source = SOURCE_DOC.read_bytes()
        before_semantics = EXHIBIT_SEMANTICS.read_bytes()

        with tempfile.TemporaryDirectory() as tmp:
            reading_view_path = Path(tmp) / "reading_view.md"
            rag_chunks_path = Path(tmp) / "rag_chunks.jsonl"
            rc = cl.main(
                [
                    str(SOURCE_DOC),
                    str(EXHIBIT_SEMANTICS),
                    "--reading-view",
                    str(reading_view_path),
                    "--rag-chunks",
                    str(rag_chunks_path),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertTrue(reading_view_path.exists())
            self.assertTrue(rag_chunks_path.exists())
            self.assertGreater(reading_view_path.stat().st_size, 0)
            self.assertGreater(rag_chunks_path.stat().st_size, 0)

        self.assertEqual(SOURCE_DOC.read_bytes(), before_source)
        self.assertEqual(EXHIBIT_SEMANTICS.read_bytes(), before_semantics)


if __name__ == "__main__":
    unittest.main()
