import pandas as pd
import pytest

from market_data.fetchers.us_stock import _filter_us_regular_session


@pytest.mark.parametrize(
    ("beijing_times", "expected_regular_session_times"),
    [
        (
            [
                "2024-07-01 20:00:00",
                "2024-07-01 21:29:00",
                "2024-07-01 21:30:00",
                "2024-07-02 03:59:00",
                "2024-07-02 04:00:00",
            ],
            ["2024-07-01 21:30:00", "2024-07-02 03:59:00"],
        ),
        (
            [
                "2024-01-02 20:00:00",
                "2024-01-02 22:29:00",
                "2024-01-02 22:30:00",
                "2024-01-03 04:59:00",
                "2024-01-03 05:00:00",
            ],
            ["2024-01-02 22:30:00", "2024-01-03 04:59:00"],
        ),
    ],
    ids=["夏令时", "冬令时"],
)
def test_filter_us_regular_session_boundaries(
    beijing_times, expected_regular_session_times
):
    df = pd.DataFrame(
        {"close": range(len(beijing_times))},
        index=pd.DatetimeIndex(beijing_times, name="dt"),
    )

    filtered = _filter_us_regular_session(df)

    expected_index = pd.DatetimeIndex(expected_regular_session_times, name="dt")
    pd.testing.assert_index_equal(filtered.index, expected_index)
