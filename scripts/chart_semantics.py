#!/usr/bin/env python3
"""Chart/figure preservation semantics.

Enriches a ``chart`` exhibit by preserving the figure reference, associating a
caption as the title, and recording OCR-readable labels and source/note text as
source-anchored hints. Conservative per ``docs/adr/0002-defer-chart-digitization``:
it preserves and associates already-extracted text; it never OCRs the image,
estimates plotted values, or emits a numeric series. ``data_extraction_status``
is always ``image_preserved_only``.
"""

from __future__ import annotations

import re
from typing import Any

DATA_EXTRACTION_STATUS = "image_preserved_only"
_SOURCE_TEXT_RE = re.compile(r"^\s*(source|note)\b[:\s]", re.IGNORECASE)


def chart_exhibit_fields(
    figure: dict[str, Any], captions_by_ref: dict[str, str]
) -> dict[str, Any]:
    """Return chart-exhibit enrichment fields for a source figure.

    Never fabricates plotted values; pins ``data_extraction_status`` to
    ``image_preserved_only``.
    """
    image_ref = figure.get("self_ref")
    caption_refs = figure.get("caption_refs") or []

    title: str | None = None
    hints: list[dict[str, Any]] = []
    for ref in caption_refs:
        text = captions_by_ref.get(ref)
        if not text:
            continue
        if title is None:
            title = text
        kind = "chart_source" if _SOURCE_TEXT_RE.match(text) else "chart_label"
        # Caption-derived text is copied from observed source facts.
        hints.append(
            {
                "kind": kind,
                "value": text,
                "confidence": "observed",
                "source_refs": [ref],
            }
        )

    return {
        "image_ref": image_ref,
        "title": title,
        "semantic_hints": hints,
        "data_extraction_status": DATA_EXTRACTION_STATUS,
    }
