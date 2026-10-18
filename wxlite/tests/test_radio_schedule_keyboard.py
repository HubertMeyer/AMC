"""Keyboard contract of the native radio schedule list."""

from __future__ import annotations

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_gui_logic import install_wx_stub

install_wx_stub()

from amc_wx_lite.radio_schedule_dialogs import (
    _full_schedule_information,
    _short_schedule_information,
)


SOURCE = Path(__file__).parents[1] / "amc_wx_lite" / "radio_schedule_dialogs.py"


def test_schedule_list_receives_space_directly_and_through_the_dialog_hook() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "self.Bind(wx.EVT_CHAR_HOOK, self._on_key)" in source
    assert "self.schedule_list.Bind(wx.EVT_KEY_DOWN, self._on_key)" in source
    assert "event_object is self.schedule_list" in source
    assert "focus_on_list and code == wx.WXK_SPACE" in source
    assert "self._toggle(event)" in source


def test_schedule_toggle_keeps_an_intentional_spoken_state() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert 'state = "włączony" if updated["enabled"] else "wyłączony"' in source
    assert 'success_message=f"{_display_name(updated)}, {state}"' in source


def test_schedule_list_left_and_right_have_read_only_information_actions() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "focus_on_list and code == wx.WXK_LEFT" in source
    assert "_short_schedule_information(selected)" in source
    assert "focus_on_list and code == wx.WXK_RIGHT" in source
    assert "_full_schedule_information(selected)" in source


def test_ctrl_enter_is_not_reassigned_and_ctrl_d_opens_disabled_copy_editor() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert 'code in (ord("D"), ord("d"))' in source
    duplicate = source[source.index("    def _duplicate"):source.index("    def _toggle")]
    assert "copy = duplicate_schedule" in duplicate
    assert "existing=copy" in duplicate
    assert "dialog.ShowModal()" in duplicate
    assert "candidate = [*self._schedules, copy]" in duplicate
    assert "WXK_CONTROL" not in source


def test_segmented_controls_have_only_user_facing_names_and_expected_keys() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "_SegmentedDateControl" in source
    assert "_SegmentedTimeControl" in source
    assert "DateSegments" in source and "TimeSegments" in source
    assert "wx.WXK_LEFT" in source and "wx.WXK_RIGHT" in source
    assert "wx.WXK_UP" in source and "wx.WXK_DOWN" in source
    assert "control.SetName(self._state.label(segment))" in source
    for leaked in ("DateSegments(", "TimeSegments(", "segment='", "value="):
        assert f"SetName({leaked}" not in source


def test_schedule_information_is_short_on_left_and_complete_on_right() -> None:
    schedule = {
        "name": "Poranek",
        "stationName": "Radio Test",
        "nextStartUtcTicks": 639_271_800_000_000_000,
        "durationMinutes": 85,
        "recurrence": "Daily",
        "activeDays": [],
        "recordingFormat": "Mp3",
        "outputFolder": r"D:\Nagrania",
        "enabled": True,
    }
    short = _short_schedule_information(schedule)
    assert short.startswith("włączony, najbliższy termin ")
    assert "Poranek" not in short and "D:\\Nagrania" not in short
    full = _full_schedule_information(schedule)
    for expected in (
        "nazwa Poranek",
        "źródło Radio Test",
        "codziennie",
        "godzina ",
        "długość 1 godzina 25 minut",
        "format MP3",
        r"folder D:\Nagrania",
    ):
        assert expected in full


def test_new_schedule_updates_weekday_until_user_edits_days() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "self._days_user_changed = False" in source
    assert "self.days.Bind(wx.EVT_CHECKLISTBOX, self._on_days_changed)" in source
    assert "if self._existing is not None or self._days_user_changed" in source
    assert "self.days.Check(index, index == wanted)" in source
