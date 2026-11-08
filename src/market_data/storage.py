"""数据写入层：upsert 函数 + 拉取日志"""
from datetime import date


def upsert_daily(conn, code, df):
    """写入日线数据（INSERT OR REPLACE）"""
    rows = []
    for _, r in df.iterrows():
        rows.append((code, r["trade_date"], r.get("open"), r.get("high"),
                     r.get("low"), r.get("close"), r.get("volume"),
                     r.get("amount"), r.get("turnover"), "akshare"))
    conn.executemany("""
        INSERT OR REPLACE INTO daily_ohlcv
        (security_code, trade_date, open, high, low, close, volume, amount, turnover, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)


def upsert_15min(conn, code, df):
    """写入 15 分钟线（先删旧数据再写入，避免盘后时段残留）"""
    conn.execute("DELETE FROM kline_15min WHERE security_code = ?", (code,))
    rows = []
    for _, r in df.iterrows():
        rows.append((code, r["dt"], r.get("open"), r.get("high"),
                     r.get("low"), r.get("close"), r.get("volume"),
                     r.get("amount"), "akshare"))
    conn.executemany("""
        INSERT OR REPLACE INTO kline_15min
        (security_code, dt, open, high, low, close, volume, amount, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)


def upsert_1h(conn, code, df):
    """写入 1 小时线（先删旧数据再写入，避免盘后时段残留）"""
    conn.execute("DELETE FROM kline_1h WHERE security_code = ?", (code,))
    rows = []
    for _, r in df.iterrows():
        rows.append((code, r["dt"], r.get("open"), r.get("high"),
                     r.get("low"), r.get("close"), r.get("volume"),
                     r.get("amount"), "akshare"))
    conn.executemany("""
        INSERT OR REPLACE INTO kline_1h
        (security_code, dt, open, high, low, close, volume, amount, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)


def upsert_weekly(conn, code, df):
    rows = []
    for _, r in df.iterrows():
        rows.append((code, r["week_start"], r.get("open"), r.get("high"),
                     r.get("low"), r.get("close"), r.get("volume"), "akshare"))
    conn.executemany("""
        INSERT OR REPLACE INTO kline_weekly
        (security_code, week_start, open, high, low, close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)


def upsert_monthly(conn, code, df):
    rows = []
    for _, r in df.iterrows():
        rows.append((code, r["month"], r.get("open"), r.get("high"),
                     r.get("low"), r.get("close"), r.get("volume"), "akshare"))
    conn.executemany("""
        INSERT OR REPLACE INTO kline_monthly
        (security_code, month, open, high, low, close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)


def log_fetch(conn, code, period, rows, status="success", error=None):
    conn.execute("""
        INSERT INTO fetch_log (security_code, period, fetch_date, rows_affected, source, status, error_msg)
        VALUES (?, ?, ?, ?, 'akshare', ?, ?)
    """, (code, period, date.today().isoformat(), rows, status, error))
    conn.commit()
