#!/usr/bin/env python3
"""Exhibit semantics foundation.

Reads a validated ``source_document.json`` (``source-document/v1``) and emits
``exhibit_semantics.json`` (``exhibit-semantics/v1``): the interpretation layer
that classifies exhibits and tags every claim with a source reference and a
confidence drawn from the fixed vocabulary.

This is the ADR-0001 consumer side: it reads the repo-owned source document,
never Docling raw JSON. It is deliberately conservative — coarse classification
and source-anchored hints only. Full table/hierarchy/chart semantics and chart
digitization belong to later changes (``docs/adr/0002-defer-chart-digitization``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import source_document_schema as sds  # noqa: E402
import table_semantics as ts  # noqa: E402

# Exhibit types whose tables get detailed table semantics (change: table-semantics).
_TABLE_SEMANTIC_TYPES = frozenset({"grid_table", "matrix_table", "financial_statement"})

SCHEMA_VERSION = "exhibit-semantics/v1"

EXHIBIT_TYPES = frozenset(
    {
        "grid_table",
        "matrix_table",
        "financial_statement",
        "hierarchy_table",
        "chart",
        "mixed",
    }
)
CONFIDENCE_VOCAB = frozenset({"observed", "inferred", "verified", "hint", "rejected"})

# Coarse financial cues: currency symbols, parenthesized negatives, percent.
_FINANCIAL_RE = re.compile(
    r"[$€£]|\(\s*[\d,]+\s*\)|\d%|\bsubtotal\b|\btotal\b", re.IGNORECASE
)


class ExtractionError(RuntimeError):
    """Raised when the input is not a conforming source document."""


def _cell_text(cell: Any) -> str:
    if isinstance(cell, dict):
        return str(cell.get("text", ""))
    return str(cell)


def _has_span(cells: list[Any]) -> bool:
    for c in cells:
        if isinstance(c, dict) and (
            (c.get("col_span") or 1) > 1 or (c.get("row_span") or 1) > 1
        ):
            return True
    return False


def classify_table(table: dict[str, Any]) -> tuple[str, str]:
    """Return ``(exhibit_type, confidence)`` for a source table.

    Coarse and deterministic. Weak evidence resolves to ``mixed``/``hint``.
    """
    cells = table.get("cells") or []
    if not cells:
        return "mixed", "hint"
    joined = " ".join(_cell_text(c) for c in cells)
    if _has_span(cells):
        return "matrix_table", "inferred"
    if _FINANCIAL_RE.search(joined):
        return "financial_statement", "inferred"
    return "grid_table", "inferred"


def _title_for(refs: list[str], captions_by_ref: dict[str, str]) -> str | None:
    for ref in refs:
        if ref in captions_by_ref:
            return captions_by_ref[ref]
    return None


def extract_exhibit_semantics(source_doc: dict[str, Any]) -> dict[str, Any]:
    """Classify exhibits in a validated source document.

    The caller MUST pass a document that already conforms to ``source-document/v1``.
    """
    # Map caption/text self_ref -> text so exhibit titles can be resolved.
    captions_by_ref: dict[str, str] = {}
    for page in source_doc.get("pages") or []:
        for block in page.get("blocks") or []:
            ref = block.get("self_ref")
            if ref and block.get("text"):
                captions_by_ref[ref] = block["text"]

    exhibits: list[dict[str, Any]] = []
    counter = 0

    for table in source_doc.get("tables") or []:
        ref = table.get("self_ref")
        if not ref:
            # Anchorless: cannot tie a claim to a source anchor -> suppress.
            continue
        counter += 1
        etype, conf = classify_table(table)
        caption_refs = table.get("caption_refs") or []
        hints = [
            {
                "kind": "classification",
                "value": etype,
                "confidence": conf,
                "source_refs": [ref],
            }
        ]
        checks: list[dict[str, Any]] = []
        roled_cells: list[dict[str, Any]] | None = None
        if etype in _TABLE_SEMANTIC_TYPES:
            # Enrich with detailed table semantics (cell roles, subtotal/total
            # candidates, arithmetic checks) per change: table-semantics.
            sem = ts.table_semantics(table, ref)
            roled_cells = sem["roled_cells"]
            hints.extend(sem["hints"])
            checks.extend(sem["checks"])
        exhibit = {
            "id": f"exhibit-{counter}",
            "type": etype,
            "source_refs": [ref],
            "title": _title_for(caption_refs, captions_by_ref),
            "semantic_hints": hints,
            "checks": checks,
        }
        if roled_cells is not None:
            exhibit["roled_cells"] = roled_cells
        exhibits.append(exhibit)

    for figure in source_doc.get("figures") or []:
        ref = figure.get("self_ref")
        if not ref:
            continue
        counter += 1
        caption_refs = figure.get("caption_refs") or []
        exhibits.append(
            {
                "id": f"exhibit-{counter}",
                "type": "chart",
                "source_refs": [ref],
                "title": _title_for(caption_refs, captions_by_ref),
                "semantic_hints": [
                    {
                        "kind": "classification",
                        "value": "chart",
                        "confidence": "inferred",
                        "source_refs": [ref],
                    }
                ],
                # No numeric series: chart digitization is deferred (ADR-0002).
                "checks": [],
            }
        )

    return {"schema_version": SCHEMA_VERSION, "exhibits": exhibits}


def load_and_extract(source_path: Path) -> dict[str, Any]:
    """Validate then extract; raise :class:`ExtractionError` on a bad input."""
    try:
        doc = json.loads(source_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExtractionError(f"source document not found: {source_path}") from exc
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"invalid JSON in {source_path}: {exc}") from exc
    result = sds.validate_source_document(doc)
    if not result.ok:
        raise ExtractionError(
            "source document is not valid source-document/v1:\n  "
            + "\n  ".join(result.errors)
        )
    return extract_exhibit_semantics(doc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract exhibit-semantics/v1 from a validated source_document.json."
    )
    parser.add_argument(
        "source_document", help="Path to a source-document/v1 JSON file."
    )
    parser.add_argument(
        "--output", required=True, help="Path for exhibit_semantics.json."
    )
    args = parser.parse_args(argv)
    try:
        semantics = load_and_extract(Path(args.source_document).expanduser())
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(semantics, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"output": str(out), "exhibits": len(semantics["exhibits"])}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
