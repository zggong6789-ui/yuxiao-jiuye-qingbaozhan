# 自动化脚本使用说明

这里存放“豫校就业情报站”自动化系统的本地 Python 脚本。当前是 V1.0 基础骨架：可以检查正式数据、创建当天工作区、备份正式数据，但**还没有自动抓取网页或自动入库功能**。

## 运行前准备

1. 电脑需要安装 Python 3。安装时建议勾选“Add Python to PATH”。
2. 在项目根目录打开 PowerShell。
3. 先确认 `data/高校来源表.csv` 和 `data/招聘信息表.csv` 没有被 Excel 等软件占用。

所有当前脚本只使用 Python 自带功能，不需要安装第三方库。

## 当前脚本

### `check_data_health.py`

检查正式数据是否健康：

- 高校来源表是否为 13 个字段；
- 招聘信息表是否为 27 个字段；
- JOB 编号是否重复；
- 官方原文链接是否重复；
- CSV 是否可正常读取。

运行方式：

```powershell
python scripts/check_data_health.py
```

它只检查，不修改任何正式数据。

### `init_daily_workspace.py`

按当天日期创建：

- `workspace/candidates/YYYY-MM-DD_待人工审核候选表.csv`
- `workspace/logs/YYYY-MM-DD_巡检日志.log`

当天文件已经存在时，它会保留原内容，不会覆盖。

运行方式：

```powershell
python scripts/init_daily_workspace.py
```

它不访问网络，不修改 `data` 中的正式数据。

### `backup_data.py`

把两张正式 CSV 复制一份到 `workspace/backups/`。备份文件带有日期和时间，不会覆盖旧备份。

运行方式：

```powershell
python scripts/backup_data.py
```

它只复制原文件，不修改原文件。

### `select_daily_sources.py`

从 `data/高校来源表.csv` 中选择当天优先检查的 5—8 个官方来源。

它只选择“已核验”且“重点监控”的来源，先看备注中的 P0/P1/P2，再比较距上次检查时间和建议查看频率；在同一优先级中尽量兼顾本科、硕士、博士和不同岗位类型。

运行方式：

```powershell
python scripts/select_daily_sources.py
```

结果保存在：

`workspace/candidates/YYYY-MM-DD_今日巡检来源.csv`

如果当天文件已经存在，脚本不会静默覆盖，而是提示停止。确认要重新生成时，使用：

```powershell
python scripts/select_daily_sources.py --overwrite
```

它不访问网络，不抓取公告，不修改“最后检查日期”，也不修改 `data/高校来源表.csv`。

## 运行后看哪里

- 数据检查结果：直接看 PowerShell 的中文输出。
- 当天候选表：`workspace/candidates/`。
- 当天日志：`workspace/logs/`。
- 数据备份：`workspace/backups/`。
- 候选人工终审记录：`workspace/reviews/候选审核结果.csv`。
- 文章人工审核记录：`workspace/reviews/文章审核结果.csv`。
- 公众号发布记录：`workspace/publish/公众号发布记录.csv`。

## 正式数据安全说明

当前三个脚本都不会写入或修改：

- `data/高校来源表.csv`
- `data/招聘信息表.csv`

后续会增加“人工审核通过后安全入库”和“生成公众号文章初稿”等脚本。即使未来增加这些功能，也必须经过人工终审，且默认不自动执行 Git commit 或 push。

## 目前还没有的功能

V1.0 基础骨架尚未实现：

- 自动访问高校招聘网页；
- 自动发现招聘公告；
- 自动生成候选招聘内容；
- 自动写入正式招聘信息表；
- 自动生成公众号文章初稿。

这些功能会在后续阶段逐项增加，并始终遵守项目的人工核验、官方来源、劳务派遣排除和不推断事业编规则。
