#!/usr/bin/env python3
"""Generate markdown from the canonical case spec."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from case_spec_utils import OutputPathError, SpecValidationError, load_spec, prepare_output_path


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_markdown(spec: dict[str, Any]) -> str:
    case = spec["case"]
    dp = spec["decision_pivot"]
    ctx = spec["company_industry_context"]
    dilemma = spec["core_dilemma"]
    evidence = spec["evidence"]
    options = spec["options"]
    recommendation = spec.get("recommendation", {})
    appendix = spec.get("appendix", {})

    parts: list[str] = []
    parts.append(f"# {case['title']}")
    if case.get("subtitle"):
        parts.append(case["subtitle"])
    if case.get("metadata"):
        parts.append("\n".join(f"`{item}`" for item in case["metadata"]))

    parts.append("## 一、導言與決策切入點")
    parts.append(f"- 決策主角：{dp['decision_owner']}")
    parts.append(f"- 核心決策：{dp['decision_question']}")
    parts.append(f"- 緊迫性：{dp['urgency']}")
    parts.append(f"- 延遲代價：{dp['delay_cost']}")
    parts.append("### 時間軸")
    parts.append(bullets(dp.get("milestones", [])))

    parts.append("## 二、公司與產業總體檢")
    parts.append("### 企業背景")
    parts.append(bullets(ctx.get("company_background", [])))
    parts.append("### 產業背景")
    parts.append(bullets(ctx.get("industry_background", [])))
    structural = ctx.get("structural_breakdown", {})
    parts.append("### 多維度拆解")
    if structural.get("market_channel"):
        parts.append("#### 市場與通路")
        parts.append(bullets(structural["market_channel"]))
    if structural.get("cost_supply_chain"):
        parts.append("#### 成本與供應鏈")
        parts.append(bullets(structural["cost_supply_chain"]))
    if structural.get("technology_organization"):
        parts.append("#### 技術與組織")
        parts.append(bullets(structural["technology_organization"]))

    parts.append("## 三、核心衝突與根本問題診斷")
    parts.append(f"- 表層問題：{dilemma['surface_problem']}")
    parts.append(f"- 根本問題：{dilemma['root_problem']}")
    parts.append("### 5 Whys")
    parts.append(bullets(dilemma.get("five_whys", [])))
    parts.append("### Trade-off")
    parts.append(bullets(dilemma.get("trade_offs", [])))
    parts.append(f"- 核心張力：{dilemma['key_tension']}")

    parts.append("## 四、數據驗證與實例支持")
    parts.append("### 關鍵數據")
    parts.append(bullets(evidence.get("quantitative_signals", [])))
    parts.append("### 內部檢查")
    parts.append(bullets(evidence.get("internal_checks", [])))
    parts.append("### 外部交叉檢查")
    parts.append(bullets(evidence.get("external_checks", [])))
    if evidence.get("open_issues"):
        parts.append("### 仍有疑點")
        parts.append(bullets(evidence["open_issues"]))

    parts.append("## 五、課堂思辨與行動決策")
    for option in options:
        parts.append(f"### {option['title']}")
        parts.append(f"- How：{option['how']}")
        parts.append(f"- Why：{option['why']}")
        parts.append(f"- Trade-off：{option['trade_off']}")

    if recommendation:
        parts.append("### 建議方案")
        parts.append(f"- 建議：{recommendation.get('recommended_option', '')}")
        parts.append(f"- 理由：{recommendation.get('reason', '')}")
        if recommendation.get("conditions"):
            parts.append("- 成立前提：")
            parts.append(bullets(recommendation["conditions"]))

    parts.append("## 附錄與參考資料")
    if appendix.get("references"):
        parts.append("### 參考來源")
        parts.append(bullets(appendix["references"]))
    if appendix.get("assumptions"):
        parts.append("### 關鍵假設")
        parts.append(bullets(appendix["assumptions"]))
    if appendix.get("discussion_questions"):
        parts.append("### 課堂討論題")
        parts.append(bullets(appendix["discussion_questions"]))
    if case.get("source_notes"):
        parts.append("### Source Notes")
        parts.append(bullets(case["source_notes"]))

    return "\n\n".join(part for part in parts if part.strip()) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate markdown from the canonical case spec.")
    parser.add_argument(
        "--allow-outside-workspace",
        action="store_true",
        help="Allow writing outside the current workspace or spec directory.",
    )
    parser.add_argument("spec", type=Path, help="Path to canonical case spec JSON.")
    parser.add_argument("output", type=Path, help="Path to output markdown file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        spec = load_spec(args.spec)
        output_path = prepare_output_path(
            args.output,
            allowed_roots=[Path.cwd(), args.spec.expanduser().resolve().parent],
            expected_suffix=".md",
            allow_outside_workspace=args.allow_outside_workspace,
        )
    except (OutputPathError, SpecValidationError) as exc:
        raise SystemExit(f"Error: {exc}") from exc

    output_path.write_text(build_markdown(spec), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
