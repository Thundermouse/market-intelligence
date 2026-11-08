#!/usr/bin/env python3
"""CLI: 拉取多周期行情数据并存入数据库"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from market_data.pipeline import fetch_one


def main():
    parser = argparse.ArgumentParser(description="Market Data Fetcher")
    parser.add_argument("--code", required=True, help="证券代码")
    parser.add_argument("--market", default="A股", choices=["A股", "美股", "港股"])
    parser.add_argument("--periods", nargs="+",
                        default=["daily", "weekly", "monthly"],
                        choices=["daily", "weekly", "monthly", "15min", "1h"])
    args = parser.parse_args()

    print(f"🚀 拉取 {args.market} {args.code} 周期: {args.periods}")
    fetch_one(args.code, args.market, args.periods)
    print("✅ Done")


if __name__ == "__main__":
    main()
