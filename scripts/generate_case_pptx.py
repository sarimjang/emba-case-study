#!/usr/bin/env python3
"""Generate a reusable EMBA-style case analysis PPTX from structured JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt


SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
FONT = "Microsoft JhengHei"
DEFAULT_FOOTER = "Generated from structured case-analysis data"

COLORS = {
    "navy": RGBColor(25, 43, 79),
    "blue": RGBColor(49, 91, 163),
    "teal": RGBColor(34, 123, 157),
    "green": RGBColor(66, 122, 92),
    "gold": RGBColor(184, 138, 61),
    "red": RGBColor(180, 61, 54),
    "ink": RGBColor(40, 40, 40),
    "muted": RGBColor(95, 103, 115),
    "line": RGBColor(215, 220, 228),
    "bg": RGBColor(246, 248, 251),
    "white": RGBColor(255, 255, 255),
}


def load_spec(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class DeckBuilder:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.prs = Presentation()
        self.prs.slide_width = SLIDE_W
        self.prs.slide_height = SLIDE_H
        self.layout = self.prs.slide_layouts[6]
        self.deck_title = self.spec.get("deck", {}).get("title", "Case Analysis")

    def color(self, name: str | None, fallback: str = "blue") -> RGBColor:
        return COLORS.get(name or "", COLORS[fallback])

    def add_bg(self, slide, color_name: str = "bg") -> None:
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = self.color(color_name, "bg")
        shape.line.fill.background()
        slide.shapes._spTree.remove(shape._element)
        slide.shapes._spTree.insert(2, shape._element)

    def add_header(self, slide, title: str, subtitle: str | None = None) -> None:
        title_box = slide.shapes.add_textbox(Inches(0.55), Inches(0.35), Inches(10.5), Inches(0.7))
        p = title_box.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = title
        r.font.name = FONT
        r.font.size = Pt(24)
        r.font.bold = True
        r.font.color.rgb = COLORS["navy"]

        if subtitle:
            sub_box = slide.shapes.add_textbox(Inches(0.58), Inches(0.96), Inches(11.2), Inches(0.45))
            p = sub_box.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = subtitle
            r.font.name = FONT
            r.font.size = Pt(10.5)
            r.font.color.rgb = COLORS["muted"]

    def add_footer(self, slide, text: str | None = None) -> None:
        footer_text = text or self.spec.get("deck", {}).get("default_footer") or DEFAULT_FOOTER
        box = slide.shapes.add_textbox(Inches(0.55), Inches(7.0), Inches(12.1), Inches(0.25))
        p = box.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run()
        r.text = footer_text
        r.font.name = FONT
        r.font.size = Pt(8.5)
        r.font.color.rgb = COLORS["muted"]

    def add_banner_title(self, slide, title: str, subtitle_lines: list[str]) -> None:
        banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, Inches(1.25))
        banner.fill.solid()
        banner.fill.fore_color.rgb = COLORS["navy"]
        banner.line.fill.background()

        box = slide.shapes.add_textbox(Inches(0.6), Inches(0.32), Inches(11.8), Inches(0.55))
        p = box.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = title
        r.font.name = FONT
        r.font.size = Pt(28)
        r.font.bold = True
        r.font.color.rgb = COLORS["white"]

        sub = slide.shapes.add_textbox(Inches(0.62), Inches(1.55), Inches(10.8), Inches(1.1))
        tf = sub.text_frame
        for idx, line in enumerate(subtitle_lines):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            r = p.add_run()
            r.text = line
            r.font.name = FONT
            r.font.size = Pt(19 if idx == 0 else 13)
            r.font.color.rgb = COLORS["ink"] if idx == 0 else COLORS["muted"]

    def add_bullets(
        self,
        slide,
        items: list[str],
        x,
        y,
        w,
        h,
        *,
        size: int = 15,
        color_name: str = "ink",
    ):
        box = slide.shapes.add_textbox(x, y, w, h)
        tf = box.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        first = True
        for item in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.space_after = Pt(6)
            r = p.add_run()
            r.text = item
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.color.rgb = self.color(color_name, "ink")
        return box

    def add_card(self, slide, card: dict[str, Any], x, y, w, h) -> None:
        accent = self.color(card.get("accent"), "blue")
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = COLORS["white"]
        shape.line.color.rgb = COLORS["line"]

        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.12))
        band.fill.solid()
        band.fill.fore_color.rgb = accent
        band.line.fill.background()

        title_box = slide.shapes.add_textbox(x + Inches(0.18), y + Inches(0.15), w - Inches(0.3), Inches(0.35))
        p = title_box.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = card["title"]
        r.font.name = FONT
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = COLORS["navy"]

        self.add_bullets(slide, card.get("bullets", []), x + Inches(0.18), y + Inches(0.55), w - Inches(0.35), h - Inches(0.7), size=12)

    def add_table(self, slide, spec: dict[str, Any], x, y, w, h) -> None:
        headers = spec["headers"]
        rows = spec["rows"]
        table = slide.shapes.add_table(len(rows) + 1, len(headers), x, y, w, h).table
        accent = self.color(spec.get("accent"), "navy")

        for col, header in enumerate(headers):
            cell = table.cell(0, col)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = accent
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    r.font.name = FONT
                    r.font.size = Pt(11)
                    r.font.bold = True
                    r.font.color.rgb = COLORS["white"]

        for row_idx, row in enumerate(rows, start=1):
            for col_idx, value in enumerate(row):
                cell = table.cell(row_idx, col_idx)
                cell.text = value
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLORS["white"] if row_idx % 2 else COLORS["bg"]
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.name = FONT
                        r.font.size = Pt(10.5)
                        r.font.color.rgb = COLORS["ink"]

    def add_bar_chart(self, slide, spec: dict[str, Any], x, y, w, h) -> None:
        data = CategoryChartData()
        data.categories = spec["categories"]
        data.add_series(spec.get("series_name", "Series 1"), tuple(spec["values"]))
        chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, x, y, w, h, data).chart
        chart.has_legend = bool(spec.get("show_legend", False))
        chart.value_axis.maximum_scale = spec.get("max_scale", 100)
        chart.value_axis.minimum_scale = spec.get("min_scale", 0)
        chart.value_axis.tick_labels.number_format = spec.get("number_format", '0"%"')
        chart.category_axis.tick_labels.font.size = Pt(11)
        chart.value_axis.tick_labels.font.size = Pt(10)
        chart.series[0].format.fill.solid()
        chart.series[0].format.fill.fore_color.rgb = self.color(spec.get("accent"), "teal")

    def render_title_slide(self, slide_spec: dict[str, Any]) -> None:
        slide = self.prs.slides.add_slide(self.layout)
        self.add_bg(slide, slide_spec.get("background", "bg"))
        self.add_banner_title(slide, slide_spec["title"], slide_spec.get("subtitle_lines", []))
        cards = slide_spec.get("hero_cards", [])
        left = Inches(0.62)
        gap = Inches(0.23)
        count = max(1, len(cards))
        width = (Inches(12.15) - gap * (count - 1)) / count
        for idx, card in enumerate(cards):
            self.add_card(slide, card, left + idx * (width + gap), Inches(3.0), width, Inches(2.25))
        self.add_footer(slide, slide_spec.get("footer"))

    def render_cards_slide(self, slide_spec: dict[str, Any]) -> None:
        slide = self.prs.slides.add_slide(self.layout)
        self.add_bg(slide, slide_spec.get("background", "bg"))
        self.add_header(slide, slide_spec["title"], slide_spec.get("subtitle"))
        cards = slide_spec["cards"]
        cols = slide_spec.get("columns", len(cards))
        gap = Inches(0.2)
        card_w = (Inches(12.2) - gap * (cols - 1)) / cols
        card_h = slide_spec.get("card_height_inches", 4.85)
        start_x = Inches(0.55)
        start_y = Inches(slide_spec.get("top_inches", 1.45))
        for idx, card in enumerate(cards):
            col = idx % cols
            row = idx // cols
            x = start_x + col * (card_w + gap)
            y = start_y + row * (Inches(card_h) + gap)
            self.add_card(slide, card, x, y, card_w, Inches(card_h))
        self.add_footer(slide, slide_spec.get("footer"))

    def render_table_slide(self, slide_spec: dict[str, Any]) -> None:
        slide = self.prs.slides.add_slide(self.layout)
        self.add_bg(slide, slide_spec.get("background", "bg"))
        self.add_header(slide, slide_spec["title"], slide_spec.get("subtitle"))
        table_spec = slide_spec["table"]
        self.add_table(slide, table_spec, Inches(0.6), Inches(1.55), Inches(12.0), Inches(slide_spec.get("table_height_inches", 3.2)))
        if slide_spec.get("insights"):
            self.add_bullets(slide, slide_spec["insights"], Inches(0.75), Inches(5.0), Inches(11.5), Inches(1.45), size=15)
        self.add_footer(slide, slide_spec.get("footer"))

    def render_chart_slide(self, slide_spec: dict[str, Any]) -> None:
        slide = self.prs.slides.add_slide(self.layout)
        self.add_bg(slide, slide_spec.get("background", "white"))
        self.add_header(slide, slide_spec["title"], slide_spec.get("subtitle"))
        chart = slide_spec["chart"]
        self.add_bar_chart(slide, chart, Inches(7.1), Inches(1.65), Inches(5.4), Inches(3.2))
        if slide_spec.get("bullets"):
            self.add_bullets(slide, slide_spec["bullets"], Inches(0.7), Inches(1.6), Inches(5.9), Inches(3.6), size=15)
        if slide_spec.get("bottom_cards"):
            cards = slide_spec["bottom_cards"]
            widths = [Inches(5.8), Inches(5.45)]
            xs = [Inches(0.75), Inches(7.05)]
            for idx, card in enumerate(cards[:2]):
                self.add_card(slide, card, xs[idx], Inches(5.05 if idx else 5.35), widths[idx], Inches(1.6 if idx else 1.3))
        self.add_footer(slide, slide_spec.get("footer"))

    def render_split_slide(self, slide_spec: dict[str, Any]) -> None:
        slide = self.prs.slides.add_slide(self.layout)
        self.add_bg(slide, slide_spec.get("background", "bg"))
        self.add_header(slide, slide_spec["title"], slide_spec.get("subtitle"))
        left = slide_spec.get("left")
        right = slide_spec.get("right")
        if left and left["kind"] == "table":
            self.add_table(slide, left["table"], Inches(0.65), Inches(1.55), Inches(7.2), Inches(left.get("height_inches", 2.55)))
        elif left and left["kind"] == "bullets":
            self.add_bullets(slide, left["items"], Inches(0.75), Inches(1.6), Inches(6.5), Inches(4.5), size=15)
        if right and right["kind"] == "bullets":
            self.add_bullets(slide, right["items"], Inches(8.1), Inches(1.7), Inches(4.2), Inches(2.8), size=15)
        if slide_spec.get("right_card"):
            self.add_card(slide, slide_spec["right_card"], Inches(8.1), Inches(4.95), Inches(4.2), Inches(1.5))
        self.add_footer(slide, slide_spec.get("footer"))

    def build(self) -> Presentation:
        for slide_spec in self.spec["slides"]:
            kind = slide_spec["kind"]
            if kind == "title":
                self.render_title_slide(slide_spec)
            elif kind == "cards":
                self.render_cards_slide(slide_spec)
            elif kind == "table":
                self.render_table_slide(slide_spec)
            elif kind == "chart":
                self.render_chart_slide(slide_spec)
            elif kind == "split":
                self.render_split_slide(slide_spec)
            else:
                raise ValueError(f"Unsupported slide kind: {kind}")
        return self.prs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a reusable EMBA-style case-analysis PPTX from JSON.")
    parser.add_argument("spec", type=Path, help="Path to deck specification JSON file.")
    parser.add_argument("output", type=Path, help="Path to output .pptx file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = load_spec(args.spec)
    builder = DeckBuilder(spec)
    builder.build()
    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    builder.prs.save(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
