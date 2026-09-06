#!/usr/bin/env python3
"""初始化当天的候选表和巡检日志；不访问网络，也不修改正式数据。"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_DIR = PROJECT_ROOT / "workspace" / "candidates"
LOGS_DIR = PROJECT_ROOT / "workspace" / "logs"

CANDIDATE_HEADER = [
    "候选编号",
    "扫描日期",
    "学校/单位",
    "公告标题",
    "公告发布日期",
    "官方原文链接",
    "来源名称",
    "来源链接",
    "招聘类型",
    "主要岗位",
    "招聘人数",
    "可报学历",
    "报名截止时间/有效期原文",
    "报名方式",
    "岗位性质/编制/聘用方式官方表述",
    "附件链接/附件提示",
    "相关后续公告链接/提示",
    "当前状态",
    "是否疑似重复",
    "建议",
    "推荐理由",
    "核验状态",
    "备注",
]


def create_candidate_file(path: Path) -> bool:
    if path.exists():
        print(f"候选表已存在，保留原内容：{path.relative_to(PROJECT_ROOT)}")
        return False
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        csv.writer(file).writerow(CANDIDATE_HEADER)
    print(f"已创建候选表：{path.relative_to(PROJECT_ROOT)}")
    return True


def create_log_file(path: Path, today: str) -> bool:
    if path.exists():
        print(f"巡检日志已存在，保留原内容：{path.relative_to(PROJECT_ROOT)}")
        return False
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = (
        f"豫校就业情报站每日巡检日志\n"
        f"日期：{today}\n"
        f"创建时间：{created_at}\n"
        "说明：本日志由工作区初始化脚本创建；尚未执行网络巡检。\n\n"
    )
    path.write_text(content, encoding="utf-8")
    print(f"已创建巡检日志：{path.relative_to(PROJECT_ROOT)}")
    return True


def main() -> None:
    today = date.today().isoformat()
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    candidate_file = CANDIDATES_DIR / f"{today}_待人工审核候选表.csv"
    log_file = LOGS_DIR / f"{today}_巡检日志.log"

    print(f"初始化日期：{today}")
    create_candidate_file(candidate_file)
    create_log_file(log_file, today)
    print("初始化完成：未访问网络，未修改 data 目录中的正式 CSV。")


if __name__ == "__main__":
    main()
