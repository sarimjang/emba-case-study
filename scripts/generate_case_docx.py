#!/usr/bin/env python3
"""Generate a reusable EMBA-style case analysis DOCX from structured JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


FONT = "Microsoft JhengHei"
TITLE_COLOR = RGBColor(25, 43, 79)
HEADING_COLOR = RGBColor(49, 91, 163)
TEXT_COLOR = RGBColor(40, 40, 40)
MUTED_COLOR = RGBColor(95, 103, 115)


def load_spec(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_doc_defaults(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(11)
    normal.font.color.rgb = TEXT_COLOR


def add_run_font(run, size: int, *, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color


def add_title_block(doc: Document, spec: dict[str, Any]) -> None:
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run(spec["title"])
    add_run_font(r, 20, bold=True, color=TITLE_COLOR)

    subtitle = spec.get("subtitle")
    if subtitle:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(subtitle)
        add_run_font(r, 11, color=MUTED_COLOR)

    if spec.get("metadata"):
        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for idx, item in enumerate(spec["metadata"]):
            if idx:
                sep = meta.add_run(" | ")
                add_run_font(sep, 9, color=MUTED_COLOR)
            r = meta.add_run(item)
            add_run_font(r, 9, color=MUTED_COLOR)


def add_bullets(doc: Document, items: list[str], *, level: int = 0) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        if level:
            p.paragraph_format.left_indent = Inches(0.25 * level)
        r = p.add_run(item)
        add_run_font(r, 11)


def add_numbered(doc: Document, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Number")
        r = p.add_run(item)
        add_run_font(r, 11)


def add_table(doc: Document, table_spec: dict[str, Any]) -> None:
    headers = table_spec["headers"]
    rows = table_spec["rows"]
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True

    for idx, header in enumerate(headers):
        cell = table.cell(0, idx)
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(header)
        add_run_font(r, 10, bold=True, color=RGBColor(255, 255, 255))
        set_cell_shading(cell, "315BA3")

    fills = ("FFFFFF", "F6F8FB")
    for row_idx, row in enumerate(rows, start=1):
        for col_idx, value in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(str(value))
            add_run_font(r, 10)
            set_cell_shading(cell, fills[row_idx % 2])


def add_callout(doc: Document, title: str, bullets: list[str]) -> None:
    p = doc.add_paragraph()
    r = p.add_run(title)
    add_run_font(r, 12, bold=True, color=HEADING_COLOR)
    add_bullets(doc, bullets)


def add_section(doc: Document, section_spec: dict[str, Any]) -> None:
    heading = doc.add_paragraph()
    r = heading.add_run(section_spec["heading"])
    add_run_font(r, 15, bold=True, color=HEADING_COLOR)

    if section_spec.get("summary"):
        p = doc.add_paragraph()
        r = p.add_run(section_spec["summary"])
        add_run_font(r, 11)

    for block in section_spec.get("blocks", []):
        kind = block["kind"]
        if kind == "paragraph":
            p = doc.add_paragraph()
            r = p.add_run(block["text"])
            add_run_font(r, 11)
        elif kind == "bullets":
            add_bullets(doc, block["items"], level=block.get("level", 0))
        elif kind == "numbered":
            add_numbered(doc, block["items"])
        elif kind == "table":
            add_table(doc, block)
        elif kind == "callout":
            add_callout(doc, block["title"], block["bullets"])
        else:
            raise ValueError(f"Unsupported DOCX block kind: {kind}")


def build_document(spec: dict[str, Any]) -> Document:
    doc = Document()
    set_doc_defaults(doc)
    add_title_block(doc, spec["document"])

    for idx, section_spec in enumerate(spec["sections"]):
        if idx:
            doc.add_paragraph()
        add_section(doc, section_spec)

    appendix = spec.get("appendix")
    if appendix:
        doc.add_section(WD_SECTION_START.CONTINUOUS)
        add_section(doc, appendix)

    return doc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a reusable EMBA-style case-analysis DOCX from JSON.")
    parser.add_argument("spec", type=Path, help="Path to document specification JSON file.")
    parser.add_argument("output", type=Path, help="Path to output .docx file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = load_spec(args.spec)
    doc = build_document(spec)
    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
