"""数据拉取主流程：按市场/周期路由 fetcher + storage"""
from .db import get_conn
from .fetchers import (
    fetch_a_daily, fetch_a_weekly, fetch_a_monthly, fetch_a_15min, fetch_a_1h,
    fetch_us_daily, fetch_us_weekly, fetch_us_monthly, fetch_us_15min, fetch_us_1h,
    fetch_hk_daily, fetch_hk_weekly, fetch_hk_monthly, fetch_hk_15min, fetch_hk_1h,
)
from .storage import (
    upsert_daily, upsert_weekly, upsert_monthly, upsert_15min, upsert_1h, log_fetch,
)

# 周期 -> (按市场选择的 fetcher, upsert 函数)
_FETCHER_MAP = {
    "daily": (
        {"A股": fetch_a_daily, "港股": fetch_hk_daily, "美股": fetch_us_daily},
        upsert_daily,
    ),
    "weekly": (
        {"A股": fetch_a_weekly, "港股": fetch_hk_weekly, "美股": fetch_us_weekly},
        upsert_weekly,
    ),
    "monthly": (
        {"A股": fetch_a_monthly, "港股": fetch_hk_monthly, "美股": fetch_us_monthly},
        upsert_monthly,
    ),
    "15min": (
        {"A股": fetch_a_15min, "港股": fetch_hk_15min, "美股": fetch_us_15min},
        upsert_15min,
    ),
    "1h": (
        {"A股": fetch_a_1h, "港股": fetch_hk_1h, "美股": fetch_us_1h},
        upsert_1h,
    ),
}


def fetch_one(code: str, market: str, periods: list[str] | None = None):
    """拉取单个标的的指定周期数据并写入数据库"""
    if periods is None:
        periods = ["daily", "weekly", "monthly"]

    conn = get_conn()
    for period in periods:
        if period not in _FETCHER_MAP:
            print(f"⚠️  不支持的周期: {period}")
            continue
        fetcher_dict, upsert_fn = _FETCHER_MAP[period]
        fetch_fn = fetcher_dict.get(market)
        if fetch_fn is None:
            print(f"⚠️  市场 {market} 不支持周期 {period}")
            continue
        try:
            print(f"  拉取 {code} {period}...", end=" ")
            df = fetch_fn(code)
            rows = upsert_fn(conn, code, df)
            log_fetch(conn, code, period, rows)
            print(f"✅ {rows} 行")
        except Exception as e:
            log_fetch(conn, code, period, 0, "failed", str(e))
            print(f"❌ {str(e)[:80]}")
    conn.close()
