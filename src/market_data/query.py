"""数据查询层：从数据库读取多周期行情数据"""
from datetime import date

from .db import get_conn

_TABLE_MAP = {
    "15min": "kline_15min",
    "1h": "kline_1h",
    "weekly": "kline_weekly",
    "monthly": "kline_monthly",
}


def query_daily(conn, code: str, limit: int = 30):
    """查询日线数据"""
    cursor = conn.execute("""
        SELECT trade_date, open, high, low, close, volume
        FROM daily_ohlcv
        WHERE security_code = ?
        ORDER BY trade_date DESC
        LIMIT ?
    """, (code, limit))
    return cursor.fetchall()


def query_period(conn, code: str, period: str, limit: int = 30):
    """查询指定周期数据（15min / 1h / weekly / monthly）"""
    table = _TABLE_MAP.get(period)
    if not table:
        return []
    date_col = "week_start" if period == "weekly" else "month" if period == "monthly" else "dt"
    cursor = conn.execute(f"""
        SELECT {date_col}, open, high, low, close, volume
        FROM {table}
        WHERE security_code = ?
        ORDER BY {date_col} DESC
        LIMIT ?
    """, (code, limit))
    return cursor.fetchall()


def query_premarket(conn, code: str):
    """查询最新盘前数据"""
    cursor = conn.execute("""
        SELECT fetch_date, premarket_price, prev_close, change_percent, volume
        FROM premarket_data
        WHERE security_code = ? AND is_active = 1
        ORDER BY fetch_date DESC
        LIMIT 1
    """, (code,))
    return cursor.fetchone()


def check_freshness(conn, code: str, period: str = "daily"):
    """检查数据新鲜度：(最新日期, 距今天数)"""
    col_map = {"daily": "trade_date", "weekly": "week_start", "monthly": "month"}
    table_map = {"daily": "daily_ohlcv", "weekly": "kline_weekly", "monthly": "kline_monthly"}
    if period not in col_map:
        return None
    cursor = conn.execute(
        f"SELECT MAX({col_map[period]}) FROM {table_map[period]} WHERE security_code = ?",
        (code,),
    )
    row = cursor.fetchone()
    if not row or not row[0]:
        return None
    latest_date = date.fromisoformat(row[0])
    days = (date.today() - latest_date).days
    return latest_date, days
