"""港股数据拉取（akshare）"""
import pandas as pd
import akshare as ak


def fetch_hk_daily(symbol: str) -> pd.DataFrame:
    """港股日线"""
    df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
    df = df.rename(columns={
        "date": "trade_date", "open": "open", "high": "high",
        "low": "low", "close": "close", "volume": "volume", "amount": "amount"
    })
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
    return df[["trade_date", "open", "high", "low", "close", "volume", "amount"]]


def fetch_hk_weekly(symbol: str) -> pd.DataFrame:
    """港股周线（从日线聚合）"""
    df = fetch_hk_daily(symbol)
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


def fetch_hk_monthly(symbol: str) -> pd.DataFrame:
    """港股月线（从日线聚合）"""
    df = fetch_hk_daily(symbol)
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


def fetch_hk_15min(symbol: str) -> pd.DataFrame:
    """港股 15 分钟线"""
    df = ak.stock_hk_hist_min_em(symbol=symbol, period="15")
    df = df.rename(columns={
        "时间": "dt", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount"
    })
    df["dt"] = pd.to_datetime(df["dt"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df[["dt", "open", "high", "low", "close", "volume", "amount"]]


def fetch_hk_1h(symbol: str) -> pd.DataFrame:
    """港股 1 小时线（从 15 分钟聚合）"""
    df = ak.stock_hk_hist_min_em(symbol=symbol, period="15")
    df = df.rename(columns={
        "时间": "dt", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount"
    })
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.set_index("dt")
    df_1h = df.resample("1h").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum", "amount": "sum"
    }).dropna()
    df_1h = df_1h.reset_index()
    df_1h["dt"] = df_1h["dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df_1h[["dt", "open", "high", "low", "close", "volume", "amount"]]
