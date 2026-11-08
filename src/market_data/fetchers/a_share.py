"""A股数据拉取（akshare 东方财富）"""
import pandas as pd
import akshare as ak


def fetch_a_daily(code: str, name: str = "") -> pd.DataFrame:
    """A股日线"""
    df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
    df = df.rename(columns={
        "日期": "trade_date", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume",
        "成交额": "amount", "换手率": "turnover"
    })
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
    return df[["trade_date", "open", "high", "low", "close", "volume", "amount", "turnover"]]


def fetch_a_weekly(code: str) -> pd.DataFrame:
    """A股周线"""
    df = ak.stock_zh_a_hist(symbol=code, period="weekly", adjust="qfq")
    df = df.rename(columns={
        "日期": "week_start", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume"
    })
    df["week_start"] = pd.to_datetime(df["week_start"]).dt.strftime("%Y-%m-%d")
    return df[["week_start", "open", "high", "low", "close", "volume"]]


def fetch_a_monthly(code: str) -> pd.DataFrame:
    """A股月线"""
    df = ak.stock_zh_a_hist(symbol=code, period="monthly", adjust="qfq")
    df = df.rename(columns={
        "日期": "month", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume"
    })
    df["month"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m-%d")
    return df[["month", "open", "high", "low", "close", "volume"]]


def fetch_a_15min(code: str) -> pd.DataFrame:
    """A股 15 分钟线"""
    df = ak.stock_zh_a_hist_min_em(symbol=code, period="15")
    df = df.rename(columns={
        "时间": "dt", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount"
    })
    df["dt"] = pd.to_datetime(df["dt"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df[["dt", "open", "high", "low", "close", "volume", "amount"]]


def fetch_a_1h(code: str) -> pd.DataFrame:
    """A股 1 小时线"""
    df = ak.stock_zh_a_hist_min_em(symbol=code, period="60")
    df = df.rename(columns={
        "时间": "dt", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount"
    })
    df["dt"] = pd.to_datetime(df["dt"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df[["dt", "open", "high", "low", "close", "volume", "amount"]]
