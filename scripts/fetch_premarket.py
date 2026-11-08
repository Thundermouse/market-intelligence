#!/usr/bin/env python3
"""CLI: 美股盘前行情数据抓取（临时存入 premarket_data 表）"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from market_data.db import get_conn
from market_data.premarket import fetch_premarket, save_premarket, cleanup_old_premarket


def main():
    parser = argparse.ArgumentParser(description="US Premarket Data Fetcher")
    parser.add_argument("--symbols", nargs="+", required=True, help="美股代码列表")
    parser.add_argument("--cleanup-days", type=int, default=1, help="清理 N 天前数据")
    args = parser.parse_args()

    conn = get_conn()

    deleted = cleanup_old_premarket(conn, args.cleanup_days)
    if deleted > 0:
        print(f"🧹 清理旧盘前数据: {deleted} 行")

    for symbol in args.symbols:
        print(f"  拉取盘前 {symbol}...", end=" ")
        data = fetch_premarket(symbol)
        if data:
            save_premarket(conn, data)
            print(f"✅ 盘前价={data['premarket_price']:.2f} 涨跌={data['change_percent']:.2f}%")
        else:
            print("❌ 无数据")

    conn.close()
    print("✅ Done")


if __name__ == "__main__":
    main()
