#!/usr/bin/env python3
"""Exhibit Identity Registry: confidence-tiered "Exhibit N" reference resolution.

Implements the tiers from
``openspec/changes/composition-linearization-rag/design.md`` Decision 5,
evaluated in a fixed order that is a correctness precondition, not a
preference:

1. Tier A (``verified``) — the exhibit's own caption/title literally carries
   "Exhibit N".
2. Tier B (``inferred``) — a prose description bridge: near an "Exhibit N"
   occurrence, a preceding-biased window contains the exhibit's distinctive
   caption head.
3. Label-anchor (``hint``) — a bare "Exhibit N" label binds to the nearest
   exhibit object on the same page, subject to anti-binding guards (Decision
   6). Runs last because its number-conflict guard depends on tiers A/B
   having already registered their bindings.

Document-order alignment is never a resolving signal on its own (Decision 5).

Unresolved numbers become phantom records (Decision 7): ``mentioned-only``
when the number appears only in prose, or ``label-detected-object-undetected``
when a bare label names the exhibit but no object was detected, carrying the
label block's own source anchor.
"""

from __future__ import annotations

import math
import re
from typing import Any

EXHIBIT_MENTION = re.compile(r"Exhibit\s*([0-9IVXivx]+)", re.IGNORECASE)
EXHIBIT_LABEL = re.compile(r"^\s*Exhibit\s*([0-9IVXivx]+)\s*$", re.IGNORECASE)

# Tier B defaults (module-level, overridable).
WINDOW_BEFORE = 20
WINDOW_AFTER = 5
MIN_HEAD_LEN = 3
GENERIC_NOUN_STOPLIST: frozenset[str] = frozenset()
BOILERPLATE_SPLIT = re.compile(r"[之的：:]|詳細|欄位")

# Label-anchor anti-binding defaults (module-level, overridable).
SEP_RATIO = 0.6
PAGE_HEIGHT_FRACTION = 0.20
DEFAULT_PAGE_HEIGHT = 792.0


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", str(text))


def _bbox_center(bbox: Any) -> tuple[float, float] | None:
    if not (isinstance(bbox, list | tuple) and len(bbox) >= 4):
        return None
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _all_blocks(source_doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        block
        for page in source_doc.get("pages") or []
        for block in page.get("blocks") or []
    ]


def _exhibit_objects(source_doc: dict[str, Any]) -> list[dict[str, Any]]:
    return list(source_doc.get("tables") or []) + list(source_doc.get("figures") or [])


def _caption_head(
    exhibit: dict[str, Any],
    object_by_ref: dict[str, dict[str, Any]],
    block_text: dict[str, str],
    boilerplate_split: re.Pattern[str],
) -> str:
    caption = str(exhibit.get("title") or "")
    if not caption:
        for ref in exhibit.get("source_refs") or []:
            for caption_ref in object_by_ref.get(ref, {}).get("caption_refs") or []:
                caption = caption or block_text.get(caption_ref, "")
    head = boilerplate_split.split(caption)[0]
    return _normalize(head)


def resolve(
    source_doc: dict[str, Any],
    semantics: dict[str, Any],
    *,
    sep_ratio: float = SEP_RATIO,
    page_height_fraction: float = PAGE_HEIGHT_FRACTION,
    window_before: int = WINDOW_BEFORE,
    window_after: int = WINDOW_AFTER,
    min_head_len: int = MIN_HEAD_LEN,
    generic_noun_stoplist: frozenset[str] = GENERIC_NOUN_STOPLIST,
    boilerplate_split: re.Pattern[str] = BOILERPLATE_SPLIT,
) -> dict[str, Any]:
    """Resolve "Exhibit N" references to exhibits using the tiered evidence.

    Returns ``{"bindings": {number: {"exhibit_id", "tier", "object_ref"}},
    "phantoms": [{"number", "type", "source_anchor"}]}``.
    """
    blocks = _all_blocks(source_doc)
    block_text = {
        b["self_ref"]: str(b.get("text", "")) for b in blocks if b.get("self_ref")
    }
    object_by_ref = {
        o["self_ref"]: o for o in _exhibit_objects(source_doc) if o.get("self_ref")
    }
    exhibit_by_object_ref = {
        ref: exhibit
        for exhibit in semantics.get("exhibits") or []
        for ref in exhibit.get("source_refs") or []
    }
    page_height = {
        page.get("page_number"): page.get("height") or DEFAULT_PAGE_HEIGHT
        for page in source_doc.get("pages") or []
    }

    bindings: dict[str, dict[str, Any]] = {}
    object_number: dict[str, str] = {}

    def bind(number: str, exhibit: dict[str, Any], object_ref: str, tier: str) -> None:
        bindings[number] = {
            "exhibit_id": exhibit["id"],
            "tier": tier,
            "object_ref": object_ref,
        }
        object_number[object_ref] = number

    # --- Tier A: caption/title literally carries "Exhibit N" (verified). ---
    for exhibit in semantics.get("exhibits") or []:
        object_ref = next(iter(exhibit.get("source_refs") or []), None)
        if object_ref is None:
            continue
        texts = [str(exhibit.get("title") or "")]
        for caption_ref in object_by_ref.get(object_ref, {}).get("caption_refs") or []:
            texts.append(block_text.get(caption_ref, ""))
        for text in texts:
            match = EXHIBIT_MENTION.search(text)
            if match and match.group(1) not in bindings:
                bind(match.group(1), exhibit, object_ref, "verified")
                break

    # --- Tier B: prose description bridge (inferred). ---
    heads = [
        (exhibit, _caption_head(exhibit, object_by_ref, block_text, boilerplate_split))
        for exhibit in semantics.get("exhibits") or []
    ]
    heads = [
        (exhibit, head)
        for exhibit, head in heads
        if len(head) >= min_head_len and head not in generic_noun_stoplist
    ]
    for text in block_text.values():
        normalized = _normalize(text)
        for match in EXHIBIT_MENTION.finditer(normalized):
            number = match.group(1)
            if number in bindings:
                continue
            window = normalized[
                max(0, match.start() - window_before) : match.end() + window_after
            ]
            hits = {exhibit["id"]: exhibit for exhibit, head in heads if head in window}
            if len(hits) == 1:
                exhibit = next(iter(hits.values()))
                object_ref = next(iter(exhibit.get("source_refs") or []), None)
                if object_ref is not None:
                    bind(number, exhibit, object_ref, "inferred")

    # --- Label-anchor: bare "Exhibit N" label to nearest object (hint). ---
    labels: list[dict[str, Any]] = []
    for block in blocks:
        match = EXHIBIT_LABEL.match(str(block.get("text", "")))
        if match:
            labels.append({"number": match.group(1), "block": block})

    objects_by_page: dict[Any, list[dict[str, Any]]] = {}
    for obj in _exhibit_objects(source_doc):
        objects_by_page.setdefault(obj.get("page_number"), []).append(obj)

    for label in labels:
        number = label["number"]
        if number in bindings:
            continue
        block = label["block"]
        label_center = _bbox_center(block.get("bbox"))
        candidates = []
        if label_center is not None:
            for obj in objects_by_page.get(block.get("page_number"), []):
                center = _bbox_center(obj.get("bbox"))
                if center is not None:
                    candidates.append((_distance(label_center, center), obj))
        candidates.sort(key=lambda pair: pair[0])
        if not candidates:
            continue
        nearest_dist, nearest_obj = candidates[0]
        runner_up_dist = candidates[1][0] if len(candidates) > 1 else float("inf")
        cap = page_height_fraction * page_height.get(
            block.get("page_number"), DEFAULT_PAGE_HEIGHT
        )
        if nearest_dist > cap:
            continue
        existing_number = object_number.get(nearest_obj["self_ref"])
        if existing_number is not None and existing_number != number:
            continue
        if nearest_dist >= sep_ratio * runner_up_dist:
            continue
        exhibit = exhibit_by_object_ref.get(nearest_obj["self_ref"])
        if exhibit is None:
            continue
        bind(number, exhibit, nearest_obj["self_ref"], "hint")

    # --- Phantom emission for numbers with no qualifying evidence. ---
    label_by_number: dict[str, dict[str, Any]] = {}
    for label in labels:
        label_by_number.setdefault(label["number"], label["block"])

    referenced_numbers: dict[str, None] = {}
    for text in block_text.values():
        for match in EXHIBIT_MENTION.finditer(text):
            referenced_numbers.setdefault(match.group(1), None)

    phantoms: list[dict[str, Any]] = []
    for number in referenced_numbers:
        if number in bindings:
            continue
        label_block = label_by_number.get(number)
        if label_block is not None:
            phantoms.append(
                {
                    "number": number,
                    "type": "label-detected-object-undetected",
                    "source_anchor": label_block["self_ref"],
                }
            )
        else:
            phantoms.append(
                {"number": number, "type": "mentioned-only", "source_anchor": None}
            )

    return {"bindings": bindings, "phantoms": phantoms}
