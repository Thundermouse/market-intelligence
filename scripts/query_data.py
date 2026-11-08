#!/usr/bin/env python3
"""CLI: 从数据库查询多周期行情数据"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from market_data.db import get_conn
from market_data.query import query_daily, query_period, query_premarket, check_freshness


def main():
    parser = argparse.ArgumentParser(description="Market Data Query")
    parser.add_argument("--code", required=True, help="证券代码")
    parser.add_argument("--period", default="daily",
                        choices=["daily", "15min", "1h", "weekly", "monthly", "premarket"])
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    conn = get_conn()

    if args.period == "premarket":
        data = query_premarket(conn, args.code)
        print(f"盘前数据: {data}" if data else "无盘前数据")
    elif args.period == "daily":
        rows = query_daily(conn, args.code, args.limit)
        print(f"日线（最近 {len(rows)} 条）:")
        for r in rows:
            print(f"  {r[0]}  O={r[1]:.2f} H={r[2]:.2f} L={r[3]:.2f} C={r[4]:.2f} V={r[5]}")
    else:
        rows = query_period(conn, args.code, args.period, args.limit)
        print(f"{args.period}（最近 {len(rows)} 条）:")
        for r in rows:
            print(f"  {r[0]}  O={r[1]:.2f} H={r[2]:.2f} L={r[3]:.2f} C={r[4]:.2f} V={r[5]}")

    if args.period in ("daily", "weekly", "monthly"):
        result = check_freshness(conn, args.code, args.period)
        if result:
            latest_date, days = result
            print(f"\n📅 最新数据: {latest_date}（{days} 天前）")
            if days > 2:
                print("⚠️  数据超过 2 天未更新，建议重新拉取")

    conn.close()


if __name__ == "__main__":
    main()
