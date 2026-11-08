"""行情数据拉取器集合：A股 / 美股 / 港股"""
from .a_share import fetch_a_daily, fetch_a_weekly, fetch_a_monthly, fetch_a_15min, fetch_a_1h
from .us_stock import fetch_us_daily, fetch_us_weekly, fetch_us_monthly, fetch_us_15min, fetch_us_1h
from .hk_stock import fetch_hk_daily, fetch_hk_weekly, fetch_hk_monthly, fetch_hk_15min, fetch_hk_1h

__all__ = [
    "fetch_a_daily", "fetch_a_weekly", "fetch_a_monthly", "fetch_a_15min", "fetch_a_1h",
    "fetch_us_daily", "fetch_us_weekly", "fetch_us_monthly", "fetch_us_15min", "fetch_us_1h",
    "fetch_hk_daily", "fetch_hk_weekly", "fetch_hk_monthly", "fetch_hk_15min", "fetch_hk_1h",
]
