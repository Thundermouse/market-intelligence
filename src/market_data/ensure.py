"""数据就绪检查：校验历史长度 + 新鲜度，自动拉取缺失/过期数据"""
from datetime import date, datetime

from .db import get_conn
from .pipeline import fetch_one

# 各周期的历史数据量要求（自然日，约等于对应交易日数）
PERIOD_HISTORY_DAYS = {
    "15min": 10,      # 7 个交易日 ≈ 10 自然日
    "1h": 90,         # 3 个月
    "daily": 180,     # 6 个月
    "weekly": 1095,   # 3 年
    "monthly": 3650,  # 10 年
}

# 各周期的新鲜度阈值（天）
PERIOD_FRESHNESS_DAYS = {
    "15min": 2,
    "1h": 2,
    "daily": 2,
    "weekly": 8,
    "monthly": 35,
}

# 分钟级数据受 API 限制（约 50 天），仅校验新鲜度，不强制历史长度
MINUTE_PERIODS = {"15min", "1h"}

_TABLE_MAP = {
    "daily": ("daily_ohlcv", "trade_date"),
    "15min": ("kline_15min", "dt"),
    "1h": ("kline_1h", "dt"),
    "weekly": ("kline_weekly", "week_start"),
    "monthly": ("kline_monthly", "month"),
}


def _parse_date(date_str: str) -> date:
    if " " in date_str:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def check_period(conn, code: str, period: str):
    """
    检查某标的某周期数据是否满足要求。
    返回: (ok, message, latest_date, days_covered)
    """
    today = date.today()
    table, date_col = _TABLE_MAP[period]
    cursor = conn.execute(
        f"SELECT MIN({date_col}), MAX({date_col}), COUNT(*) FROM {table} WHERE security_code = ?",
        (code,),
    )
    min_date_str, max_date_str, count = cursor.fetchone()

    if count == 0 or not min_date_str:
        return False, "无数据", None, 0

    min_date = _parse_date(min_date_str)
    max_date = _parse_date(max_date_str)
    days_covered = (max_date - min_date).days

    # 新鲜度校验（所有周期）
    freshness = (today - max_date).days
    threshold = PERIOD_FRESHNESS_DAYS[period]
    if freshness > threshold:
        return False, f"数据过期（{freshness}天 > 阈值{threshold}天）", max_date, days_covered

    # 分钟级：API 历史有限，不强制历史长度
    if period in MINUTE_PERIODS:
        return True, f"OK（{days_covered}天，API上限）", max_date, days_covered

    # 日/周/月线：历史数据量校验
    required_days = PERIOD_HISTORY_DAYS[period]
    if days_covered < required_days:
        return False, f"历史数据不足（{days_covered}天 < 需要{required_days}天）", max_date, days_covered

    return True, "OK", max_date, days_covered


def ensure_one(code: str, market: str, periods: list[str] | None = None):
    """
    确保单个标的数据就绪：
      - 无数据 → 全量初始化
      - 不满足要求 → 补丁拉取
      - 已满足 → 跳过
    """
    if periods is None:
        periods = ["daily", "weekly", "monthly", "15min", "1h"]

    conn = get_conn()
    results = {}
    for period in periods:
        ok, msg, latest, covered = check_period(conn, code, period)
        if ok:
            results[period] = (True, f"✅ 已有数据（{covered}天，最新{latest}）")
            print(f"  {period:8s}: ✅ 已有 {covered} 天数据，最新 {latest}")
        else:
            action = "初始化" if covered == 0 else "补丁"
            print(f"  {period:8s}: ⚠️  {msg}，执行{action}拉取...")
            try:
                fetch_one(code, market, [period])
                ok2, msg2, latest2, covered2 = check_period(conn, code, period)
                if ok2:
                    results[period] = (True, f"✅ {action}成功（{covered2}天，最新{latest2}）")
                    print(f"  {period:8s}: ✅ {action}后验证通过")
                else:
                    results[period] = (False, f"❌ {action}后仍不满足: {msg2}")
                    print(f"  {period:8s}: ❌ {action}后仍不满足: {msg2}")
            except Exception as e:
                results[period] = (False, f"❌ 拉取失败: {str(e)[:80]}")
                print(f"  {period:8s}: ❌ 拉取失败: {str(e)[:80]}")
    conn.close()
    return results


def ensure_batch(codes: list[str], market: str, periods: list[str] | None = None):
    """批量确保多个标的数据就绪"""
    all_ok = True
    summary = {}
    for code in codes:
        print(f"\n📦 {market} {code}:")
        results = ensure_one(code, market, periods)
        summary[code] = results
        if not all(ok for ok, _ in results.values()):
            all_ok = False
    return all_ok, summary
