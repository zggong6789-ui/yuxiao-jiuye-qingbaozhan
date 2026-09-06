#!/usr/bin/env python3
"""从高校来源表选择当天优先巡检的官方来源；不访问网络、不修改正式数据。"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = PROJECT_ROOT / "data" / "高校来源表.csv"
RULE_FILE = PROJECT_ROOT / "config" / "巡检规则.json"
OUTPUT_DIR = PROJECT_ROOT / "workspace" / "candidates"

OUTPUT_HEADER = [
    "来源编号",
    "学校名称",
    "城市",
    "来源名称",
    "来源类型",
    "来源链接",
    "优先级",
    "建议查看频率",
    "最后检查日期",
    "主要关注内容",
    "选择原因",
    "今日排序",
]

PRIORITY_PATTERN = re.compile(r"优先级\s*(P[0-2])", re.IGNORECASE)
FREQUENCY_PATTERN = re.compile(r"每周\s*([1-3])\s*次")

ROLE_RULES = {
    "本科": ("本科",),
    "硕士": ("硕士",),
    "博士": ("博士",),
    "教师": ("教师",),
    "辅导员": ("辅导员",),
    "行政教辅": ("行政教辅", "行政管理", "行政助理", "教辅"),
    "实验实训": ("实验实训", "实验员", "实训"),
    "科研助理": ("科研助理", "科研秘书", "项目助理"),
    "技能人才": ("技能人才",),
    "高层次人才": ("高层次人才", "人才引进"),
}


def load_rules() -> dict:
    with RULE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_priority(note: str) -> tuple[str, int]:
    match = PRIORITY_PATTERN.search(note or "")
    if match:
        priority = match.group(1).upper()
        return priority, int(priority[1])
    return "P2（备注未标注）", 2


def parse_frequency(text: str) -> tuple[int, str]:
    """提取每周次数；招聘季或联考期的提升次数也纳入排序参考。"""
    matches = [int(item) for item in FREQUENCY_PATTERN.findall(text or "")]
    if not matches:
        return 0, "频率未识别"
    times = max(matches)
    if len(matches) > 1:
        return times, f"最高每周 {times} 次（含招聘季/联考期提升）"
    return times, f"每周 {times} 次"


def days_since(last_checked: str, today: date) -> int:
    try:
        checked_date = datetime.strptime(last_checked.strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        # 日期缺失或格式不标准时，优先交由人工补充，因此按很久未检查处理。
        return 9999
    return max((today - checked_date).days, 0)


def coverage_of(row: dict[str, str]) -> set[str]:
    text = " ".join((row.get("主要关注内容", ""), row.get("来源名称", "")))
    return {
        label
        for label, keywords in ROLE_RULES.items()
        if any(keyword in text for keyword in keywords)
    }


def strict_eligible(row: dict[str, str]) -> bool:
    return row.get("当前状态", "").strip() == "已核验" and row.get("是否重点监控", "").strip() == "是"


def fallback_eligible(row: dict[str, str]) -> bool:
    """只有严格合格来源不足最低数量时才使用，且仍排除待核验/异常/失效来源。"""
    status = row.get("当前状态", "").strip()
    excluded_status_words = ("待核验", "待继续核验", "页面异常", "已失效")
    return row.get("是否重点监控", "").strip() == "是" and not any(
        word in status for word in excluded_status_words
    )


def base_sort_key(item: dict) -> tuple[int, int, int, str]:
    return (
        item["priority_value"],
        -item["days_since_check"],
        -item["frequency_times"],
        item["row"].get("来源编号", ""),
    )


def diversity_order(items: list[dict]) -> list[dict]:
    """不跨越优先级，仅在相同优先级中优先选择可补足覆盖面的来源。"""
    ordered: list[dict] = []
    covered: set[str] = set()
    for priority in range(3):
        group = sorted(
            [item for item in items if item["priority_value"] == priority],
            key=base_sort_key,
        )
        while group:
            group.sort(
                key=lambda item: (
                    -len(item["coverage"] - covered),
                    *base_sort_key(item),
                )
            )
            chosen = group.pop(0)
            ordered.append(chosen)
            covered.update(chosen["coverage"])
    return ordered


def selection_reason(item: dict, new_coverage: set[str], is_fallback: bool) -> str:
    priority = item["priority"]
    days = item["days_since_check"]
    frequency_note = item["frequency_note"]
    reasons = [f"{priority} 优先级", frequency_note, f"距上次检查 {days} 天"]
    if new_coverage:
        reasons.append("补足关注范围：" + "、".join(sorted(new_coverage)))
    if is_fallback:
        reasons.append("严格合格来源不足时的补充选择")
    return "；".join(reasons)


def build_items(rows: list[dict[str, str]], today: date, predicate) -> list[dict]:
    items: list[dict] = []
    for row in rows:
        if not predicate(row):
            continue
        priority, priority_value = parse_priority(row.get("备注", ""))
        frequency_times, frequency_note = parse_frequency(row.get("建议查看频率", ""))
        items.append(
            {
                "row": row,
                "priority": priority,
                "priority_value": priority_value,
                "frequency_times": frequency_times,
                "frequency_note": frequency_note,
                "days_since_check": days_since(row.get("最后检查日期", ""), today),
                "coverage": coverage_of(row),
            }
        )
    return items


def select_items(rows: list[dict[str, str]], today: date, minimum: int, maximum: int) -> list[tuple[dict, bool]]:
    strict_items = build_items(rows, today, strict_eligible)
    ordered_strict = diversity_order(strict_items)
    selected: list[tuple[dict, bool]] = [(item, False) for item in ordered_strict[:maximum]]

    if len(selected) >= minimum:
        return selected

    selected_ids = {item["row"].get("来源编号", "") for item, _ in selected}
    fallback_items = [
        item
        for item in build_items(rows, today, fallback_eligible)
        if item["row"].get("来源编号", "") not in selected_ids
    ]
    for item in diversity_order(fallback_items):
        if len(selected) >= minimum:
            break
        selected.append((item, True))
    return selected


def write_output(path: Path, selected: list[tuple[dict, bool]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_HEADER)
        writer.writeheader()
        covered: set[str] = set()
        for rank, (item, is_fallback) in enumerate(selected, start=1):
            row = item["row"]
            new_coverage = item["coverage"] - covered
            reason = selection_reason(item, new_coverage, is_fallback)
            covered.update(item["coverage"])
            writer.writerow(
                {
                    "来源编号": row.get("来源编号", ""),
                    "学校名称": row.get("学校名称", ""),
                    "城市": row.get("城市", ""),
                    "来源名称": row.get("来源名称", ""),
                    "来源类型": row.get("来源类型", ""),
                    "来源链接": row.get("来源链接", ""),
                    "优先级": item["priority"],
                    "建议查看频率": row.get("建议查看频率", ""),
                    "最后检查日期": row.get("最后检查日期", ""),
                    "主要关注内容": row.get("主要关注内容", ""),
                    "选择原因": reason,
                    "今日排序": rank,
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="选择当天优先巡检的官方来源。")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="明确允许重新生成当天来源表；不加此参数时不会覆盖已有文件。",
    )
    args = parser.parse_args()

    try:
        rules = load_rules()
        count_rules = rules["每日默认检查来源数量"]
        minimum = int(count_rules["最少"])
        maximum = int(count_rules["最多"])
        if minimum < 1 or maximum < minimum:
            raise ValueError("巡检规则中的每日来源数量设置不正确。")
        with SOURCE_FILE.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError, csv.Error) as error:
        print(f"无法选择今日来源：{error}")
        return 1

    today = date.today()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{today.isoformat()}_今日巡检来源.csv"
    if output_path.exists() and not args.overwrite:
        print(f"今天的来源表已存在：{output_path.relative_to(PROJECT_ROOT)}")
        print("为保护已有内容，本次未覆盖。若确认需要重新生成，请执行：")
        print("python scripts/select_daily_sources.py --overwrite")
        return 0

    selected = select_items(rows, today, minimum, maximum)
    write_output(output_path, selected)

    print(f"今日选择来源总数：{len(selected)}（规则范围：{minimum}—{maximum}）")
    print(f"已生成：{output_path.relative_to(PROJECT_ROOT)}")
    for rank, (item, is_fallback) in enumerate(selected, start=1):
        reason = selection_reason(item, set(item["coverage"]), is_fallback)
        row = item["row"]
        print(f"{rank}. {row.get('学校名称', '')}｜{row.get('来源名称', '')}｜{item['priority']}｜{reason}")

    if len(selected) < minimum:
        print("提示：符合条件的来源不足最低数量；未使用待核验、页面异常、已失效或非重点监控来源补足。")
    print("本脚本未访问网络，未修改高校来源表，也未更新最后检查日期。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
