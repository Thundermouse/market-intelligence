---
name: market-intelligence-db
description: 行情数据库读写 Skill。提供 SQLite 数据库的连接、查询、写入、数据新鲜度检查等操作，支持日线、周线、月线、15分钟线、1小时线、盘前数据的读写。Use when 需要从数据库读取历史行情、写入新数据、检查数据新鲜度、或执行自定义 SQL 查询。
---

# 行情数据库读写 Skill

## 数据库信息

- **路径**：`/home/yuhaic/workspace/market-intelligence/data/market_data.db`
- **类型**：SQLite（WAL 模式，支持并发读写）
- **Schema**：`/home/yuhaic/workspace/market-intelligence/src/market_data/db/schema.sql`

## 连接方式

### Python

```python
import sys
sys.path.insert(0, "/home/yuhaic/workspace/market-intelligence/src")
from market_data.db import get_conn

conn = get_conn()
cursor = conn.execute("SELECT * FROM daily_ohlcv WHERE security_code = ? LIMIT 5", ("600519",))
rows = cursor.fetchall()
conn.close()
```

### SQLAlchemy

```python
from sqlalchemy import create_engine, text

engine = create_engine(
    "sqlite:////home/yuhaic/workspace/market-intelligence/data/market_data.db",
    connect_args={"check_same_thread": False}
)
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM daily_ohlcv WHERE security_code = :code LIMIT 5"), {"code": "600519"})
    rows = result.fetchall()
```

### 命令行

```bash
sqlite3 /home/yuhaic/workspace/market-intelligence/data/market_data.db "SELECT * FROM daily_ohlcv WHERE security_code='600519' ORDER BY trade_date DESC LIMIT 5;"
```

## 表结构

### securities（证券基础信息）
```
id, code, name, market, exchange, industry, created_at, updated_at
UNIQUE(code, market)
```

### daily_ohlcv（每日 OHLCV，永久保存）
```
id, security_code, trade_date, open, high, low, close, volume, amount, turnover, source, created_at
UNIQUE(security_code, trade_date)
```

### kline_15min / kline_1h（分钟线）
```
id, security_code, dt, open, high, low, close, volume, amount, source, created_at
UNIQUE(security_code, dt)
```

### kline_weekly（周线）
```
id, security_code, week_start, open, high, low, close, volume, source, created_at
UNIQUE(security_code, week_start)
```

### kline_monthly（月线）
```
id, security_code, month, open, high, low, close, volume, source, created_at
UNIQUE(security_code, month)
```

### premarket_data（盘前临时数据）
```
id, security_code, fetch_date, fetch_time, premarket_price, prev_close, change_percent, volume, source, is_active, created_at
UNIQUE(security_code, fetch_date)
```

### fetch_log（拉取日志）
```
id, security_code, period, fetch_date, rows_affected, source, status, error_msg, created_at
```

## 常用查询

### 查询某标的日线（最近 N 条）
```sql
SELECT trade_date, open, high, low, close, volume
FROM daily_ohlcv
WHERE security_code = '600519'
ORDER BY trade_date DESC
LIMIT 30;
```

### 查询某标的周线
```sql
SELECT week_start, open, high, low, close, volume
FROM kline_weekly
WHERE security_code = 'AAPL'
ORDER BY week_start DESC
LIMIT 52;
```

### 查询某标的月线
```sql
SELECT month, open, high, low, close, volume
FROM kline_monthly
WHERE security_code = 'AAPL'
ORDER BY month DESC
LIMIT 12;
```

### 查询 15 分钟线（最近 N 条）
```sql
SELECT dt, open, high, low, close, volume
FROM kline_15min
WHERE security_code = '600519'
ORDER BY dt DESC
LIMIT 100;
```

### 查询盘前数据
```sql
SELECT fetch_date, premarket_price, prev_close, change_percent, volume
FROM premarket_data
WHERE security_code = 'AAPL' AND is_active = 1
ORDER BY fetch_date DESC
LIMIT 1;
```

### 检查数据新鲜度
```sql
-- 日线最新日期
SELECT MAX(trade_date) FROM daily_ohlcv WHERE security_code = '600519';

-- 周线最新日期
SELECT MAX(week_start) FROM kline_weekly WHERE security_code = 'AAPL';

-- 月线最新日期
SELECT MAX(month) FROM kline_monthly WHERE security_code = 'AAPL';
```

### 查看拉取日志
```sql
SELECT security_code, period, fetch_date, rows_affected, status, created_at
FROM fetch_log
ORDER BY created_at DESC
LIMIT 20;
```

## 写入操作

### 写入日线数据（INSERT OR REPLACE）
```sql
INSERT OR REPLACE INTO daily_ohlcv
(security_code, trade_date, open, high, low, close, volume, amount, turnover, source)
VALUES ('600519', '2026-11-06', 1450.00, 1457.72, 1436.00, 1453.00, 42848, 6200000000, 0.34, 'akshare');
```

### 批量写入
使用 `executemany` 批量插入，性能更好。

### 写入盘前数据
```sql
INSERT OR REPLACE INTO premarket_data
(security_code, fetch_date, fetch_time, premarket_price, prev_close, change_percent, volume, source, is_active)
VALUES ('AAPL', '2026-11-07', '2026-11-07 21:30:00', 345.00, 344.17, 0.24, 1000000, 'akshare', 1);
```

## 数据清理

### 清理旧盘前数据
```sql
DELETE FROM premarket_data WHERE fetch_date < date('now', '-1 day');
```

### 清理旧分钟线（保留最近 30 天）
```sql
DELETE FROM kline_15min WHERE dt < datetime('now', '-30 days');
DELETE FROM kline_1h WHERE dt < datetime('now', '-30 days');
```

**注意**：日线、周线、月线数据永久保存，不清理。

## 数据新鲜度判断规则

| 周期 | 新鲜阈值 | 过期处理 |
|---|---|---|
| 日线 | ≤ 2 天 | 重新拉取 |
| 周线 | ≤ 8 天 | 重新拉取 |
| 月线 | ≤ 35 天 | 重新拉取 |
| 15min/1h | 仅交易日 | 交易日盘中拉取 |
| 盘前 | 当天 | 盘前时段拉取 |

## 注意事项

- 所有写入操作使用 `INSERT OR REPLACE`，确保幂等
- 日线/周线/月线数据永久保存，不删除（节省数据源额度）
- 分钟线和盘前数据是临时的，可定期清理
- 并发读写使用 WAL 模式，不会阻塞
- 数据库文件路径固定，所有脚本和 Skill 统一使用
