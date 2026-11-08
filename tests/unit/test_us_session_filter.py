"""
美股常规交易时段过滤单元测试。

不依赖网络、不读写数据库，直接对 _filter_us_regular_session 输入 mock DataFrame 验证。
覆盖 EDT/EST 转换、跨午夜、盘前盘后、边界时刻、空 DataFrame 等场景。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pandas as pd
import pytest
from zoneinfo import ZoneInfo

from market_data.fetchers.us_stock import _filter_us_regular_session


def _make_df(timestamps: list[str]) -> pd.DataFrame:
    """用北京时间字符串构造待过滤 DataFrame。"""
    return pd.DataFrame({"value": range(len(timestamps))}, index=pd.to_datetime(timestamps))


class TestUsSessionFilter:
    # ------------------------------------------------------------------
    # 1. 常规交易时段内的 bar 被保留（夏令时 EDT）
    # ------------------------------------------------------------------
    def test_keep_regular_hours_edt(self):
        """EDT: 北京时间 21:30 ~ 次日 04:00 对应 ET 09:30 ~ 16:00"""
        ts = [
            "2023-07-10 21:30:00",  # ET 09:30 EDT
            "2023-07-10 22:00:00",  # ET 10:00 EDT
            "2023-07-11 00:00:00",  # ET 12:00 EDT
            "2023-07-11 03:59:00",  # ET 15:59 EDT
        ]
        df = _make_df(ts)
        result = _filter_us_regular_session(df)
        assert len(result) == 4
        assert list(result.index) == list(pd.to_datetime(ts))

    # ------------------------------------------------------------------
    # 2. 常规交易时段内的 bar 被保留（冬令时 EST）
    # ------------------------------------------------------------------
    def test_keep_regular_hours_est(self):
        """EST: 北京时间 22:30 ~ 次日 05:00 对应 ET 09:30 ~ 16:00"""
        ts = [
            "2023-01-10 22:30:00",  # ET 09:30 EST
            "2023-01-10 23:00:00",  # ET 10:00 EST
            "2023-01-11 01:00:00",  # ET 12:00 EST
            "2023-01-11 04:59:00",  # ET 15:59 EST
        ]
        df = _make_df(ts)
        result = _filter_us_regular_session(df)
        assert len(result) == 4
        assert list(result.index) == list(pd.to_datetime(ts))

    # ------------------------------------------------------------------
    # 3. 盘前 / 盘后 bar 被过滤掉
    # ------------------------------------------------------------------
    def test_filter_premarket(self):
        """EDT 盘前：北京时间 21:00 对应 ET 09:00"""
        df = _make_df(["2023-07-10 21:00:00"])
        result = _filter_us_regular_session(df)
        assert len(result) == 0

    def test_filter_afterhours(self):
        """EDT 盘后：北京时间 05:00 对应 ET 17:00"""
        df = _make_df(["2023-07-11 05:00:00"])
        result = _filter_us_regular_session(df)
        assert len(result) == 0

    def test_filter_mixed_premarket_afterhours(self):
        """混合盘前、盘中、盘后，仅保留盘中"""
        ts = [
            "2023-07-10 20:00:00",  # ET 08:00 盘前
            "2023-07-10 21:30:00",  # ET 09:30 盘中
            "2023-07-11 04:00:00",  # ET 16:00 盘后（边界，被过滤）
            "2023-07-11 06:00:00",  # ET 18:00 盘后
        ]
        df = _make_df(ts)
        result = _filter_us_regular_session(df)
        assert len(result) == 1
        assert result.index[0] == pd.Timestamp("2023-07-10 21:30:00")

    # ------------------------------------------------------------------
    # 4. 夏令时 / 冬令时边界
    # ------------------------------------------------------------------
    def test_dst_start_boundary(self):
        """2023年夏令时开始：3月12日，首个交易日 3月13日"""
        ts = [
            "2023-03-13 21:30:00",  # ET 09:30 EDT
            "2023-03-14 04:00:00",  # ET 16:00 EDT
        ]
        df = _make_df(ts)
        result = _filter_us_regular_session(df)
        assert len(result) == 1
        assert result.index[0] == pd.Timestamp("2023-03-13 21:30:00")

    def test_dst_end_boundary(self):
        """2023年夏令时结束：11月5日，首个交易日 11月6日"""
        ts = [
            "2023-11-06 22:30:00",  # ET 09:30 EST
            "2023-11-07 05:00:00",  # ET 16:00 EST
        ]
        df = _make_df(ts)
        result = _filter_us_regular_session(df)
        assert len(result) == 1
        assert result.index[0] == pd.Timestamp("2023-11-06 22:30:00")

    # ------------------------------------------------------------------
    # 5. 跨午夜情况（北京时间 21:30~次日 04:00/05:00）
    # ------------------------------------------------------------------
    def test_cross_midnight_edt(self):
        """EDT 跨午夜：同一 ET 交易日分布在北京时间两天"""
        ts = [
            "2023-07-10 21:30:00",  # 北京 7月10日 -> ET 7月10日 09:30
            "2023-07-11 01:00:00",  # 北京 7月11日 -> ET 7月10日 13:00
            "2023-07-11 03:59:00",  # 北京 7月11日 -> ET 7月10日 15:59
        ]
        df = _make_df(ts)
        result = _filter_us_regular_session(df)
        assert len(result) == 3

    def test_cross_midnight_est(self):
        """EST 跨午夜：同一 ET 交易日分布在北京时间两天"""
        ts = [
            "2023-01-10 22:30:00",  # 北京 1月10日 -> ET 1月10日 09:30
            "2023-01-11 01:00:00",  # 北京 1月11日 -> ET 1月10日 12:00
            "2023-01-11 04:59:00",  # 北京 1月11日 -> ET 1月10日 15:59
        ]
        df = _make_df(ts)
        result = _filter_us_regular_session(df)
        assert len(result) == 3

    # ------------------------------------------------------------------
    # 6. 精确边界时刻
    # ------------------------------------------------------------------
    def test_exact_open_930_kept(self):
        """ET 09:30 整点应保留"""
        df = _make_df(["2023-07-10 21:30:00"])  # EDT 09:30
        result = _filter_us_regular_session(df)
        assert len(result) == 1

    def test_exact_close_1600_filtered(self):
        """ET 16:00 整点应被过滤（minutes < 960）"""
        df = _make_df(["2023-07-11 04:00:00"])  # EDT 16:00
        result = _filter_us_regular_session(df)
        assert len(result) == 0

    def test_one_minute_before_open_filtered(self):
        """ET 09:29 应被过滤"""
        df = _make_df(["2023-07-10 21:29:00"])  # EDT 09:29
        result = _filter_us_regular_session(df)
        assert len(result) == 0

    def test_one_minute_before_close_kept(self):
        """ET 15:59 应保留"""
        df = _make_df(["2023-07-11 03:59:00"])  # EDT 15:59
        result = _filter_us_regular_session(df)
        assert len(result) == 1

    # ------------------------------------------------------------------
    # 7. 空 DataFrame
    # ------------------------------------------------------------------
    def test_empty_dataframe(self):
        df = pd.DataFrame({"value": []}, index=pd.DatetimeIndex([], dtype="datetime64[ns]"))
        result = _filter_us_regular_session(df)
        assert len(result) == 0
        assert isinstance(result.index, pd.DatetimeIndex)

    # ------------------------------------------------------------------
    # 8. 防御性：index 已经带时区时应抛出 TypeError
    # ------------------------------------------------------------------
    def test_already_tz_aware_raises(self):
        df = pd.DataFrame(
            {"value": [1]},
            index=pd.DatetimeIndex(["2023-07-10 21:30:00"]).tz_localize("UTC"),
        )
        with pytest.raises(TypeError):
            _filter_us_regular_session(df)
