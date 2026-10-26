"""Runtime contract for the read-only path control used by Settings."""

from __future__ import annotations

import unittest

try:
    import wx
except ImportError:  # Zwykły runner CI może nie mieć natywnego wxPython.
    wx = None


def test_read_only_path_is_a_real_tab_stop_between_buttons() -> None:
    if wx is None or not getattr(wx, "version", None):
        raise unittest.SkipTest("test wymaga prawdziwego wxPython")
    from amc_wx_lite.accessible_controls import FocusableReadOnlyTextCtrl

    app = wx.GetApp() or wx.App(False)
    frame = wx.Frame(None)
    panel = wx.Panel(frame)
    before = wx.Button(panel, label="Przed polem")
    path = FocusableReadOnlyTextCtrl(panel, value=r"C:\Nagrania")
    path.SetName("Domyślny folder nagrywania radia")
    after = wx.Button(panel, label="Wybierz")
    layout = wx.BoxSizer(wx.VERTICAL)
    for control in (before, path, after):
        layout.Add(control)
    panel.SetSizer(layout)
    frame.Show()
    app.Yield()
    try:
        assert not path.IsEditable()
        assert path.AcceptsFocusFromKeyboard()
        before.SetFocus()
        app.Yield()
        assert before.Navigate()
        app.Yield()
        assert wx.Window.FindFocus() is path
        assert path.Navigate()
        app.Yield()
        assert wx.Window.FindFocus() is after
    finally:
        frame.Destroy()
        app.Yield()


def test_update_page_exposes_named_values_in_keyboard_order() -> None:
    if wx is None or not getattr(wx, "version", None):
        raise unittest.SkipTest("test wymaga prawdziwego wxPython")
    from amc_wx_lite.gui import GeneralPlaybackOptionsDialog
    from amc_wx_lite.podcast_source import PodcastGlobalSettings
    from amc_wx_lite.radio_recording import RadioRecordingPreferences
    from amc_wx_lite.state_store import Options
    from amc_wx_lite.transport_parity import MessagePolicy

    app = wx.GetApp() or wx.App(False)
    frame = wx.Frame(None)
    dialog = GeneralPlaybackOptionsDialog(
        frame,
        Options(),
        RadioRecordingPreferences(),
        True,
        PodcastGlobalSettings(),
        True,
        60,
        True,
        True,
        True,
        MessagePolicy(),
        {
            "available": True,
            "checkAutomatically": True,
            "downloadAutomatically": True,
            "ffmpeg": "FFmpeg jest gotowy",
            "ytDlp": "yt-dlp jest gotowy",
            "message": "Składniki są aktualne.",
        },
        "Testowy — wydania wstępne AMC Test",
        lambda _completed: False,
        {
            "available": False,
            "displayName": "AMC Test",
            "message": "Integracja jest niedostępna.",
            "groups": [],
        },
        lambda: {"success": False},
        r"C:\Nagrania",
        r"C:\Podcasty",
        {},
        lambda _message: None,
    )
    dialog.notebook.SetSelection(5)
    dialog.Show()
    app.Yield()
    try:
        assert not dialog.update_channel.IsEditable()
        assert dialog.update_channel.AcceptsFocusFromKeyboard()
        assert dialog.update_channel.GetName() == "Kanał aktualizacji programu"
        assert dialog.component_ffmpeg_status.GetName() == "Stan składnika FFmpeg"
        assert dialog.component_yt_dlp_status.GetName() == "Stan składnika yt-dlp"

        dialog.update_channel.SetFocus()
        app.Yield()
        assert dialog.update_channel.Navigate()
        app.Yield()
        assert wx.Window.FindFocus() is dialog.component_check_automatically
        assert dialog.component_check_automatically.Navigate()
        app.Yield()
        assert wx.Window.FindFocus() is dialog.component_download_automatically
        assert dialog.component_download_automatically.Navigate()
        app.Yield()
        assert wx.Window.FindFocus() is dialog.component_ffmpeg_status

        assert dialog.values["component_check_automatically"] is True
        assert dialog.values["component_download_automatically"] is True
    finally:
        dialog.Destroy()
        frame.Destroy()
        app.Yield()
