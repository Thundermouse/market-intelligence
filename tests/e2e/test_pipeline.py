"""
端到端测试：行情数据管线全流程验证。

覆盖完整功能（非单元测试）：
  1. A股全周期拉取 → 存储 → 查询 → 就绪校验
  2. 美股全周期拉取（含 DST 时段过滤）→ 存储 → 查询 → 就绪校验
  3. 港股全周期拉取 → 存储 → 查询 → 就绪校验
  4. 数据完整性校验（时段边界、周/月线聚合一致性）
  5. 新股票初始化 / 已有股票补丁 / 达标跳过 三种分支

运行: pytest tests/e2e/test_pipeline.py -v
或:   python tests/e2e/test_pipeline.py
"""
import os
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from market_data.db import get_conn, init_db
from market_data.pipeline import fetch_one
from market_data.ensure import ensure_one, check_period, PERIOD_HISTORY_DAYS, PERIOD_FRESHNESS_DAYS
from market_data.query import query_daily, query_period, check_freshness

# 测试标的
TEST_SYMBOLS = {
    "A股": "600519",    # 贵州茅台
    "美股": "AAPL",      # 苹果
    "港股": "00700",     # 腾讯
}
ALL_PERIODS = ["daily", "weekly", "monthly", "15min", "1h"]

results = {"pass": 0, "fail": 0}


def check(name, condition, detail=""):
    if condition:
        results["pass"] += 1
        print(f"  ✅ {name}")
    else:
        results["fail"] += 1
        print(f"  ❌ {name}  {detail}")


def test_market_full_pipeline(market, code):
    """单市场全流程：拉取 → 查询 → 就绪校验"""
    print(f"\n{'='*60}")
    print(f"📦 {market} {code} 全流程测试")
    print(f"{'='*60}")

    # 1. 拉取全周期
    print("\n[1/4] 拉取全周期数据...")
    fetch_one(code, market, ALL_PERIODS)

    conn = get_conn()

    # 2. 查询验证
    print("\n[2/4] 查询验证...")
    for period in ALL_PERIODS:
        if period == "daily":
            rows = query_daily(conn, code, limit=5)
        else:
            rows = query_period(conn, code, period, limit=5)
        check(f"{period} 查询返回非空", len(rows) > 0, f"返回 {len(rows)} 行")

    # 3. 新鲜度校验
    print("\n[3/4] 新鲜度校验...")
    for period in ["daily", "weekly", "monthly"]:
        result = check_freshness(conn, code, period)
        if result:
            latest, days = result
            threshold = PERIOD_FRESHNESS_DAYS[period]
            check(f"{period} 新鲜度 ≤ {threshold}天", days <= threshold,
                  f"最新{latest}，{days}天前")
        else:
            check(f"{period} 新鲜度", False, "无数据")

    # 4. 就绪校验
    print("\n[4/4] 就绪校验...")
    for period in ALL_PERIODS:
        ok, msg, latest, covered = check_period(conn, code, period)
        check(f"{period} 就绪", ok, msg)

    conn.close()


def test_us_session_filter():
    """美股时段过滤：1h/15min 不得包含盘前盘后数据"""
    print(f"\n{'='*60}")
    print(f"🇺🇸 美股时段过滤测试（DST 自动处理）")
    print(f"{'='*60}")

    code = TEST_SYMBOLS["美股"]
    conn = get_conn()

    for period in ["1h", "15min"]:
        table = f"kline_{period}"
        cursor = conn.execute(f"SELECT dt FROM {table} WHERE security_code = ?", (code,))
        bad = 0
        for (dt_str,) in cursor.fetchall():
            bj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            ny = bj.replace(tzinfo=ZoneInfo("Asia/Shanghai")).astimezone(ZoneInfo("America/New_York"))
            mins = ny.hour * 60 + ny.minute
            if mins < 570 or mins >= 960:  # 9:30-16:00 ET
                bad += 1
        check(f"{period} 无盘前/盘后 bar", bad == 0, f"异常 bar 数: {bad}")

    conn.close()


def test_a_share_session():
    """A股时段校验：1h/15min 必须在 9:30-11:30 / 13:00-15:00"""
    print(f"\n{'='*60}")
    print(f"🇨🇳 A股时段校验")
    print(f"{'='*60}")

    code = TEST_SYMBOLS["A股"]
    conn = get_conn()

    for period in ["1h", "15min"]:
        table = f"kline_{period}"
        cursor = conn.execute(f"SELECT dt FROM {table} WHERE security_code = ?", (code,))
        bad = 0
        for (dt_str,) in cursor.fetchall():
            bj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            mins = bj.hour * 60 + bj.minute
            # 9:30-11:30 (570-690) 或 13:00-15:00 (780-900)
            if not ((570 <= mins <= 690) or (780 <= mins <= 900)):
                bad += 1
        check(f"{period} 时段正确", bad == 0, f"异常 bar 数: {bad}")

    conn.close()


def test_weekly_aggregation():
    """周线聚合一致性：周线 OHLC 应等于当周日线聚合"""
    from datetime import date, timedelta
    print(f"\n{'='*60}")
    print(f"📊 周线聚合一致性测试")
    print(f"{'='*60}")

    for market, code in TEST_SYMBOLS.items():
        conn = get_conn()
        # 取最新周线
        cursor = conn.execute("""
            SELECT week_start, open, high, low, close
            FROM kline_weekly WHERE security_code = ?
            ORDER BY week_start DESC LIMIT 1
        """, (code,))
        row = cursor.fetchone()
        if not row:
            check(f"{market} 周线存在", False, "无周线数据")
            conn.close()
            continue
        week_start, w_open, w_high, w_low, w_close = row

        # 根据 week_start 推算该周周一~周五
        ws = date.fromisoformat(week_start)
        monday = ws - timedelta(days=ws.weekday())
        friday = monday + timedelta(days=4)

        # 取该周内日线
        cursor = conn.execute("""
            SELECT trade_date, open, high, low, close
            FROM daily_ohlcv
            WHERE security_code = ? AND trade_date >= ? AND trade_date <= ?
            ORDER BY trade_date
        """, (code, monday.isoformat(), friday.isoformat()))
        dailies = cursor.fetchall()
        conn.close()

        if not dailies:
            check(f"{market} 周线对应日线", False,
                  f"周线 {week_start} 该周({monday}~{friday})无日线")
            continue

        d_open = dailies[0][1]
        d_high = max(r[2] for r in dailies)
        d_low = min(r[3] for r in dailies)
        d_close = dailies[-1][4]

        check(f"{market} 周线开盘=当周首日开盘", abs(w_open - d_open) < 0.01,
              f"周线O={w_open} 首日O={d_open}")
        check(f"{market} 周线最高=当周最高", abs(w_high - d_high) < 0.01,
              f"周线H={w_high} 当周H={d_high}")
        check(f"{market} 周线最低=当周最低", abs(w_low - d_low) < 0.01,
              f"周线L={w_low} 当周L={d_low}")
        check(f"{market} 周线收盘=当周末日收盘", abs(w_close - d_close) < 0.01,
              f"周线C={w_close} 末日C={d_close}")


def test_ensure_branches():
    """ensure_data 三分支：已有达标→跳过 / 过期→补丁 / 无数据→初始化"""
    print(f"\n{'='*60}")
    print(f"🔄 ensure_data 分支测试")
    print(f"{'='*60}")

    market = "A股"
    code = TEST_SYMBOLS[market]

    # 已有达标 → 跳过（应直接 OK）
    print("\n[1/3] 已有达标 → 应跳过...")
    results = ensure_one(code, market, ["daily"])
    ok, msg = results["daily"]
    check("已有数据跳过", ok and "已有" in msg, msg)

    # 人为制造过期 → 补丁
    # 注意：不能用 UPDATE 把多行改成同一日期（违反 UNIQUE 约束），
    # 改为先清空再插入两条不同日期的过期数据，使 covered>0 走"补丁"分支
    print("\n[2/3] 模拟过期 → 应补丁...")
    conn = get_conn()
    conn.execute("DELETE FROM daily_ohlcv WHERE security_code = ?", (code,))
    conn.executemany("""
        INSERT INTO daily_ohlcv
        (security_code, trade_date, open, high, low, close, volume, amount, turnover, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (code, "2020-01-01", 100.0, 101.0, 99.0, 100.5, 1000, 100500.0, 0.5, "test"),
        (code, "2020-01-02", 100.5, 102.0, 100.0, 101.5, 1200, 121800.0, 0.6, "test"),
    ])
    conn.commit()
    conn.close()
    results = ensure_one(code, market, ["daily"])
    ok, msg = results["daily"]
    check("过期数据补丁", ok and "补丁" in msg, msg)

    # 无数据 → 初始化
    print("\n[3/3] 模拟无数据 → 应初始化...")
    conn = get_conn()
    conn.execute("DELETE FROM daily_ohlcv WHERE security_code = ?", (code,))
    conn.commit()
    conn.close()
    results = ensure_one(code, market, ["daily"])
    ok, msg = results["daily"]
    check("无数据初始化", ok and "初始化" in msg, msg)


def main():
    print("=" * 60)
    print("🚀 行情数据管线 端到端测试")
    print(f"📅 测试日期: {date.today()}")
    print("=" * 60)

    # 确保 DB 初始化
    init_db()

    # 三市场全流程
    for market, code in TEST_SYMBOLS.items():
        test_market_full_pipeline(market, code)

    # 时段过滤
    test_us_session_filter()
    test_a_share_session()

    # 聚合一致性
    test_weekly_aggregation()

    # ensure 分支
    test_ensure_branches()

    # 汇总
    print(f"\n{'='*60}")
    print(f"📋 测试汇总: ✅ {results['pass']} 通过, ❌ {results['fail']} 失败")
    print(f"{'='*60}")
    sys.exit(0 if results["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
