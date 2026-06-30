#!/usr/bin/env python3
"""Hierarchy semantics for borderless (no-grid) exhibits.

Infers indentation levels from source-block bounding boxes, maps category
headings to indented child rows, parses value/percentage ranges, and associates
footnote/source-note blocks with the nearest exhibit block. Uncertain structure
is emitted as ``hint``-confidence hints with source references — never asserted.

Operates on ``source-document/v1`` page blocks (observed facts only). Used by
``extract_exhibit_semantics`` to build conservative ``hierarchy_table`` exhibits.
"""

from __future__ import annotations

import re
from typing import Any

import table_semantics as ts

_NOTE_LABELS = frozenset({"footnote", "source", "source_note", "note"})
_NOTE_TEXT_RE = re.compile(r"^\s*(source|note)\b[:\s]", re.IGNORECASE)
# An embedded value range (e.g. "70.0-80.0") or percentage — the borderless-
# hierarchy signal — anywhere within a row's text.
_EMBEDDED_RANGE_RE = re.compile(
    r"\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*%"
)


def _left_edge(block: dict[str, Any]) -> float | None:
    bbox = block.get("bbox")
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 1:
        try:
            return float(bbox[0])
        except (TypeError, ValueError):
            return None
    return None


def infer_indent_levels(
    blocks: list[dict[str, Any]], tol: float = 4.0
) -> dict[str, int]:
    """Cluster block left edges into ordered indent levels (leftmost == 0)."""
    edges = sorted({le for b in blocks if (le := _left_edge(b)) is not None})
    # Greedy cluster representative edges within tolerance.
    clusters: list[float] = []
    for e in edges:
        if not clusters or e - clusters[-1] > tol:
            clusters.append(e)

    def level_for(edge: float | None) -> int:
        if edge is None:
            return 0
        best = 0
        for i, c in enumerate(clusters):
            if abs(edge - c) <= tol:
                best = i
                break
            if edge > c:
                best = i
        return best

    return {b["id"]: level_for(_left_edge(b)) for b in blocks if "id" in b}


def build_parent_child(
    blocks: list[dict[str, Any]], levels: dict[str, int]
) -> list[dict[str, Any]]:
    """Map each block to the nearest preceding shallower block as its parent."""
    out: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []  # (block_id, level)
    for b in blocks:
        bid = b.get("id")
        if bid is None:
            continue
        lvl = levels.get(bid, 0)
        while stack and stack[-1][1] >= lvl:
            stack.pop()
        parent = stack[-1][0] if stack else None
        out.append({"block_id": bid, "level": lvl, "parent_id": parent})
        stack.append((bid, lvl))
    return out


def parse_range(text: str) -> dict[str, Any] | None:
    """Parse a value/percentage range or amount, reusing the shared parser."""
    return ts.parse_amount(text)


def _is_note(block: dict[str, Any]) -> bool:
    label = str(block.get("label", "")).lower()
    if label in _NOTE_LABELS:
        return True
    return bool(_NOTE_TEXT_RE.match(str(block.get("text", ""))))


def associate_notes(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Link each note block to the nearest preceding non-note block."""
    out: list[dict[str, Any]] = []
    last_non_note: str | None = None
    for b in blocks:
        bid = b.get("id")
        if bid is None:
            continue
        if _is_note(b):
            if last_non_note is not None:
                out.append({"note_id": bid, "exhibit_id": last_non_note})
        else:
            last_non_note = bid
    return out


def hierarchy_exhibit_from_blocks(
    blocks: list[dict[str, Any]], source_ref: str, *, tol: float = 4.0
) -> dict[str, Any] | None:
    """Build a conservative ``hierarchy_table`` exhibit, or ``None``.

    Emits only when the blocks show >=2 distinct indent levels and >=1 leaf
    parses as a range/amount. Otherwise returns ``None`` (no spurious exhibit).
    """
    usable = [b for b in blocks if b.get("id")]
    if len(usable) < 2:
        return None
    levels = infer_indent_levels(usable, tol)
    if len({levels.get(b["id"], 0) for b in usable}) < 2:
        return None

    # Require a genuine embedded range/percent leaf (the borderless-hierarchy
    # signal), not a stray number like a year in prose, to avoid false positives.
    if not any(_EMBEDDED_RANGE_RE.search(str(b.get("text", ""))) for b in usable):
        return None

    parentage = build_parent_child(usable, levels)
    hints: list[dict[str, Any]] = [
        {
            "kind": "indent_hierarchy",
            "block_id": p["block_id"],
            "parent_id": p["parent_id"],
            "level": p["level"],
            "confidence": "hint",
            "source_refs": [b_ref(p["block_id"])],
        }
        for p in parentage
    ]
    for note in associate_notes(usable):
        hints.append(
            {
                "kind": "note_association",
                "note_id": note["note_id"],
                "exhibit_id": note["exhibit_id"],
                "confidence": "hint",
                "source_refs": [b_ref(note["note_id"])],
            }
        )
    return {
        "id": "exhibit-hierarchy",
        "type": "hierarchy_table",
        "source_refs": [source_ref],
        "semantic_hints": hints,
        "checks": [],
    }


def b_ref(block_id: str) -> str:
    """Normalize a block id into a source_document anchor reference."""
    return block_id if str(block_id).startswith("#/") else f"#/{block_id}"
