#!/usr/bin/env python3
"""Table semantics: cell roles, financial amount parsing, subtotal/total
detection, and evidence-gated arithmetic checks.

Pure functions that enrich ``exhibit-semantics/v1`` table exhibits. Nothing is
coerced: a cell that is not a parseable amount stays unparsed, and an arithmetic
check is emitted only when a column's data values all parse (`CONTEXT.md`
"Semantic Confidence"). Used by ``extract_exhibit_semantics`` for grid/matrix/
financial exhibits.
"""

from __future__ import annotations

import re
from typing import Any

CELL_ROLES = frozenset({"column_group_header", "column_header", "row_header", "data"})

_TOTAL_LABEL_RE = re.compile(r"\b(sub)?total\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
_RANGE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*%?\s*$")


def _cell_field(cell: Any, *names: str, default: Any = None) -> Any:
    if isinstance(cell, dict):
        for n in names:
            if n in cell and cell[n] is not None:
                return cell[n]
    return default


def _span(cell: Any, kind: str) -> int:
    explicit = _cell_field(cell, f"{kind}_span")
    if isinstance(explicit, int) and explicit > 0:
        return explicit
    start = _cell_field(cell, f"start_{kind}_offset_idx")
    end = _cell_field(cell, f"end_{kind}_offset_idx")
    if isinstance(start, int) and isinstance(end, int) and end > start:
        return end - start
    return 1


def classify_cell_roles(table: dict[str, Any]) -> list[dict[str, Any]]:
    """Annotate each table cell with a role, preserving spans and blank cells."""
    roled: list[dict[str, Any]] = []
    for cell in table.get("cells") or []:
        text = str(_cell_field(cell, "text", default="") or "")
        col_span = _span(cell, "col")
        row_span = _span(cell, "row")
        is_col_header = bool(_cell_field(cell, "column_header", default=False))
        is_row_header = bool(_cell_field(cell, "row_header", default=False))
        if is_col_header and col_span > 1:
            role = "column_group_header"
        elif is_col_header:
            role = "column_header"
        elif is_row_header:
            role = "row_header"
        else:
            role = "data"
        roled.append(
            {
                "text": text,
                "role": role,
                "col_span": col_span,
                "row_span": row_span,
                "row": _cell_field(cell, "row", "start_row_offset_idx"),
                "col": _cell_field(cell, "col", "start_col_offset_idx"),
            }
        )
    return roled


def parse_amount(text: str) -> dict[str, Any] | None:
    """Parse a financial amount; return a typed result or ``None`` if not an amount.

    Handles currency symbols, thousands separators, percentages, value ranges,
    and parenthesized negatives. Never coerces non-amounts.
    """
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None

    range_match = _RANGE_RE.match(raw)
    if range_match:
        low, high = float(range_match.group(1)), float(range_match.group(2))
        return {"kind": "range", "low": low, "high": high}

    negative = raw.startswith("(") and raw.endswith(")")
    body = raw[1:-1] if negative else raw
    is_percent = body.rstrip().endswith("%")

    num_match = _NUMBER_RE.search(body)
    if not num_match:
        return None
    # Reject cells that carry substantial non-numeric text (free prose).
    cleaned = num_match.group(0).replace(",", "")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if negative:
        value = -abs(value)
    if is_percent:
        return {"kind": "percent", "value": value}
    return {"kind": "number", "value": value}


def detect_subtotal_total_candidates(
    roled_cells: list[dict[str, Any]], source_ref: str
) -> list[dict[str, Any]]:
    """Mark rows whose row-header text indicates a subtotal/total as candidates."""
    hints: list[dict[str, Any]] = []
    for cell in roled_cells:
        if cell["role"] == "row_header" and _TOTAL_LABEL_RE.search(cell["text"]):
            hints.append(
                {
                    "kind": "subtotal_total_candidate",
                    "value": cell["text"],
                    "row": cell.get("row"),
                    "confidence": "hint",
                    "source_refs": [source_ref],
                }
            )
    return hints


def arithmetic_checks(
    roled_cells: list[dict[str, Any]], source_ref: str, *, tolerance: float = 0.01
) -> list[dict[str, Any]]:
    """Emit an arithmetic check per column that has a total row and parseable data.

    A matching sum is ``verified``; a mismatch is ``rejected``; an unparseable
    column produces no check.
    """
    # Identify total rows by row index.
    total_rows = {
        c.get("row")
        for c in roled_cells
        if c["role"] == "row_header" and _TOTAL_LABEL_RE.search(c["text"])
    }
    if not total_rows:
        return []

    # Group parseable numeric cells by column.
    by_col: dict[Any, list[dict[str, Any]]] = {}
    for c in roled_cells:
        if c["role"] != "data":
            continue
        parsed = parse_amount(c["text"])
        if parsed is None or parsed["kind"] not in ("number", "percent"):
            continue
        by_col.setdefault(c.get("col"), []).append({**c, "_value": parsed["value"]})

    checks: list[dict[str, Any]] = []
    for col, cells in by_col.items():
        total_cells = [c for c in cells if c.get("row") in total_rows]
        data_cells = [c for c in cells if c.get("row") not in total_rows]
        # Need exactly one total and at least two data rows that all parsed.
        if len(total_cells) != 1 or len(data_cells) < 2:
            continue
        # Require the column to be fully parseable: no data cell in this column
        # was skipped for being unparseable.
        raw_data = [
            c
            for c in roled_cells
            if c["role"] == "data"
            and c.get("col") == col
            and c.get("row") not in total_rows
        ]
        if len(raw_data) != len(data_cells):
            continue  # some cell did not parse -> no check
        total = total_cells[0]["_value"]
        summed = sum(c["_value"] for c in data_cells)
        confidence = "verified" if abs(summed - total) <= tolerance else "rejected"
        checks.append(
            {
                "kind": "arithmetic",
                "column": col,
                "sum": summed,
                "total": total,
                "confidence": confidence,
                "source_refs": [source_ref],
            }
        )
    return checks


def table_semantics(table: dict[str, Any], source_ref: str) -> dict[str, Any]:
    """Convenience aggregator returning roles, candidate hints, and checks."""
    roled = classify_cell_roles(table)
    return {
        "roled_cells": roled,
        "hints": detect_subtotal_total_candidates(roled, source_ref),
        "checks": arithmetic_checks(roled, source_ref),
    }
