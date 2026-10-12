"""Structural contract for the native, keyboard-oriented settings window."""

from __future__ import annotations

from pathlib import Path


SOURCE = Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"


def test_settings_have_real_native_pages_and_explicit_accessible_names() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "self.notebook = wx.Notebook(self)" in source
    assert 'self.notebook.SetName("Kategorie ustawień")' in source
    assert 'self.notebook.AddPage(general, "Ogólne", select=True)' in source
    assert 'self.notebook.AddPage(messages, "Komunikaty")' in source
    assert 'self.silence.SetName("Dodatkowa cisza po naturalnym końcu utworu")' in source
    assert 'self.tempo.SetName("Sposób przeliczania zmienionego tempa")' in source


def test_enter_save_has_one_short_confirmation_and_reconfigures_the_host() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert 'save.SetName("Zapisz ustawienia")' in source
    assert 'save.SetDefault()' in source
    assert 'self.announcer.say("Zapisano ustawienia")' in source
    assert 'client.configure_audio(' in source


def test_all_exposed_choices_use_intentional_user_facing_labels() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "choices=[TEMPO_LABELS[value] for value in self._tempo_values]" in source
    assert "session_options.inter_track_silence_label(value)" in source
    assert "STATE_POSITION_LABELS" in source
