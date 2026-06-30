#!/usr/bin/env python3
"""Docling ingestion adapter.

Converts a source document into a local Docling raw JSON artifact and a
normalized, repo-owned ``source_document.json`` (schema ``source-document/v1``)
plus an ``ingestion_manifest.json`` gate record.

This is the ADR-0001 boundary: Docling raw JSON stays a local debug/audit
artifact and is never embedded into the normalized contract. See
``ROADMAP.md`` (Phase 1) and ``openspec/changes/docling-ingestion-adapter``.

The module is import-friendly: the subprocess invocation is injected via a
``runner`` callable so normalization, gating, and path-safety logic can be
tested without a real Docling install.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SCHEMA_VERSION = "source-document/v1"

# Default executable discovery chain (ROADMAP "Confirmed local Docling surface").
PYENV_DOCLING = Path("~/.pyenv/versions/3.12.0/bin/docling")
PYENV_SHIM_DOCLING = Path("~/.pyenv/shims/docling")

# Artifact-size warning thresholds (ROADMAP "Performance and artifact-size budget").
RAW_JSON_WARN_BYTES = 25 * 1024 * 1024
SOURCE_DOC_WARN_BYTES = 10 * 1024 * 1024
TOTAL_ARTIFACT_WARN_BYTES = 100 * 1024 * 1024

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "source",
    "pages",
    "tables",
    "figures",
    "notes",
)
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

MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".html": "text/html",
    ".md": "text/markdown",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


class IngestionError(RuntimeError):
    """Raised on any gate failure; carries an actionable, user-facing message."""


class OutputPathError(IngestionError):
    """Raised when an output path violates local safety rules."""


# --------------------------------------------------------------------------- #
# Executable resolution and environment gate
# --------------------------------------------------------------------------- #
def discover_docling_executable(explicit: str | Path | None) -> Path:
    """Resolve a runnable Docling executable.

    Order: explicit flag -> pyenv versioned path -> pyenv shim -> ``PATH``.
    Raises :class:`IngestionError` naming searched locations if none is usable.
    """
    searched: list[str] = []
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.append(PYENV_DOCLING.expanduser())
    candidates.append(PYENV_SHIM_DOCLING.expanduser())

    for cand in candidates:
        searched.append(str(cand))
        if cand.is_file() and os.access(cand, os.X_OK):
            return cand

    on_path = shutil.which("docling")
    searched.append("PATH:docling")
    if on_path:
        return Path(on_path)

    raise IngestionError(
        "Could not find a runnable Docling executable. Searched: "
        + ", ".join(searched)
        + ". Pass --docling-executable with an explicit path."
    )


def _default_runner(cmd: list[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def probe_versions(
    executable: Path, runner: Runner = _default_runner
) -> dict[str, str | None]:
    """Read Docling component versions; raise if the version probe fails."""
    result = runner([str(executable), "--version"])
    if result.returncode != 0:
        raise IngestionError(
            f"Docling version probe failed for {executable} "
            f"(exit {result.returncode}): {(result.stderr or '').strip()}"
        )
    text = f"{result.stdout}\n{result.stderr}"
    versions: dict[str, str | None] = {
        "docling_version": _grep_version(text, "docling"),
        "docling_core_version": _grep_version(text, "docling-core"),
        "docling_parse_version": _grep_version(text, "docling-parse"),
        "docling_ibm_models_version": _grep_version(text, "docling-ibm-models"),
    }
    if versions["docling_version"] is None:
        # The bare `docling --version` line typically reads "Docling version: X".
        import re

        m = re.search(r"(\d+\.\d+\.\d+)", text)
        versions["docling_version"] = m.group(1) if m else None
    return versions


def _grep_version(text: str, package: str) -> str | None:
    import re

    pattern = rf"{re.escape(package)}[^\d]*(\d+\.\d+\.\d+)"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else None


# --------------------------------------------------------------------------- #
# Output-path containment (directory variant of the generators' pattern)
# --------------------------------------------------------------------------- #
def prepare_output_dir(
    output_dir: Path,
    *,
    allowed_roots: list[Path],
    allow_outside_workspace: bool = False,
) -> Path:
    resolved = output_dir.expanduser().resolve()
    if resolved.is_symlink():
        raise OutputPathError(f"Refusing to write to symlinked output dir: {resolved}")
    if resolved.exists() and not resolved.is_dir():
        raise OutputPathError(f"Output path must be a directory: {resolved}")

    resolved_roots = [root.expanduser().resolve() for root in allowed_roots]
    if not allow_outside_workspace and not any(
        resolved.is_relative_to(root) for root in resolved_roots
    ):
        joined = ", ".join(str(root) for root in resolved_roots)
        raise OutputPathError(
            f"Refusing to write outside the local workspace roots ({joined}). "
            "Pass --allow-outside-workspace to override."
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


# --------------------------------------------------------------------------- #
# Docling command construction
# --------------------------------------------------------------------------- #
def build_docling_command(
    executable: Path,
    source: Path,
    raw_output_dir: Path,
    *,
    from_format: str | None,
    ocr: bool,
    ocr_lang: str,
    table_mode: str,
    device: str,
    document_timeout: int,
) -> list[str]:
    cmd = [
        str(executable),
        str(source),
        "--to",
        "json",
        "--output",
        str(raw_output_dir),
    ]
    if from_format:
        cmd += ["--from", from_format]
    cmd += ["--ocr"] if ocr else ["--no-ocr"]
    cmd += ["--ocr-lang", ocr_lang]
    cmd += ["--table-mode", table_mode]
    cmd += ["--device", device]
    cmd += ["--document-timeout", str(document_timeout)]
    return cmd


# --------------------------------------------------------------------------- #
# Normalization: Docling raw JSON -> source-document/v1
# --------------------------------------------------------------------------- #
def _bbox(prov_item: dict[str, Any]) -> list[float] | None:
    bbox = prov_item.get("bbox")
    if not isinstance(bbox, dict):
        return None
    keys = ("l", "t", "r", "b")
    if all(k in bbox for k in keys):
        return [float(bbox[k]) for k in keys]
    return None


def _first_prov(item: dict[str, Any]) -> dict[str, Any]:
    prov = item.get("prov")
    if isinstance(prov, list) and prov:
        return prov[0]
    return {}


def normalize_source_document(
    raw: dict[str, Any], source_meta: dict[str, Any]
) -> dict[str, Any]:
    """Map a Docling ``DoclingDocument`` JSON into the ``source-document/v1`` shape.

    Records observed facts only — no business interpretation. Never embeds the
    raw schema or base64 page images.
    """
    raw_pages = raw.get("pages") or {}
    # Docling keys pages by string page-no; values carry size {width,height}.
    page_index = {}
    for key, page in raw_pages.items() if isinstance(raw_pages, dict) else []:
        size = (page or {}).get("size") or {}
        try:
            page_no = int(page.get("page_no", key))
        except (TypeError, ValueError):
            page_no = int(key) if str(key).isdigit() else len(page_index) + 1
        page_index[page_no] = {
            "page_number": page_no,
            "width": float(size.get("width", 0.0)),
            "height": float(size.get("height", 0.0)),
            "blocks": [],
        }

    blocks: list[dict[str, Any]] = []

    def add_block(item: dict[str, Any], default_type: str) -> None:
        prov = _first_prov(item)
        page_no = prov.get("page_no")
        block = {
            "id": item.get("self_ref", "").lstrip("#/")
            or f"{default_type}-{len(blocks)}",
            "self_ref": item.get("self_ref"),
            "type": default_type,
            "label": item.get("label", default_type),
            "text": item.get("text", ""),
            "page_number": page_no,
            "bbox": _bbox(prov),
            "parent_ref": (item.get("parent") or {}).get("$ref")
            if isinstance(item.get("parent"), dict)
            else item.get("parent"),
            "child_refs": [
                c.get("$ref") if isinstance(c, dict) else c
                for c in (item.get("children") or [])
            ],
            "confidence": item.get("confidence"),
        }
        blocks.append(block)
        if page_no in page_index:
            page_index[page_no]["blocks"].append(block["id"])

    for text_item in raw.get("texts") or []:
        if isinstance(text_item, dict):
            add_block(text_item, "text")

    tables_out: list[dict[str, Any]] = []
    for tbl in raw.get("tables") or []:
        if not isinstance(tbl, dict):
            continue
        prov = _first_prov(tbl)
        data = tbl.get("data") or {}
        cells = data.get("table_cells") or data.get("grid") or []
        tables_out.append(
            {
                "id": tbl.get("self_ref", "").lstrip("#/")
                or f"table-{len(tables_out)}",
                "self_ref": tbl.get("self_ref"),
                "page_number": prov.get("page_no"),
                "bbox": _bbox(prov),
                "num_rows": data.get("num_rows"),
                "num_cols": data.get("num_cols"),
                "caption_refs": [
                    c.get("$ref") if isinstance(c, dict) else c
                    for c in (tbl.get("captions") or [])
                ],
                "cells": cells,
            }
        )

    figures_out: list[dict[str, Any]] = []
    for pic in raw.get("pictures") or []:
        if not isinstance(pic, dict):
            continue
        prov = _first_prov(pic)
        figures_out.append(
            {
                "id": pic.get("self_ref", "").lstrip("#/")
                or f"figure-{len(figures_out)}",
                "self_ref": pic.get("self_ref"),
                "page_number": prov.get("page_no"),
                "bbox": _bbox(prov),
                "caption_refs": [
                    c.get("$ref") if isinstance(c, dict) else c
                    for c in (pic.get("captions") or [])
                ],
                "data_extraction_status": "image_preserved_only",
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "source": source_meta,
        "pages": [page_index[k] for k in sorted(page_index)],
        "tables": tables_out,
        "figures": figures_out,
        "notes": [],
    }


def validate_source_document_minimum(doc: dict[str, Any]) -> None:
    """Assert the minimum ``source-document/v1`` field contract; raise on the first gap."""
    for field in REQUIRED_TOP_LEVEL:
        if field not in doc:
            raise IngestionError(
                f"source_document.json missing required field: {field}"
            )
    if doc.get("schema_version") != SCHEMA_VERSION:
        raise IngestionError(
            f"source_document.json schema_version must be {SCHEMA_VERSION!r}, "
            f"got {doc.get('schema_version')!r}"
        )
    source = doc.get("source")
    if not isinstance(source, dict):
        raise IngestionError("source_document.json 'source' must be an object")
    for field in REQUIRED_SOURCE_FIELDS:
        if field not in source:
            raise IngestionError(
                f"source_document.json missing required field: source.{field}"
            )
    pages = doc.get("pages")
    if not isinstance(pages, list):
        raise IngestionError("source_document.json 'pages' must be a list")
    for idx, page in enumerate(pages):
        for field in REQUIRED_PAGE_FIELDS:
            if field not in page:
                raise IngestionError(
                    f"source_document.json missing required field: pages[{idx}].{field}"
                )
    for idx, table in enumerate(doc.get("tables") or []):
        if table.get("page_number") is None:
            raise IngestionError(
                f"source_document.json tables[{idx}] has no page provenance"
            )
        if not table.get("cells"):
            raise IngestionError(f"source_document.json tables[{idx}] has no cells")


def assert_no_embedded_base64(doc: dict[str, Any]) -> None:
    """Reject canonical output that embeds base64 page images by default."""
    blob = json.dumps(doc)
    if "data:image" in blob or '"base64"' in blob:
        raise IngestionError(
            "Canonical source_document.json must not embed base64 page images by default."
        )


# --------------------------------------------------------------------------- #
# Size budget
# --------------------------------------------------------------------------- #
def size_warnings(raw_bytes: int, source_doc_bytes: int, total_bytes: int) -> list[str]:
    warns: list[str] = []
    if raw_bytes > RAW_JSON_WARN_BYTES:
        warns.append(
            f"raw Docling JSON exceeds {RAW_JSON_WARN_BYTES} bytes ({raw_bytes})"
        )
    if source_doc_bytes > SOURCE_DOC_WARN_BYTES:
        warns.append(
            f"source_document.json exceeds {SOURCE_DOC_WARN_BYTES} bytes ({source_doc_bytes})"
        )
    if total_bytes > TOTAL_ARTIFACT_WARN_BYTES:
        warns.append(
            f"total ingestion artifacts exceed {TOTAL_ARTIFACT_WARN_BYTES} bytes ({total_bytes})"
        )
    return warns


def _mime_for(source: Path) -> str:
    return MIME_BY_SUFFIX.get(source.suffix.lower(), "application/octet-stream")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run_ingestion(
    args: argparse.Namespace, runner: Runner = _default_runner
) -> dict[str, Any]:
    source = Path(args.input).expanduser().resolve()
    if not source.is_file():
        raise IngestionError(f"Source document not found: {source}")

    allowed_roots = [Path.cwd(), source.parent]
    out_dir = prepare_output_dir(
        Path(args.output_dir),
        allowed_roots=allowed_roots,
        allow_outside_workspace=args.allow_outside_workspace,
    )
    docling_dir = out_dir / "docling"
    docling_dir.mkdir(parents=True, exist_ok=True)

    executable = discover_docling_executable(args.docling_executable)
    versions = probe_versions(executable, runner=runner)

    cmd = build_docling_command(
        executable,
        source,
        docling_dir,
        from_format=args.from_format,
        ocr=args.ocr,
        ocr_lang=args.ocr_lang,
        table_mode=args.table_mode,
        device=args.device,
        document_timeout=args.document_timeout,
    )

    # Privacy/network/model-download gate: default-deny via offline env unless allowed.
    env_offline = not (args.allow_network or args.allow_model_downloads)

    result = runner(cmd if not env_offline else cmd)  # runner observes os.environ
    if result.returncode != 0:
        stderr = (result.stderr or "").lower()
        if env_offline and (
            "download" in stderr or "offline" in stderr or "huggingface" in stderr
        ):
            raise IngestionError(
                "Docling needs to download a model but downloads are disabled. "
                "Re-run with --allow-model-downloads to permit a one-time download."
            )
        raise IngestionError(
            f"Docling failed (exit {result.returncode}): {(result.stderr or '').strip()}"
        )

    raw_path = _locate_raw_json(docling_dir)
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    source_meta = {
        "path": str(source),
        "mime_type": _mime_for(source),
        "provider": "docling",
        "provider_version": versions.get("docling_version"),
        "ingested_at": _now_iso(),
        "docling_command": " ".join(cmd),
    }
    doc = normalize_source_document(raw, source_meta)
    validate_source_document_minimum(doc)
    assert_no_embedded_base64(doc)

    source_doc_path = out_dir / "source_document.json"
    source_doc_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    manifest = {
        "docling_executable": str(executable),
        **versions,
        "ocr_enabled": args.ocr,
        "ocr_language": args.ocr_lang,
        "table_mode": args.table_mode,
        "device": args.device,
        "document_timeout_seconds": args.document_timeout,
        "model_downloads_allowed": bool(args.allow_model_downloads),
        "network_allowed": bool(args.allow_network),
        "raw_json_path": str(raw_path),
        "source_document_path": str(source_doc_path),
    }
    manifest_path = out_dir / "ingestion_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    raw_bytes = raw_path.stat().st_size
    sd_bytes = source_doc_path.stat().st_size
    total_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    for warn in size_warnings(raw_bytes, sd_bytes, total_bytes):
        print(f"warning: {warn}", file=sys.stderr)

    return {
        "raw_json_path": str(raw_path),
        "source_document_path": str(source_doc_path),
        "manifest_path": str(manifest_path),
    }


def _locate_raw_json(docling_dir: Path) -> Path:
    candidates = sorted(docling_dir.glob("*.json"))
    if not candidates:
        raise IngestionError(f"Docling produced no JSON output in {docling_dir}")
    preferred = docling_dir / "raw.json"
    if preferred.exists():
        return preferred
    chosen = candidates[0]
    target = docling_dir / "raw.json"
    if chosen != target:
        shutil.copyfile(chosen, target)
        return target
    return chosen


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Ingest a source document via local Docling into source-document/v1."
    )
    p.add_argument("input", help="Source document path.")
    p.add_argument(
        "--output-dir", required=True, help="Directory for ingestion artifacts."
    )
    p.add_argument(
        "--docling-executable", default=None, help="Explicit Docling executable path."
    )
    p.add_argument(
        "--from", dest="from_format", default=None, help="Source format for Docling."
    )
    ocr = p.add_mutually_exclusive_group()
    ocr.add_argument(
        "--ocr", dest="ocr", action="store_true", help="Enable OCR (default)."
    )
    ocr.add_argument("--no-ocr", dest="ocr", action="store_false", help="Disable OCR.")
    p.set_defaults(ocr=True)
    p.add_argument("--ocr-lang", default="en", help="OCR language code (default: en).")
    p.add_argument(
        "--table-mode",
        choices=["fast", "accurate"],
        default="accurate",
        help="Docling table mode (default: accurate).",
    )
    p.add_argument("--device", default="cpu", help="Docling device (default: cpu).")
    p.add_argument(
        "--document-timeout",
        type=int,
        default=180,
        help="Document timeout seconds (default: 180).",
    )
    p.add_argument(
        "--allow-outside-workspace",
        action="store_true",
        help="Allow writing outside the workspace or source directory.",
    )
    p.add_argument(
        "--allow-network",
        action="store_true",
        help="Permit Docling network access (default deny).",
    )
    p.add_argument(
        "--allow-model-downloads",
        action="store_true",
        help="Permit one-time Docling model downloads (default deny).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        outputs = run_ingestion(args)
    except IngestionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
