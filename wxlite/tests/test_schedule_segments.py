from datetime import date, time

import pytest

from amc_wx_lite.schedule_segments import (
    DateSegments,
    TimeSegments,
    duration_from_fields,
)


def test_date_segments_keep_real_calendar_boundaries() -> None:
    state = DateSegments(date(2024, 2, 29))
    assert state.label("day") == "dzień 29"
    assert state.label("month") == "miesiąc luty"
    assert state.adjust("year", 1).value == date(2025, 2, 28)
    assert DateSegments(date(2026, 1, 31)).adjust("month", 1).value == date(2026, 2, 28)
    assert DateSegments(date(2026, 4, 30)).adjust("day", 1).value == date(2026, 4, 1)


def test_time_segments_wrap_2359_without_invalid_values() -> None:
    state = TimeSegments(time(23, 59))
    assert state.adjust("hour", 1).value == time(0, 59)
    assert state.adjust("minute", 1).value == time(23, 0)
    assert state.label("hour") == "godzina 23"
    assert state.label("minute") == "minuty 59"


def test_digit_prefix_waits_only_when_another_valid_digit_can_follow() -> None:
    date_state = DateSegments(date(2026, 10, 18))
    assert date_state.may_extend("day", "1")
    assert not date_state.may_extend("day", "4")
    assert date_state.may_extend("month", "1")
    assert not date_state.may_extend("month", "2")
    assert date_state.may_extend("year", "202")
    assert not date_state.may_extend("year", "2026")

    time_state = TimeSegments(time(9, 25))
    assert time_state.may_extend("hour", "2")
    assert not time_state.may_extend("hour", "3")
    assert time_state.may_extend("minute", "5")
    assert not time_state.may_extend("minute", "6")


def test_numeric_replacement_rejects_invalid_date_and_time() -> None:
    assert DateSegments(date(2024, 2, 1)).replace_segment("day", 29).value.day == 29
    with pytest.raises(ValueError):
        DateSegments(date(2025, 2, 1)).replace_segment("day", 29)
    with pytest.raises(ValueError):
        TimeSegments(time(0, 0)).replace_segment("minute", 60)


def test_empty_duration_hours_mean_zero_but_empty_whole_duration_is_rejected() -> None:
    assert duration_from_fields("", 25) == 25
    assert duration_from_fields("2", 5) == 125
    with pytest.raises(ValueError, match="Podaj długość"):
        duration_from_fields("", 0)
    with pytest.raises(ValueError, match="liczbą"):
        duration_from_fields("dwie", 5)

