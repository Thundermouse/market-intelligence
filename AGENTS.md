# AGENTS.md

本文件只覆盖 `market-intelligence/` 目录。工作区其他项目不在本文件范围内。

## 项目定位

多周期行情数据管线：A股 / 港股 / 美股，日线、周线、月线、15分钟、1小时，另有美股盘前。
Python + SQLite，数据源为 akshare（东方财富）与 iFinD MCP。

## 目录结构

- `src/market_data/` — 全部核心逻辑，**包名是 `market_data`**，不随目录改名
  - `fetchers/` — 按市场拆分：`a_share.py`、`hk_stock.py`、`us_stock.py`
  - `db/` — 连接管理与 `schema.sql`
  - `pipeline.py` — 拉取编排
  - `ensure.py` — 就绪校验（历史长度 + 新鲜度）
  - `storage.py` — 入库写入
  - `query.py` — 查询
  - `premarket.py` — 美股盘前
- `scripts/` — CLI 入口，统一 `sys.path` 注入 `../src`
- `data/market_data.db` — SQLite 数据库（文件名沿用旧名，属预期）
- `result/` — 运行产物，按 `China-market` / `US-market` 分目录（**不入库**）
- `skills/` — `market-intelligence-fetch`、`market-intelligence-db`、`market-intelligence-e2e`、`investment-roundtable`
- `automations/` — 4 个定时分析任务的定义快照（cron + prompt），用于备份与恢复
- `tests/` — pytest，含 `tests/e2e/`

## 数据库

表：`securities`、`daily_ohlcv`、`kline_15min`、`kline_1h`、`kline_weekly`、`kline_monthly`、`premarket_data`、`fetch_log`。

## 常用命令

在本目录下执行：

- 拉取指定标的：`python scripts/fetch_data.py --code 600519 --market A股 --periods daily weekly monthly`
- 检查并补齐缺失：`python scripts/ensure_data.py --codes 600519 000001 --market A股`
- 查询：`python scripts/query_data.py --code 600519 --period daily --limit 10`
- 美股盘前：`python scripts/fetch_premarket.py --symbols AAPL MSFT`
- 测试：`pytest tests -q`（`pythonpath=src` 已配置，无需安装包）

参数取值：`--market` 为 `A股` / `美股` / `港股`；`--periods` 为 `daily` / `weekly` / `monthly` / `15min` / `1h`。

## 约定

- 命名：目录、`pyproject.toml` 的 `name`、skill 前缀统一用 `market-intelligence`；Python 包与数据库文件仍用 `market_data`，不要跟着改。
- 数据库只通过 `src/market_data` 读写，不要手写 SQL 直接改库。
- 分钟线历史有上限（API 约 50 天），`ensure` 对分钟级只校验新鲜度，不校验历史长度。
- 时间统一按 `Asia/Shanghai`；盘前数据存 `premarket_data` 表，与常规交易时段分开。
- 拉取前先判断新鲜度，已有的完整历史区间不要重复覆盖。
- 新文件保持现有风格：`sys.path` 注入 `../src`，不依赖安装。

## 禁止

- 不要删除 `data/market_data.db`，重建需先确认。
- 不要擅自重命名 `market_data` 包或 `market_data.db`。
- 数据库文件、`result/` 产物不外发、不入库。
