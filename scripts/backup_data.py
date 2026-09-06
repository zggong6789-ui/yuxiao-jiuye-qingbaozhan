#!/usr/bin/env python3
"""为正式 CSV 创建带时间戳的只读备份；不会改写原始文件。"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "workspace" / "backups"
DATA_FILES = [
    PROJECT_ROOT / "data" / "高校来源表.csv",
    PROJECT_ROOT / "data" / "招聘信息表.csv",
]


def unique_backup_path(source: Path, timestamp: str) -> Path:
    candidate = BACKUP_DIR / f"{source.stem}_{timestamp}{source.suffix}"
    sequence = 1
    while candidate.exists():
        candidate = BACKUP_DIR / f"{source.stem}_{timestamp}_{sequence}{source.suffix}"
        sequence += 1
    return candidate


def main() -> int:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("豫校就业情报站：正式数据备份")
    print("说明：本脚本只复制 data 中的 CSV，不会修改原文件。")

    for source in DATA_FILES:
        if not source.exists():
            print(f"备份失败：找不到文件：{source.relative_to(PROJECT_ROOT)}")
            return 1
        destination = unique_backup_path(source, timestamp)
        shutil.copy2(source, destination)
        print(f"已备份：{source.relative_to(PROJECT_ROOT)} → {destination.relative_to(PROJECT_ROOT)}")

    print("备份完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
