"""美股数据拉取（akshare）"""
from zoneinfo import ZoneInfo

import pandas as pd
import akshare as ak


def fetch_us_daily(symbol: str) -> pd.DataFrame:
    """美股日线"""
    df = ak.stock_us_daily(symbol=symbol, adjust="")
    df = df.rename(columns={
        "date": "trade_date", "open": "open", "high": "high",
        "low": "low", "close": "close", "volume": "volume"
    })
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
    if "amount" not in df.columns:
        df["amount"] = None
    return df[["trade_date", "open", "high", "low", "close", "volume", "amount"]]


def fetch_us_weekly(symbol: str) -> pd.DataFrame:
    """美股周线（从日线聚合）"""
    df = fetch_us_daily(symbol)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date")
    weekly = df.resample("W").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna()
    weekly = weekly.reset_index()
    weekly["trade_date"] = weekly["trade_date"].dt.strftime("%Y-%m-%d")
    weekly = weekly.rename(columns={"trade_date": "week_start"})
    return weekly[["week_start", "open", "high", "low", "close", "volume"]]


def fetch_us_monthly(symbol: str) -> pd.DataFrame:
    """美股月线（从日线聚合）"""
    df = fetch_us_daily(symbol)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.set_index("trade_date")
    monthly = df.resample("ME").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna()
    monthly = monthly.reset_index()
    monthly["trade_date"] = monthly["trade_date"].dt.strftime("%Y-%m-%d")
    monthly = monthly.rename(columns={"trade_date": "month"})
    return monthly[["month", "open", "high", "low", "close", "volume"]]


def _filter_us_regular_session(df):
    """
    过滤美股常规交易时段（9:30-16:00 ET）。
    自动处理夏令时(EDT)/冬令时(EST)转换，无需手动切换北京时间窗口。
    北京时间对应：
      - EDT (3月第2周日~11月第1周日): 21:30-04:00
      - EST (11月第1周日~次年3月第2周日): 22:30-05:00
    """
    beijing_tz = ZoneInfo("Asia/Shanghai")
    ny_tz = ZoneInfo("America/New_York")
    dt_bj = df.index.tz_localize(beijing_tz)
    dt_ny = dt_bj.tz_convert(ny_tz)
    minutes = dt_ny.hour * 60 + dt_ny.minute
    mask = (minutes >= 9 * 60 + 30) & (minutes < 16 * 60)
    return df[mask]


def fetch_us_15min(symbol: str) -> pd.DataFrame:
    """美股 15 分钟线（从 1 分钟聚合，仅常规交易时段）"""
    df = ak.stock_us_hist_min_em(symbol=f"105.{symbol}")
    df = df.rename(columns={
        "时间": "dt", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount"
    })
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.set_index("dt")
    df = _filter_us_regular_session(df)
    df_15 = df.resample("15min").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum", "amount": "sum"
    }).dropna()
    df_15 = df_15.reset_index()
    df_15["dt"] = df_15["dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df_15[["dt", "open", "high", "low", "close", "volume", "amount"]]


def fetch_us_1h(symbol: str) -> pd.DataFrame:
    """美股 1 小时线（从 1 分钟聚合，仅常规交易时段，对齐 9:30 ET 开盘）"""
    df = ak.stock_us_hist_min_em(symbol=f"105.{symbol}")
    df = df.rename(columns={
        "时间": "dt", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount"
    })
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.set_index("dt")
    df = _filter_us_regular_session(df)
    # offset=30min 使 1h bar 对齐 9:30 ET 开盘
    df_1h = df.resample("1h", offset="30min").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum", "amount": "sum"
    }).dropna()
    df_1h = df_1h.reset_index()
    df_1h["dt"] = df_1h["dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df_1h[["dt", "open", "high", "low", "close", "volume", "amount"]]
