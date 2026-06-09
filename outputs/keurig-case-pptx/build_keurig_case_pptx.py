#!/usr/bin/env python3
"""Build the Keurig case deck by first writing a structured spec, then calling the generic PPTX generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "outputs" / "keurig-case-pptx"
SPEC_PATH = OUTPUT_DIR / "keurig-at-home-case-analysis.spec.json"
PPTX_PATH = OUTPUT_DIR / "keurig-at-home-case-analysis.pptx"
GENERATOR = ROOT / "scripts" / "generate_case_pptx.py"


SPEC = {
    "deck": {
        "title": "Keurig at Home 個案分析",
        "default_footer": "來源：Keurig case OCR + exhibit cross-check",
    },
    "slides": [
        {
            "kind": "title",
            "title": "Keurig at Home 個案分析",
            "subtitle_lines": [
                "核心問題：single K-Cup 還是 two-K-Cup？B100 與家用咖啡包應如何定價？",
                "分析基礎：掃描 PDF OCR + 個案原文展品交叉整理",
            ],
            "hero_cards": [
                {
                    "title": "決策時點",
                    "bullets": ["2003/02，距家用上市不到 6 個月", "GMCR 當天要求重審雙包裝策略"],
                    "accent": "blue",
                },
                {
                    "title": "真正張力",
                    "bullets": ["速度 vs 通路控制", "硬體滲透 vs 現金流承壓"],
                    "accent": "teal",
                },
                {
                    "title": "建議主張",
                    "bullets": ["傾向 single K-Cup", "B100 建議以 $199 促進裝機"],
                    "accent": "gold",
                },
            ],
            "footer": "來源：PDF p.1-2, p.10-11, OCR 整理",
        },
        {
            "kind": "cards",
            "title": "1. 導言與決策切入點",
            "subtitle": "主角、時間壓力與為何不能再拖",
            "cards": [
                {
                    "title": "決策主角",
                    "bullets": [
                        "CEO Nick Lazaris 在與 GMCR 會後，必須向管理團隊與董事會定案。",
                        "不只要決定包裝策略，也要同步處理 B100 定價與上市節奏。",
                    ],
                    "accent": "blue",
                },
                {
                    "title": "時間軸",
                    "bullets": [
                        "1998：B2000 在 OCS 上市，建立單杯沖泡基礎。",
                        "2002：為家庭市場籌資，GMCR 持股升至 42%。",
                        "2003/02：距 9 月上市不到 6 個月，競爭者將進場。",
                    ],
                    "accent": "teal",
                },
                {
                    "title": "延遲代價",
                    "bullets": [
                        "若重做 two-K-Cup 方案，上市可能延誤。",
                        "若過度簡化，又可能傷到 KAD 與既有 OCS 收益池。",
                    ],
                    "accent": "red",
                },
            ],
            "footer": "來源：PDF p.1-3, p.9-11, p.13-14",
        },
        {
            "kind": "cards",
            "title": "2. 公司與產業總體檢",
            "subtitle": "Keurig 的優勢不在零售貨架，而在封閉系統與夥伴網路",
            "background": "white",
            "card_height_inches": 4.85,
            "cards": [
                {
                    "title": "公司基礎",
                    "bullets": [
                        "1992 成立，主打單杯沖泡科技與專利包材。",
                        "OCS 成功靠的是『設備 + 耗材 + 多品牌烘焙夥伴』組合。",
                    ],
                    "accent": "blue",
                },
                {
                    "title": "市場機會",
                    "bullets": [
                        "OCS 市場約 $34.6 億。",
                        "家庭零售咖啡市場約 $185 億；其中家庭消費約 $69 億。",
                        "高品質咖啡消費正被 Starbucks 等教育起來。",
                    ],
                    "accent": "teal",
                },
                {
                    "title": "競爭與模式",
                    "bullets": [
                        "烘焙商每賣 1 顆 K-Cup，Keurig 抽約 $0.04 權利金。",
                        "Melitta/Salton、Senseo、P&G 都可能切入。",
                    ],
                    "accent": "gold",
                },
            ],
            "footer": "來源：PDF p.2-8, Exhibit 9",
        },
        {
            "kind": "table",
            "title": "3. 核心衝突與根本問題",
            "subtitle": "這不是產品小改版，而是平台治理與通路權力分配",
            "table": {
                "headers": ["面向", "採用 single K-Cup", "採用 two-K-Cup"],
                "rows": [
                    ["上市速度", "較快；降低 SKU 與教育負擔", "較慢；需處理雙包裝生產與教育"],
                    ["通路控制", "較弱；可能侵蝕 KAD 關係", "較強；可分離家用與商用價格"],
                    ["供應鏈複雜度", "較低", "較高；GMCR 擔心庫存與倉儲翻倍"],
                ],
                "accent": "navy",
            },
            "insights": [
                "表層問題：家用市場到底要不要用專屬 Keurig-Cup？",
                "深層問題：Keurig 想同時要『消費品速度』與『封閉生態控制力』。",
                "真正 trade-off：短期卡位速度 vs 長期通路秩序與價格權。",
            ],
            "footer": "來源：PDF p.9-10, p.12, p.24",
        },
        {
            "kind": "chart",
            "title": "4. 數據驗證：消費者接受度與定價線索",
            "subtitle": "家用機價格敏感，但咖啡包願付能力並不弱",
            "background": "white",
            "chart": {
                "categories": ["$0.25", "$0.30", "$0.35", "$0.40", "$0.45", "$0.50", "$0.55"],
                "values": [97.8, 87.3, 79.3, 69.5, 60.0, 53.5, 43.8],
                "series_name": "累積願付比例",
                "accent": "teal",
            },
            "bullets": [
                "44% 受訪者願為一杯好咖啡支付 $0.55。",
                "對系統有興趣者中，超過 30% 願為 K-Cup 支付至少 $0.50。",
                "家庭試用顯示：家用機可接受帶約落在 $129-$199；超過 $200 容易被視為奢侈品。",
                "測試中，K-Cup 以 $0.50 零售並未成為主要阻礙。",
            ],
            "bottom_cards": [
                {"title": "解讀", "bullets": ["咖啡包可支撐相對高單價；真正價格阻力主要集中在 B100 入手價。"], "accent": "gold"},
                {"title": "展品依據", "bullets": ["Exhibit 7A / 7B / 7C，與中文翻譯 p.7 對照。"], "accent": "blue"},
            ],
            "footer": "來源：PDF p.7, Exhibit 6-7, p.28",
        },
        {
            "kind": "split",
            "title": "5. 數據驗證：B100 單機 economics",
            "subtitle": "199 美元最有吸引力，但短期會壓現金流",
            "background": "bg",
            "left": {
                "kind": "table",
                "height_inches": 2.55,
                "table": {
                    "headers": ["價格點", "對消費者吸引力", "對單機毛利", "策略含義"],
                    "rows": [
                        ["$199", "最高", "若成本 $220，單機約 -$21", "快速裝機，但需靠後續 K-Cup royalty 回收"],
                        ["$249", "中等", "有較健康毛利", "在成長與現金之間折衷"],
                        ["$299", "最低", "毛利較安全", "恐拖慢採用，錯失先行者優勢"],
                    ],
                    "accent": "blue",
                },
            },
            "right": {
                "kind": "bullets",
                "items": [
                    "最新製造成本估計約 $220，工程努力目標是壓到 $200。",
                    "公司明示：已無法回到原本想要的 $149 價位。",
                    "若高定價之後再降價，競爭壓力可能不給 Keurig 修正時間。",
                ],
            },
            "right_card": {
                "title": "關鍵判讀",
                "bullets": ["B100 應被視為帶動耗材與生態系的裝機工具，而非單靠硬體獲利。"],
                "accent": "red",
            },
            "footer": "來源：PDF p.10-11, p.23",
        },
        {
            "kind": "cards",
            "title": "6. 建議方案",
            "subtitle": "以速度與系統裝機為先，但要用配套保護通路",
            "background": "white",
            "cards": [
                {
                    "title": "建議一：採 single K-Cup",
                    "bullets": [
                        "先取消家用專屬 Keurig-Cup，避免複雜度與上市延誤。",
                        "減少 GMCR 阻力，避免寫掉新 tooling 與包材計畫。",
                    ],
                    "accent": "teal",
                },
                {
                    "title": "建議二：B100 定價 $199",
                    "bullets": [
                        "接受短期硬體損失，換取裝機與先行者位置。",
                        "回收邏輯放在後續耗材與口碑擴散。",
                    ],
                    "accent": "gold",
                },
                {
                    "title": "建議三：K-Cup 約 $0.50",
                    "bullets": [
                        "與研究顯示的願付價格一致。",
                        "保留精品咖啡定位，不跟低價 pod 對手正面比價。",
                    ],
                    "accent": "blue",
                },
            ],
            "footer": "結論屬課堂立場建議，非個案唯一正解",
        },
        {
            "kind": "table",
            "title": "7. Trade-off 與執行風險",
            "subtitle": "推薦方案可行，但不等於沒有代價",
            "table_height_inches": 3.3,
            "table": {
                "headers": ["風險", "若發生的後果", "對策"],
                "rows": [
                    ["KAD 反彈", "擔心直銷侵蝕 OCS", "延續 POS referral、保留每包 annuity 與 lead 回饋"],
                    ["GMCR / 烘焙商壓力", "擔心市場節奏或價格管理", "以單一包裝換上市速度，降低生產複雜度"],
                    ["硬體虧損拉大", "現金流承壓", "嚴控 B100 成本壓至 $200；聚焦高頻咖啡用戶"],
                    ["競爭者低價進攻", "削弱高價定位", "強化精品咖啡、口感一致性與 30 秒便利性"],
                ],
                "accent": "navy",
            },
            "insights": [
                "這個個案最關鍵的管理課題：平台型商業模式在新通路擴張時，應先保速度還是先保秩序？",
                "若課堂要延伸討論，可追問：Keurig 是賣咖啡機，還是在治理單杯咖啡生態系？",
            ],
            "footer": "來源：PDF p.9-12, p.24",
        },
    ],
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_PATH.write_text(json.dumps(SPEC, ensure_ascii=False, indent=2), encoding="utf-8")
    cmd = [sys.executable, str(GENERATOR), str(SPEC_PATH), str(PPTX_PATH)]
    subprocess.run(cmd, check=True)
    print(PPTX_PATH)


if __name__ == "__main__":
    main()
