"""Keyboard contract of the native radio schedule list."""

from __future__ import annotations

from pathlib import Path


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
