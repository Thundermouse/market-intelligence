-- ============================================================
-- Market Data Database Schema
-- 兼容 SQLite / MySQL（语法尽量通用）
-- ============================================================

-- 证券基础信息表
CREATE TABLE IF NOT EXISTS securities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL,
    exchange VARCHAR(20),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, market)
);

-- 每日 OHLCV 数据（永久保存，不删除）
CREATE TABLE IF NOT EXISTS daily_ohlcv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(18,4),
    high DECIMAL(18,4),
    low DECIMAL(18,4),
    close DECIMAL(18,4),
    volume BIGINT,
    amount DECIMAL(20,2),
    turnover DECIMAL(10,4),
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(security_code, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_daily_code_date ON daily_ohlcv(security_code, trade_date);

-- 15分钟 K 线
CREATE TABLE IF NOT EXISTS kline_15min (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_code VARCHAR(20) NOT NULL,
    dt DATETIME NOT NULL,
    open DECIMAL(18,4),
    high DECIMAL(18,4),
    low DECIMAL(18,4),
    close DECIMAL(18,4),
    volume BIGINT,
    amount DECIMAL(20,2),
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(security_code, dt)
);
CREATE INDEX IF NOT EXISTS idx_15min_code_dt ON kline_15min(security_code, dt);

-- 1小时 K 线
CREATE TABLE IF NOT EXISTS kline_1h (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_code VARCHAR(20) NOT NULL,
    dt DATETIME NOT NULL,
    open DECIMAL(18,4),
    high DECIMAL(18,4),
    low DECIMAL(18,4),
    close DECIMAL(18,4),
    volume BIGINT,
    amount DECIMAL(20,2),
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(security_code, dt)
);
CREATE INDEX IF NOT EXISTS idx_1h_code_dt ON kline_1h(security_code, dt);

-- 周线 K 线
CREATE TABLE IF NOT EXISTS kline_weekly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_code VARCHAR(20) NOT NULL,
    week_start DATE NOT NULL,
    open DECIMAL(18,4),
    high DECIMAL(18,4),
    low DECIMAL(18,4),
    close DECIMAL(18,4),
    volume BIGINT,
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(security_code, week_start)
);

-- 月线 K 线
CREATE TABLE IF NOT EXISTS kline_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_code VARCHAR(20) NOT NULL,
    month DATE NOT NULL,
    open DECIMAL(18,4),
    high DECIMAL(18,4),
    low DECIMAL(18,4),
    close DECIMAL(18,4),
    volume BIGINT,
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(security_code, month)
);

-- 盘前临时数据（美股盘前一次性抓取，收盘后可清理）
CREATE TABLE IF NOT EXISTS premarket_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_code VARCHAR(20) NOT NULL,
    fetch_date DATE NOT NULL,
    fetch_time TIMESTAMP NOT NULL,
    premarket_price DECIMAL(18,4),
    prev_close DECIMAL(18,4),
    change_percent DECIMAL(10,4),
    volume BIGINT,
    source VARCHAR(20),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(security_code, fetch_date)
);

-- 数据新鲜度日志（记录每次拉取的时间和范围）
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_code VARCHAR(20) NOT NULL,
    period VARCHAR(10) NOT NULL,
    fetch_date DATE NOT NULL,
    rows_affected INTEGER,
    source VARCHAR(20),
    status VARCHAR(10),
    error_msg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
