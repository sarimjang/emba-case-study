"""Tests for structured-evidence rendering across generators (change: export-source-ref-rendering)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import case_spec_utils as csu  # noqa: E402
import generate_case_docx as gdocx  # noqa: E402
import generate_case_md as gmd  # noqa: E402
import generate_case_pptx as gpptx  # noqa: E402

STRUCTURED = {
    "text": "Valves carry the highest margin.",
    "source_refs": ["exhibit-1"],
    "evidence_type": "exhibit_interpretation",
}


def _spec(signals):
    return {
        "case": {"title": "Wilkerson"},
        "decision_pivot": {
            "decision_owner": "CEO",
            "decision_question": "Q?",
            "urgency": "high",
            "delay_cost": "erosion",
        },
        "company_industry_context": {},
        "core_dilemma": {
            "surface_problem": "a",
            "root_problem": "b",
            "key_tension": "c",
        },
        "evidence": {"quantitative_signals": signals},
        "options": [{"title": "A", "how": "h", "why": "w", "trade_off": "t"}],
    }


class HelperTests(unittest.TestCase):
    def test_string_passthrough(self):
        self.assertEqual(csu.evidence_item_text("Plain note"), "Plain note")

    def test_object_with_refs(self):
        out = csu.evidence_item_text(STRUCTURED)
        self.assertTrue(out.startswith("Valves carry the highest margin."))
        self.assertIn("exhibit-1", out)

    def test_object_without_refs(self):
        out = csu.evidence_item_text({"text": "No refs here"})
        self.assertEqual(out, "No refs here")
        self.assertNotIn("sources:", out)


class MarkdownRenderTests(unittest.TestCase):
    def test_structured_rendered(self):
        md = gmd.build_markdown(_spec([STRUCTURED]))
        self.assertIn("Valves carry the highest margin.", md)
        self.assertIn("exhibit-1", md)

    def test_legacy_string_unchanged(self):
        spec = _spec(["Plain signal."])
        self.assertIn("- Plain signal.", gmd.build_markdown(spec))
        # No reference decoration introduced for a plain string.
        self.assertNotIn("(sources:", gmd.build_markdown(spec))


class DocxRenderTests(unittest.TestCase):
    def _paragraph_texts(self, doc):
        return [p.text for p in doc.paragraphs]

    def test_structured_rendered(self):
        doc = gdocx.build_document(_spec([STRUCTURED]))
        joined = "\n".join(self._paragraph_texts(doc))
        self.assertIn("Valves carry the highest margin.", joined)
        self.assertIn("exhibit-1", joined)

    def test_legacy_string_unchanged(self):
        doc = gdocx.build_document(_spec(["Plain signal."]))
        joined = "\n".join(self._paragraph_texts(doc))
        self.assertIn("Plain signal.", joined)
        self.assertNotIn("(sources:", joined)


class PptxRenderTests(unittest.TestCase):
    def _all_text(self, prs):
        out = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    out.append(shape.text_frame.text)
        return "\n".join(out)

    def test_structured_rendered(self):
        builder = gpptx.DeckBuilder(_spec([STRUCTURED]))
        builder.render()
        text = self._all_text(builder.prs)
        self.assertIn("Valves carry the highest margin.", text)
        self.assertIn("exhibit-1", text)


if __name__ == "__main__":
    unittest.main()
