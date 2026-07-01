#!/usr/bin/env python3
"""Composition-linearization-rag: derived third layer over the two canonical
artifacts (``source_document.json`` facts, ``exhibit_semantics.json``
interpretation).

This module never mutates either canonical input. ``linearize`` produces an
ordered stream of text and exhibit-placeholder items using the source
document's native block order as the spine (see
``openspec/changes/composition-linearization-rag/design.md`` Decision 2),
with exhibits inserted at their caption position or, lacking a caption, by
bounding-box position among the native-order blocks (Decision 4).

A prose block is suppressed only when it is a true duplicate of a same-page
table cell: exact text match AND its bbox center lies inside that table's
bbox (Decision 3, conservative dedup).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import exhibit_registry as er  # noqa: E402


def _bbox_top(bbox: Any) -> float:
    if isinstance(bbox, list | tuple) and len(bbox) >= 2:
        return bbox[1]
    return 0.0


def _bbox_center(bbox: Any) -> tuple[float, float] | None:
    if not (isinstance(bbox, list | tuple) and len(bbox) >= 4):
        return None
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


def _point_inside(point: tuple[float, float] | None, bbox: Any) -> bool:
    if point is None or not (isinstance(bbox, list | tuple) and len(bbox) >= 4):
        return False
    x, y = point
    lo_x, hi_x = min(bbox[0], bbox[2]), max(bbox[0], bbox[2])
    lo_y, hi_y = min(bbox[1], bbox[3]), max(bbox[1], bbox[3])
    return lo_x <= x <= hi_x and lo_y <= y <= hi_y


def _exhibit_objects(source_doc: dict[str, Any]) -> list[dict[str, Any]]:
    return list(source_doc.get("tables") or []) + list(source_doc.get("figures") or [])


def _is_true_duplicate(
    block: dict[str, Any], same_page_tables: list[dict[str, Any]]
) -> bool:
    text = str(block.get("text", "")).strip()
    if not text:
        return False
    center = _bbox_center(block.get("bbox"))
    for tbl in same_page_tables:
        cell_texts = {str(c.get("text", "")).strip() for c in (tbl.get("cells") or [])}
        if text in cell_texts and _point_inside(center, tbl.get("bbox")):
            return True
    return False


def linearize(
    source_doc: dict[str, Any], semantics: dict[str, Any]
) -> list[dict[str, Any]]:
    """Linearize ``source_doc`` into an ordered text/exhibit stream.

    Each item is ``{"kind": "text", "page": int, "self_ref": str, "label": str,
    "text": str, "bbox": ...}`` or ``{"kind": "exhibit", "page": int,
    "self_ref": str, "exhibit": dict | None, "object": dict}``.
    """
    ex_by_ref = {
        ref: exhibit
        for exhibit in semantics.get("exhibits") or []
        for ref in exhibit.get("source_refs") or []
    }

    stream: list[dict[str, Any]] = []
    for page in source_doc.get("pages") or []:
        page_number = page.get("page_number")
        blocks = page.get("blocks") or []
        ref_index = {b["self_ref"]: i for i, b in enumerate(blocks)}

        page_objects = [
            obj
            for obj in _exhibit_objects(source_doc)
            if obj.get("page_number") == page_number
        ]
        page_tables = [
            t
            for t in source_doc.get("tables") or []
            if t.get("page_number") == page_number
        ]

        # Group exhibit insertions by the block index they attach after;
        # exhibits with no viable anchor sort ahead of the page.
        inserts_after: dict[int, list[dict[str, Any]]] = {}
        head_inserts: list[dict[str, Any]] = []
        for obj in page_objects:
            caption_ref = next(iter(obj.get("caption_refs") or []), None)
            if caption_ref in ref_index:
                inserts_after.setdefault(ref_index[caption_ref], []).append(obj)
                continue
            # bbox fallback: insert after the last native-order block whose
            # top is at or above the exhibit's top (i.e. appears before it).
            exhibit_top = _bbox_top(obj.get("bbox"))
            anchor_idx = -1
            for i, blk in enumerate(blocks):
                if _bbox_top(blk.get("bbox")) >= exhibit_top:
                    anchor_idx = i
            if anchor_idx < 0:
                head_inserts.append(obj)
            else:
                inserts_after.setdefault(anchor_idx, []).append(obj)

        def emit_exhibit(
            obj: dict[str, Any], *, page_number: Any = page_number
        ) -> None:
            stream.append(
                {
                    "kind": "exhibit",
                    "page": page_number,
                    "self_ref": obj["self_ref"],
                    "exhibit": ex_by_ref.get(obj["self_ref"]),
                    "object": obj,
                }
            )

        for obj in head_inserts:
            emit_exhibit(obj)

        for i, blk in enumerate(blocks):
            if not _is_true_duplicate(blk, page_tables):
                stream.append(
                    {
                        "kind": "text",
                        "page": page_number,
                        "self_ref": blk.get("self_ref"),
                        "label": blk.get("label", "text"),
                        "text": blk.get("text", ""),
                        "bbox": blk.get("bbox"),
                    }
                )
            for obj in inserts_after.get(i, []):
                emit_exhibit(obj)

    return stream


def _render_table_body(exhibit: dict[str, Any] | None) -> str:
    if exhibit is None:
        return "_(unmapped)_"
    cells = exhibit.get("roled_cells")
    if not cells:
        return "_(chart — image preserved only)_"
    ncol = max((c["col"] for c in cells), default=0) + 1
    rows: dict[int, dict[int, str]] = {}
    for c in cells:
        rows.setdefault(c["row"], {})[c["col"]] = c["text"]
    lines = []
    for i, row_idx in enumerate(sorted(rows)):
        row = rows[row_idx]
        lines.append("| " + " | ".join(row.get(ci, "") for ci in range(ncol)) + " |")
        if i == 0:
            lines.append("|" + "|".join([" --- "] * ncol) + "|")
    return "\n".join(lines)


def _annotate_references(text: str, resolution: dict[str, Any]) -> str:
    bindings = resolution.get("bindings", {})
    annotations = []
    for match in er.EXHIBIT_MENTION.finditer(text):
        number = match.group(1)
        binding = bindings.get(number)
        if binding is not None:
            annotations.append(
                f"(Exhibit {number} -> {binding['exhibit_id']}, {binding['tier']})"
            )
        else:
            annotations.append(f"(Exhibit {number}: unresolved)")
    if not annotations:
        return text
    return text + "  " + " ".join(annotations)


def render_reading_view(
    stream: list[dict[str, Any]], resolution: dict[str, Any]
) -> str:
    """Render the human reading view: interleaved prose and exhibit bodies.

    Each prose block's "Exhibit N" references are annotated with their
    resolved target and confidence, or marked unresolved. Each exhibit
    appears as a placeholder anchor followed by its rendered body.
    """
    lines: list[str] = []
    current_page: Any = None
    for item in stream:
        if item["page"] != current_page:
            current_page = item["page"]
            lines.append(f"\n## Page {current_page}\n")
        if item["kind"] == "text":
            label = item.get("label", "text")
            text = item.get("text", "")
            annotated = _annotate_references(text, resolution)
            if label in ("section_header", "page_header"):
                lines.append(f"### {annotated}")
            elif label == "caption":
                lines.append(f"*{annotated}*")
            else:
                lines.append(annotated)
        else:
            exhibit = item.get("exhibit")
            eid = exhibit["id"] if exhibit else "?"
            etype = exhibit["type"] if exhibit else "unknown"
            title = (exhibit or {}).get("title")
            header = f"\n**⟦{eid} · {etype} · `{item['self_ref']}`⟧**"
            if title:
                header += f" — {title}"
            lines.append(header)
            lines.append(_render_table_body(exhibit))
    return "\n".join(lines) + "\n"


def build_rag_chunks(
    stream: list[dict[str, Any]], resolution: dict[str, Any]
) -> list[dict[str, Any]]:
    """Emit one RAG chunk per prose section and per exhibit.

    Each chunk carries its source anchors. Prose chunks and the exhibits
    they resolve reference each other (bidirectional ``related_refs``).
    Reading-order neighbor edges (``prev_chunk``/``next_chunk``) are added
    across the full chunk sequence.
    """
    bindings = resolution.get("bindings", {})
    chunks: list[dict[str, Any]] = []
    buf: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal buf
        if buf is not None and buf["source_anchors"]:
            chunks.append(buf)
        buf = None

    for item in stream:
        if item["kind"] == "text":
            label = item.get("label", "text")
            text = item.get("text", "")
            if label in ("section_header", "page_header") or buf is None:
                flush()
                buf = {
                    "chunk_id": f"chunk-{len(chunks):03d}",
                    "kind": "prose",
                    "page": item["page"],
                    "text": "",
                    "source_anchors": [],
                    "related_refs": [],
                    "unresolved_refs": [],
                }
            buf["text"] += ("\n" if buf["text"] else "") + text
            buf["source_anchors"].append(item["self_ref"])
            for match in er.EXHIBIT_MENTION.finditer(text):
                number = match.group(1)
                binding = bindings.get(number)
                if binding is not None:
                    buf["related_refs"].append(binding["exhibit_id"])
                else:
                    buf["unresolved_refs"].append(f"Exhibit {number}")
        else:
            flush()
            exhibit = item.get("exhibit")
            chunks.append(
                {
                    "chunk_id": f"chunk-{len(chunks):03d}",
                    "kind": "exhibit",
                    "page": item["page"],
                    "exhibit_id": (exhibit or {}).get("id"),
                    "exhibit_type": (exhibit or {}).get("type"),
                    "title": (exhibit or {}).get("title"),
                    "source_anchors": [item["self_ref"]],
                    "related_refs": [],
                }
            )
    flush()

    # Backfill: an exhibit's related_refs is the set of prose chunks that
    # resolved a reference to it (bidirectional edge, Decision requirement).
    chunk_by_exhibit_id = {
        c["exhibit_id"]: c["chunk_id"] for c in chunks if c["kind"] == "exhibit"
    }
    for c in chunks:
        if c["kind"] == "prose":
            c["related_refs"] = [
                chunk_by_exhibit_id[eid]
                for eid in c["related_refs"]
                if eid in chunk_by_exhibit_id
            ]
    prose_chunks_by_exhibit_chunk: dict[str, list[str]] = {}
    for c in chunks:
        if c["kind"] == "prose":
            for exhibit_chunk_id in c["related_refs"]:
                prose_chunks_by_exhibit_chunk.setdefault(exhibit_chunk_id, []).append(
                    c["chunk_id"]
                )
    for c in chunks:
        if c["kind"] == "exhibit":
            c["related_refs"] = prose_chunks_by_exhibit_chunk.get(c["chunk_id"], [])

    for i, c in enumerate(chunks):
        c["prev_chunk"] = chunks[i - 1]["chunk_id"] if i > 0 else None
        c["next_chunk"] = chunks[i + 1]["chunk_id"] if i + 1 < len(chunks) else None

    return chunks


def compose(
    source_doc: dict[str, Any], semantics: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run linearization and reference resolution over the two canonical inputs."""
    stream = linearize(source_doc, semantics)
    resolution = er.resolve(source_doc, semantics)
    return stream, resolution


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compose the reading_view and rag_chunks projections from a "
            "source_document.json and exhibit_semantics.json. Never mutates "
            "either input."
        )
    )
    parser.add_argument("source_document", help="Path to source_document.json")
    parser.add_argument("exhibit_semantics", help="Path to exhibit_semantics.json")
    parser.add_argument(
        "--reading-view", required=True, help="Output path for reading_view.md"
    )
    parser.add_argument(
        "--rag-chunks", required=True, help="Output path for rag_chunks.jsonl"
    )
    args = parser.parse_args(argv)

    source_doc = json.loads(Path(args.source_document).read_text(encoding="utf-8"))
    semantics = json.loads(Path(args.exhibit_semantics).read_text(encoding="utf-8"))
    stream, resolution = compose(source_doc, semantics)

    reading_view_path = Path(args.reading_view)
    reading_view_path.parent.mkdir(parents=True, exist_ok=True)
    reading_view_path.write_text(
        render_reading_view(stream, resolution), encoding="utf-8"
    )

    rag_chunks = build_rag_chunks(stream, resolution)
    rag_chunks_path = Path(args.rag_chunks)
    rag_chunks_path.parent.mkdir(parents=True, exist_ok=True)
    rag_chunks_path.write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in rag_chunks) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "reading_view": str(reading_view_path),
                "rag_chunks": str(rag_chunks_path),
                "chunks": len(rag_chunks),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
