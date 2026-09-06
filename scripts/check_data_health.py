#!/usr/bin/env python3
"""检查正式 CSV 的字段、重复项与可读性；本脚本不会修改任何数据。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = PROJECT_ROOT / "data" / "高校来源表.csv"
JOB_FILE = PROJECT_ROOT / "data" / "招聘信息表.csv"

SOURCE_FIELD_COUNT = 13
JOB_FIELD_COUNT = 27


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]], list[str]]:
    """使用 UTF-8（兼容 BOM）读取 CSV，并检查每行字段数量。"""
    issues: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.reader(file))
    except FileNotFoundError:
        return [], [], [f"找不到文件：{path}"]
    except (UnicodeDecodeError, csv.Error) as error:
        return [], [], [f"CSV 无法正常读取：{error}"]

    if not rows:
        return [], [], ["CSV 为空。"]

    header = rows[0]
    data_rows = rows[1:]
    expected_count = len(header)
    for row_number, row in enumerate(data_rows, start=2):
        if len(row) != expected_count:
            issues.append(
                f"第 {row_number} 行有 {len(row)} 个字段，应为 {expected_count} 个字段。"
            )
    return header, data_rows, issues


def find_duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        if normalized in seen and normalized not in duplicates:
            duplicates.append(normalized)
        seen.add(normalized)
    return duplicates


def print_result(label: str, passed: bool, detail: str) -> None:
    status = "通过" if passed else "发现问题"
    print(f"[{status}] {label}：{detail}")


def main() -> int:
    print("豫校就业情报站：正式数据健康检查")
    print("说明：本脚本仅检查，不会修改任何 CSV 数据。\n")

    has_problem = False
    source_header, source_rows, source_issues = read_csv_rows(SOURCE_FILE)
    job_header, job_rows, job_issues = read_csv_rows(JOB_FILE)

    source_ok = len(source_header) == SOURCE_FIELD_COUNT
    print_result(
        "高校来源表字段数",
        source_ok,
        f"当前 {len(source_header)} 个字段，要求 {SOURCE_FIELD_COUNT} 个字段。",
    )
    has_problem = has_problem or not source_ok

    job_ok = len(job_header) == JOB_FIELD_COUNT
    print_result(
        "招聘信息表字段数",
        job_ok,
        f"当前 {len(job_header)} 个字段，要求 {JOB_FIELD_COUNT} 个字段。",
    )
    has_problem = has_problem or not job_ok

    for label, issues in (("高校来源表 CSV 格式", source_issues), ("招聘信息表 CSV 格式", job_issues)):
        if issues:
            print_result(label, False, "；".join(issues))
            has_problem = True
        else:
            print_result(label, True, "可正常读取，所有数据行字段数一致。")

    if "信息编号" in job_header:
        job_id_index = job_header.index("信息编号")
        duplicate_job_ids = find_duplicates(
            [row[job_id_index] for row in job_rows if len(row) > job_id_index]
        )
        if duplicate_job_ids:
            print_result("JOB 编号重复", False, "、".join(duplicate_job_ids))
            has_problem = True
        else:
            print_result("JOB 编号重复", True, f"共检查 {len(job_rows)} 条招聘记录，未发现重复编号。")
    else:
        print_result("JOB 编号检查", False, "未找到“信息编号”字段。")
        has_problem = True

    if "官方原文链接" in job_header:
        url_index = job_header.index("官方原文链接")
        duplicate_urls = find_duplicates(
            [row[url_index] for row in job_rows if len(row) > url_index]
        )
        if duplicate_urls:
            print_result("官方原文链接重复", False, "、".join(duplicate_urls))
            has_problem = True
        else:
            print_result("官方原文链接重复", True, "未发现重复的非空官方原文链接。")
    else:
        print_result("官方原文链接检查", False, "未找到“官方原文链接”字段。")
        has_problem = True

    print(f"\n记录统计：高校来源表 {len(source_rows)} 条；招聘信息表 {len(job_rows)} 条。")
    if has_problem:
        print("检查完成：发现问题。请先核对上述内容，暂不要进行自动入库。")
        return 1

    print("检查完成：正式 CSV 结构与基础去重检查均正常。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
