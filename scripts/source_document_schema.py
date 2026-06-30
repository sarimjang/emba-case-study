#!/usr/bin/env python3
"""Shared validator for the repo-owned ``source-document/v1`` contract.

Pure stdlib (no schema-framework dependency). Provides:

- :func:`validate_source_document` — structural validation of every required
  top-level, source, page, block, and table field, returning a structured
  :class:`ValidationResult` whose errors name the offending field path.
- Facts-only enforcement: rejects reserved interpretation keys that belong to
  ``exhibit_semantics.json`` (subtotal meaning, exhibit type, row role, …),
  because ``source-document/v1`` records observed facts only (``CONTEXT.md``
  "Source Document").

This is the frozen anchor contract downstream changes (3–9) validate against.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "source-document/v1"

REQUIRED_SOURCE_FIELDS = (
    "path",
    "mime_type",
    "provider",
    "provider_version",
    "ingested_at",
    "docling_command",
)
REQUIRED_PAGE_FIELDS = ("page_number", "width", "height")
REQUIRED_BLOCK_FIELDS = (
    "id",
    "self_ref",
    "type",
    "label",
    "text",
    "page_number",
    "bbox",
    "parent_ref",
    "child_refs",
    "confidence",
)

# Reserved keys that belong to exhibit_semantics.json, never the source document.
# Their presence signals interpretation leaking into a facts-only contract.
RESERVED_INTERPRETATION_KEYS = frozenset(
    {
        "exhibit_type",
        "exhibit_semantics",
        "subtotal_meaning",
        "is_subtotal",
        "is_total",
        "row_role",
        "column_group_meaning",
        "financial_metric",
        "arithmetic_check",
        "chart_trend",
        "chart_data",
        "ranking",
        "semantic_confidence",
        "analysis_claim",
    }
)


@dataclass
class ValidationResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def fail(self, path: str, message: str) -> None:
        self.ok = False
        self.errors.append(f"{path}: {message}")


def _require(result: ValidationResult, container: Any, key: str, path: str) -> bool:
    if not isinstance(container, dict) or key not in container:
        result.fail(f"{path}.{key}" if path else key, "missing required field")
        return False
    return True


def _scan_interpretation_keys(node: Any, path: str, result: ValidationResult) -> None:
    """Walk the document and reject reserved interpretation keys anywhere."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in RESERVED_INTERPRETATION_KEYS:
                result.fail(
                    f"{path}.{key}" if path else key,
                    "interpretation field not allowed in source-document/v1 "
                    "(belongs in exhibit_semantics.json)",
                )
            _scan_interpretation_keys(value, f"{path}.{key}" if path else key, result)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _scan_interpretation_keys(item, f"{path}[{idx}]", result)


def validate_source_document(doc: Any) -> ValidationResult:
    """Validate a parsed ``source_document.json`` against ``source-document/v1``."""
    result = ValidationResult()
    if not isinstance(doc, dict):
        result.fail("", "document must be a JSON object")
        return result

    if doc.get("schema_version") != SCHEMA_VERSION:
        result.fail(
            "schema_version",
            f"must be {SCHEMA_VERSION!r}, got {doc.get('schema_version')!r}",
        )

    if _require(result, doc, "source", ""):
        for f in REQUIRED_SOURCE_FIELDS:
            _require(result, doc["source"], f, "source")

    for container in ("pages", "tables", "figures", "notes"):
        if container not in doc:
            result.fail(container, "missing required field")
        elif not isinstance(doc[container], list):
            result.fail(container, "must be a list")

    for p_idx, page in enumerate(doc.get("pages") or []):
        ppath = f"pages[{p_idx}]"
        for f in REQUIRED_PAGE_FIELDS:
            _require(result, page, f, ppath)
        for b_idx, block in enumerate((page or {}).get("blocks") or []):
            bpath = f"{ppath}.blocks[{b_idx}]"
            if not isinstance(block, dict):
                result.fail(bpath, "block must be an object")
                continue
            for f in REQUIRED_BLOCK_FIELDS:
                _require(result, block, f, bpath)

    for t_idx, table in enumerate(doc.get("tables") or []):
        tpath = f"tables[{t_idx}]"
        if not isinstance(table, dict):
            result.fail(tpath, "table must be an object")
            continue
        if table.get("page_number") is None:
            result.fail(f"{tpath}.page_number", "table has no page provenance")
        if not table.get("cells"):
            result.fail(f"{tpath}.cells", "table has no cells")

    # Facts-only constraint: no interpretation keys anywhere in the document.
    _scan_interpretation_keys(doc, "", result)
    return result


def load_and_validate(path: Path) -> ValidationResult:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        r = ValidationResult()
        r.fail(str(path), "file not found")
        return r
    except json.JSONDecodeError as exc:
        r = ValidationResult()
        r.fail(str(path), f"invalid JSON: {exc}")
        return r
    return validate_source_document(doc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a source_document.json against source-document/v1."
    )
    parser.add_argument("path", help="Path to source_document.json")
    args = parser.parse_args(argv)
    result = load_and_validate(Path(args.path).expanduser())
    if result.ok:
        print(f"valid: {args.path}")
        return 0
    print(f"invalid: {args.path}", file=sys.stderr)
    for err in result.errors:
        print(f"  {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
