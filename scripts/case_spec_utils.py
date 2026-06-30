#!/usr/bin/env python3
"""Shared validation and path-safety helpers for case spec generators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MAX_SPEC_BYTES = 5 * 1024 * 1024


class SpecValidationError(ValueError):
    """Raised when a case spec is missing required structure."""


class OutputPathError(ValueError):
    """Raised when an output path violates local safety rules."""


def _expect_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SpecValidationError(f"{label} must be an object.")
    return value


def _expect_list_of_str(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SpecValidationError(f"{label} must be a list of strings.")
    return value


def _expect_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecValidationError(f"{label} must be a non-empty string.")
    return value


def _validate_chart_data(chart_data: Any) -> None:
    chart = _expect_mapping(chart_data, "evidence.chart_data")
    labels = _expect_list_of_str(chart.get("labels"), "evidence.chart_data.labels")
    values = chart.get("values")
    if not isinstance(values, list) or not values:
        raise SpecValidationError("evidence.chart_data.values must be a non-empty list.")
    if len(labels) != len(values):
        raise SpecValidationError(
            "evidence.chart_data.labels and evidence.chart_data.values must have the same length."
        )
    if not all(isinstance(value, int | float) for value in values):
        raise SpecValidationError(
            "evidence.chart_data.values must contain only numbers."
        )
    if "unit" in chart and chart["unit"] is not None and not isinstance(chart["unit"], str):
        raise SpecValidationError("evidence.chart_data.unit must be a string when provided.")
    if "title" in chart and chart["title"] is not None and not isinstance(chart["title"], str):
        raise SpecValidationError("evidence.chart_data.title must be a string when provided.")


def validate_spec(spec: Any) -> dict[str, Any]:
    root = _expect_mapping(spec, "case spec")

    case = _expect_mapping(root.get("case"), "case")
    _expect_str(case.get("title"), "case.title")
    if "subtitle" in case and case["subtitle"] is not None and not isinstance(case["subtitle"], str):
        raise SpecValidationError("case.subtitle must be a string when provided.")
    if "metadata" in case and case["metadata"] is not None:
        _expect_list_of_str(case["metadata"], "case.metadata")
    if "source_notes" in case and case["source_notes"] is not None:
        _expect_list_of_str(case["source_notes"], "case.source_notes")

    dp = _expect_mapping(root.get("decision_pivot"), "decision_pivot")
    _expect_str(dp.get("decision_owner"), "decision_pivot.decision_owner")
    _expect_str(dp.get("decision_question"), "decision_pivot.decision_question")
    _expect_str(dp.get("urgency"), "decision_pivot.urgency")
    _expect_str(dp.get("delay_cost"), "decision_pivot.delay_cost")
    _expect_list_of_str(dp.get("milestones", []), "decision_pivot.milestones")

    ctx = _expect_mapping(root.get("company_industry_context"), "company_industry_context")
    _expect_list_of_str(
        ctx.get("company_background", []), "company_industry_context.company_background"
    )
    _expect_list_of_str(
        ctx.get("industry_background", []), "company_industry_context.industry_background"
    )
    structural = _expect_mapping(
        ctx.get("structural_breakdown", {}), "company_industry_context.structural_breakdown"
    )
    for key in ("market_channel", "cost_supply_chain", "technology_organization"):
        if key in structural and structural[key] is not None:
            _expect_list_of_str(
                structural[key],
                f"company_industry_context.structural_breakdown.{key}",
            )

    dilemma = _expect_mapping(root.get("core_dilemma"), "core_dilemma")
    _expect_str(dilemma.get("surface_problem"), "core_dilemma.surface_problem")
    _expect_str(dilemma.get("root_problem"), "core_dilemma.root_problem")
    _expect_str(dilemma.get("key_tension"), "core_dilemma.key_tension")
    _expect_list_of_str(dilemma.get("five_whys", []), "core_dilemma.five_whys")
    _expect_list_of_str(dilemma.get("trade_offs", []), "core_dilemma.trade_offs")

    evidence = _expect_mapping(root.get("evidence"), "evidence")
    _expect_list_of_str(evidence.get("quantitative_signals", []), "evidence.quantitative_signals")
    _expect_list_of_str(evidence.get("internal_checks", []), "evidence.internal_checks")
    _expect_list_of_str(evidence.get("external_checks", []), "evidence.external_checks")
    if "open_issues" in evidence and evidence["open_issues"] is not None:
        _expect_list_of_str(evidence["open_issues"], "evidence.open_issues")
    if evidence.get("chart_data") is not None:
        _validate_chart_data(evidence["chart_data"])

    options = root.get("options")
    if not isinstance(options, list) or not options:
        raise SpecValidationError("options must be a non-empty list.")
    for idx, option in enumerate(options):
        opt = _expect_mapping(option, f"options[{idx}]")
        for key in ("title", "how", "why", "trade_off"):
            _expect_str(opt.get(key), f"options[{idx}].{key}")

    recommendation = root.get("recommendation")
    if recommendation is not None:
        rec = _expect_mapping(recommendation, "recommendation")
        for key in ("recommended_option", "reason"):
            if key in rec and rec[key] is not None:
                _expect_str(rec[key], f"recommendation.{key}")
        if "conditions" in rec and rec["conditions"] is not None:
            _expect_list_of_str(rec["conditions"], "recommendation.conditions")

    appendix = root.get("appendix")
    if appendix is not None:
        app = _expect_mapping(appendix, "appendix")
        for key in ("references", "assumptions", "discussion_questions"):
            if key in app and app[key] is not None:
                _expect_list_of_str(app[key], f"appendix.{key}")

    return root


def load_spec(path: Path) -> dict[str, Any]:
    resolved_path = path.expanduser().resolve()
    if not resolved_path.is_file():
        raise SpecValidationError(f"Spec file not found: {resolved_path}")
    if resolved_path.stat().st_size > MAX_SPEC_BYTES:
        raise SpecValidationError(
            f"Spec file is too large: {resolved_path} exceeds {MAX_SPEC_BYTES} bytes."
        )
    with resolved_path.open("r", encoding="utf-8") as f:
        return validate_spec(json.load(f))


def prepare_output_path(
    output: Path,
    *,
    allowed_roots: list[Path],
    expected_suffix: str,
    allow_outside_workspace: bool = False,
) -> Path:
    resolved_output = output.expanduser().resolve()
    if resolved_output.suffix.lower() != expected_suffix:
        raise OutputPathError(
            f"Output file must use the {expected_suffix} extension: {resolved_output}"
        )
    if resolved_output.exists() and not resolved_output.is_file():
        raise OutputPathError(f"Output path must be a regular file: {resolved_output}")
    if resolved_output.is_symlink():
        raise OutputPathError(f"Refusing to write to symlinked output: {resolved_output}")

    resolved_roots = [root.expanduser().resolve() for root in allowed_roots]
    if not allow_outside_workspace and not any(
        resolved_output.is_relative_to(root) for root in resolved_roots
    ):
        joined_roots = ", ".join(str(root) for root in resolved_roots)
        raise OutputPathError(
            f"Refusing to write outside the local workspace roots ({joined_roots}). "
            "Pass --allow-outside-workspace to override."
        )

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    return resolved_output
