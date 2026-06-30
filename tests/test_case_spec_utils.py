from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from case_spec_utils import (  # noqa: E402
    MAX_SPEC_BYTES,
    OutputPathError,
    SpecValidationError,
    load_spec,
    prepare_output_path,
)


class CaseSpecUtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_path = REPO_ROOT / "scripts" / "examples" / "case_spec.sample.json"

    def test_load_spec_accepts_sample(self) -> None:
        spec = load_spec(self.sample_path)
        self.assertEqual(spec["case"]["title"], "Sample Case Analysis")

    def test_load_spec_rejects_missing_required_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            broken = json.loads(self.sample_path.read_text(encoding="utf-8"))
            del broken["case"]["title"]
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(SpecValidationError):
                load_spec(path)

    def test_load_spec_rejects_oversized_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "huge.json"
            huge = {
                "case": {"title": "x" * (MAX_SPEC_BYTES + 100)},
                "decision_pivot": {
                    "decision_owner": "owner",
                    "decision_question": "question",
                    "urgency": "urgent",
                    "delay_cost": "cost",
                    "milestones": [],
                },
                "company_industry_context": {
                    "company_background": [],
                    "industry_background": [],
                    "structural_breakdown": {},
                },
                "core_dilemma": {
                    "surface_problem": "surface",
                    "root_problem": "root",
                    "five_whys": [],
                    "trade_offs": [],
                    "key_tension": "tension",
                },
                "evidence": {
                    "quantitative_signals": [],
                    "internal_checks": [],
                    "external_checks": [],
                },
                "options": [
                    {
                        "title": "one",
                        "how": "how",
                        "why": "why",
                        "trade_off": "trade-off",
                    }
                ],
            }
            path.write_text(json.dumps(huge), encoding="utf-8")
            with self.assertRaises(SpecValidationError):
                load_spec(path)

    def test_prepare_output_path_rejects_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            outside = Path(tmp) / "outside.md"
            with self.assertRaises(OutputPathError):
                prepare_output_path(
                    outside,
                    allowed_roots=[root],
                    expected_suffix=".md",
                )

    def test_prepare_output_path_allows_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            outside = Path(tmp) / "outside.md"
            prepared = prepare_output_path(
                outside,
                allowed_roots=[root],
                expected_suffix=".md",
                allow_outside_workspace=True,
            )
            self.assertEqual(prepared, outside.resolve())

    def test_markdown_cli_blocks_outside_workspace_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "generate_case_md.py"),
                    str(self.sample_path),
                    str(outside),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to write outside the local workspace roots", result.stderr)

    def test_markdown_cli_allows_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "generate_case_md.py"),
                    "--allow-outside-workspace",
                    str(self.sample_path),
                    str(outside),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(outside.exists())


if __name__ == "__main__":
    unittest.main()
