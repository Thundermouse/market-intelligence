"""美股盘前数据拉取与清理（临时存储，独立于 K 线表）"""
from datetime import date, datetime, timedelta

import akshare as ak
import pandas as pd

from .db import get_conn


def fetch_premarket(symbol: str):
    """
    获取美股盘前快照。
    取 akshare 1 分钟分时的最新收盘价作为盘前价。
    """
    try:
        df = ak.stock_us_hist_min_em(symbol=f"105.{symbol}")
        if df.empty:
            return None
        df = df.rename(columns={"时间": "dt", "收盘": "close", "成交量": "volume"})
        df["dt"] = pd.to_datetime(df["dt"])
        latest = df.iloc[-1]
        daily = ak.stock_us_daily(symbol=symbol, adjust="")
        prev_close = float(daily["close"].iloc[-1]) if not daily.empty else None
        return {
            "security_code": symbol,
            "fetch_date": date.today().isoformat(),
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "premarket_price": float(latest["close"]),
            "prev_close": prev_close,
            "change_percent": (
                ((float(latest["close"]) - prev_close) / prev_close * 100)
                if prev_close else None
            ),
            "volume": int(latest["volume"]) if pd.notna(latest.get("volume")) else None,
            "source": "akshare",
            "is_active": 1,
        }
    except Exception as e:
        print(f"  ❌ 拉取盘前数据失败: {str(e)[:100]}")
        return None


def save_premarket(conn, data):
    """保存盘前数据（每天每只标的一条，覆盖更新）"""
    conn.execute("""
        INSERT OR REPLACE INTO premarket_data
        (security_code, fetch_date, fetch_time, premarket_price, prev_close,
         change_percent, volume, source, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["security_code"], data["fetch_date"], data["fetch_time"],
        data["premarket_price"], data["prev_close"], data["change_percent"],
        data["volume"], data["source"], data["is_active"],
    ))
    conn.commit()


def cleanup_old_premarket(conn, days: int = 1) -> int:
    """清理 N 天前的盘前数据"""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    cursor = conn.execute("DELETE FROM premarket_data WHERE fetch_date < ?", (cutoff,))
    conn.commit()
    return cursor.rowcount
