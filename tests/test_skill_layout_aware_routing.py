"""Content checks for SKILL.md layout-aware routing guidance (change: skill-workflow-layout-aware-routing)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"


class SkillRoutingContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_names_layout_aware_adapter_and_output(self):
        self.assertIn("scripts/ingest_with_docling.py", self.text)
        self.assertIn("source_document.json", self.text)

    def test_discloses_structure_preservation_tradeoff(self):
        # Plain path loses structure; layout-aware path preserves it.
        self.assertTrue(re.search(r"loses? structure", self.text, re.IGNORECASE))
        self.assertTrue(re.search(r"preserve", self.text, re.IGNORECASE))

    def test_requires_consent_for_adapter_ingestion(self):
        self.assertTrue(
            re.search(r"consent", self.text, re.IGNORECASE),
            "SKILL.md must require consent before layout-aware ingestion",
        )

    def test_does_not_instruct_weakening_gates(self):
        self.assertTrue(
            re.search(
                r"never weaken|not weaken|without weakening", self.text, re.IGNORECASE
            ),
            "SKILL.md must preserve the privacy/network/model-download gates",
        )

    def test_requires_source_anchor_before_trust(self):
        self.assertIn("exhibit_semantics.json", self.text)
        self.assertTrue(
            re.search(r"anchor", self.text, re.IGNORECASE),
            "SKILL.md must require a source anchor before trusting exhibit claims",
        )

    def test_does_not_instruct_reading_raw_docling_json(self):
        # Downstream must depend on source_document.json, never raw Docling JSON.
        self.assertTrue(
            re.search(r"never read Docling raw JSON", self.text, re.IGNORECASE)
        )


if __name__ == "__main__":
    unittest.main()
