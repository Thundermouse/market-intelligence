#!/usr/bin/env python3
"""CLI: 检查并确保多周期数据就绪（自动初始化/补丁）"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from market_data.ensure import (
    ensure_batch, PERIOD_HISTORY_DAYS, PERIOD_FRESHNESS_DAYS,
)


def main():
    parser = argparse.ArgumentParser(description="Ensure Market Data Ready")
    parser.add_argument("--codes", nargs="+", required=True, help="证券代码列表")
    parser.add_argument("--market", default="A股", choices=["A股", "美股", "港股"])
    parser.add_argument("--periods", nargs="+",
                        default=["daily", "weekly", "monthly", "15min", "1h"])
    args = parser.parse_args()

    print(f"🔍 确保 {args.market} 数据就绪: {args.codes}")
    print(f"   周期: {args.periods}")
    print(f"   历史数据量要求: {PERIOD_HISTORY_DAYS}")
    print(f"   新鲜度阈值: {PERIOD_FRESHNESS_DAYS}")
    print(f"   分钟级仅校验新鲜度（API 历史上限约 50 天）")
    print()

    all_ok, summary = ensure_batch(args.codes, args.market, args.periods)

    print("\n" + "=" * 60)
    print("📋 汇总:")
    for code, results in summary.items():
        for period, (ok, msg) in results.items():
            print(f"  {code} {period:8s}: {msg}")

    print("\n" + ("✅ 全部就绪" if all_ok else "❌ 部分数据未就绪"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
