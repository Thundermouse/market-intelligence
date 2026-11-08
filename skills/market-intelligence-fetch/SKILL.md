---
name: market-intelligence-fetch
description: 多周期行情数据拉取 Skill。从 akshare（东方财富）和 iFinD MCP 拉取 A股/美股的日线、周线、月线、15分钟线、1小时线以及美股盘前数据，存入本地 SQLite 数据库。支持数据新鲜度检查，避免重复拉取。Use when 需要获取股票多周期K线数据、盘前行情、或判断数据是否需要更新。
---

# 多周期行情数据拉取 Skill

## 数据源与优先级

| 优先级 | 数据源 | 覆盖范围 |
|---|---|---|
| ① | **akshare（东方财富）** | A股：全周期；美股：日线、15min/1h（从1分钟聚合）、周线/月线（从日线聚合） |
| ② | **iFinD MCP** | A股：日内高频（15min/1h 仅交易日）；全市场：日频指标 |
| ③ | **WebSearch/WebFetch** | 兜底，从 Barchart/Yahoo Finance 补充 |

## 数据库

- 位置：`/home/yuhaic/workspace/market-intelligence/data/market_data.db`
- 类型：SQLite（WAL 模式，支持并发）
- Schema：`/home/yuhaic/workspace/market-intelligence/src/market_data/db/schema.sql`

## 数据表

| 表名 | 用途 | 周期 |
|---|---|---|
| `daily_ohlcv` | 每日 OHLCV（永久保存） | 日线 |
| `kline_15min` | 15 分钟 K 线 | 15min |
| `kline_1h` | 1 小时 K 线 | 1h |
| `kline_weekly` | 周线 K 线 | weekly |
| `kline_monthly` | 月线 K 线 | monthly |
| `premarket_data` | 美股盘前临时数据 | premarket |
| `fetch_log` | 拉取日志 | — |

## 使用方法

### 1. 初始化数据库（首次使用）

```bash
cd /home/yuhaic/workspace/market-intelligence
PYTHONPATH=src python3 -c "from market_data.db import init_db; init_db()"
```

或直接运行任意拉取脚本（会自动初始化）：

```bash
python3 scripts/fetch_data.py --code 600519 --market A股 --periods daily
```

### 2. 拉取多周期数据

```bash
cd /home/yuhaic/workspace/market-intelligence

# A股日线+周线+月线
python3 scripts/fetch_data.py --code 600519 --market A股 --periods daily weekly monthly

# 美股全部周期
python3 scripts/fetch_data.py --code AAPL --market 美股 --periods daily weekly monthly 15min 1h

# A股日内高频（仅交易日有效）
python3 scripts/fetch_data.py --code 600519 --market A股 --periods 15min 1h
```

### 3. 拉取美股盘前数据

```bash
cd /home/yuhaic/workspace/market-intelligence
python3 scripts/fetch_premarket.py --symbols AAPL TSLA NVDA
```

### 4. 查询数据

```bash
# 日线
python3 scripts/query_data.py --code 600519 --period daily --limit 10

# 周线
python3 scripts/query_data.py --code AAPL --period weekly --limit 10

# 盘前
python3 scripts/query_data.py --code AAPL --period premarket
```

## 数据新鲜度检查

每次圆桌会议前，先检查数据新鲜度：

```bash
python3 scripts/query_data.py --code <代码> --period daily
```

- 输出 `最新数据: YYYY-MM-DD（N 天前）`
- 若 N > 2，需重新拉取：`python3 scripts/fetch_data.py --code <代码> --market <市场> --periods daily`

## 与圆桌会议集成

在投资圆桌会议中，A3（多周期趋势分析师）应：
1. 优先从数据库读取多周期数据
2. 若数据过期（>2 天），调用 `fetch_data.py` 更新
3. 盘前会议调用 `fetch_premarket.py` 获取最新盘前价
4. 将数据库数据与 iFinD 实时数据交叉验证

## 注意事项

- 日线数据永久保存，不删除（节省数据源额度）
- 15min/1h 数据可定期清理（保留最近 N 天）
- 盘前数据每天一条，自动清理 1 天前的旧数据
- akshare 美股代码格式：直接用 `AAPL`（脚本内部会加 `105.` 前缀）
- A 股代码：用 6 位数字（如 `600519`）
