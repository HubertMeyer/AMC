"""Kontrakt Ctrl+O: plik, świadomy wybór i anulowanie bez uruchamiania wx."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_gui_logic import install_wx_stub
install_wx_stub()
from amc_wx_lite import gui, menu_model
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.shortcuts import Action, Chord, describe, keyboard_help_announcement, resolve

REAL_IMPORT_DIALOG = gui.PodcastOpmlImportDialog


@pytest.fixture
def import_context(monkeypatch):
    calls = []
    messages = []
    paths = []
    picker_options = {}
    decisions = SimpleNamespace(picker=True, selection=True)
    path = "subscriptions.csv"
    entries = [
        {"title": "Kanał Alfa", "label": "Kanał Alfa, YouTube", "feedUrl": "https://www.youtube.com/channel/UCaaaaaaaaaaaaaaaaaaaaaa"},
        {"title": "Kanał Beta", "label": "Kanał Beta, YouTube", "feedUrl": "https://www.youtube.com/channel/UCbbbbbbbbbbbbbbbbbbbbbb"},
    ]

    class Picker:
        def __init__(self, *args, **kwargs):
            picker_options.update(kwargs)
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass
        def ShowModal(self):
            return gui.wx.ID_OK if decisions.picker else gui.wx.ID_CANCEL
        def GetPath(self):
            return path

    class Selection(Picker):
        def __init__(self, parent, values):
            assert values == entries
        def ShowModal(self):
            return gui.wx.ID_OK if decisions.selection else gui.wx.ID_CANCEL
        selected_feed_urls = [entries[1]["feedUrl"]]

    class Client:
        def inspect_podcast_opml(self, value):
            paths.append(value)
            return {"entries": entries}
        def import_podcast_opml(self, value, selected):
            calls.append((value, selected))
            return {"imported": 1, "failed": 0}

    class Runner:
        def submit(self, key, work, done, failed):
            # Do not swallow assertion errors as fake host errors.
            done(work())

    monkeypatch.setattr(gui.wx, "FD_OPEN", 1)
    monkeypatch.setattr(gui.wx, "FD_FILE_MUST_EXIST", 2)
    monkeypatch.setattr(gui.wx, "FileDialog", Picker)
    monkeypatch.setattr(gui, "PodcastOpmlImportDialog", Selection)
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.PODCASTS, sessions={SessionId.PODCASTS: SimpleNamespace(view=None)}),
        _podcast_opml_pending=False,
        client=Client(), runner=Runner(),
        announcer=SimpleNamespace(say=messages.append),
        status_field=SimpleNamespace(SetLabel=messages.append),
        status_bar=SimpleNamespace(show=messages.append),
    )
    return SimpleNamespace(frame=frame, options=picker_options, decisions=decisions,
                           calls=calls, paths=paths, entries=entries, messages=messages)


def test_ctrl_o_picker_exposes_subscription_formats_and_imports_only_selection(import_context):
    context = import_context
    gui.LiteFrame._import_podcast_opml(context.frame)
    wildcard = context.options["wildcard"]
    for extension in ("*.opml", "*.xml", "*.csv", "*.zip", "*.json", "*.db"):
        assert extension in wildcard
    assert "YouTube" in context.options["message"]
    assert context.calls == [("subscriptions.csv", [context.entries[1]["feedUrl"]])]
    assert not context.frame._podcast_opml_pending
    assert any("źródła" in text.casefold() for text in context.messages)


@pytest.mark.parametrize("stage", ["picker", "selection"])
def test_cancel_import_never_writes_sources(import_context, stage):
    context = import_context
    setattr(context.decisions, stage, False)
    gui.LiteFrame._import_podcast_opml(context.frame)
    assert context.calls == []
    assert context.paths == ([] if stage == "picker" else ["subscriptions.csv"])
    assert not context.frame._podcast_opml_pending


def test_subscription_import_preserves_ctrl_o_identity_on_every_command_surface():
    action = Action.IMPORT_PODCAST_OPML
    chord = Chord("O", ctrl=True)
    assert resolve(chord, player_view=False, radio_session=False, podcast_session=True) is action
    menu = next(item for group in menu_model.menus_for_session(SessionId.PODCASTS)
                for item in group.items if item.action is action)
    palette = next(item for item in entries_for_session(SessionId.PODCASTS) if item.action is action)
    help_text = dict(describe("Podcasty i YouTube", {action}))["Ctrl+O (Podcasty i YouTube)"]
    for text in (menu.label, palette.label, help_text,
                 keyboard_help_announcement(chord, action, "Podcasty i YouTube")):
        assert "YouTube" in text
        assert "OPML" in text.replace("&", "")
    assert menu.shortcut == "Ctrl+O"
    assert not menu.accelerator


def test_subscription_import_has_translated_controls_and_command_description():
    from amc_wx_lite import i18n
    try:
        i18n.configure("en")
        assert i18n.ui_text("Importuj podcasty i kanały YouTube z pliku") == "Import podcasts and YouTube channels from a file"
        assert i18n.ui_text("Podcasty i kanały YouTube do importu") == "Podcasts and YouTube channels to import"
        assert "Takeout" in i18n.command_description(Action.IMPORT_PODCAST_OPML.value, "")
    finally:
        i18n.configure("pl")


def test_english_import_translates_real_picker_and_selection_state(import_context):
    from amc_wx_lite import i18n
    try:
        i18n.configure("en")
        gui.LiteFrame._import_podcast_opml(import_context.frame)
        assert import_context.options["message"] == "Import podcasts and YouTube channels from a file"
        assert "Subscription files" in import_context.options["wildcard"]
        # Use the real dialog class, not the selection seam installed above.
        dialog = object.__new__(REAL_IMPORT_DIALOG)
        dialog._entries = import_context.entries
        dialog._included = [True, False]
        assert dialog._label(0) == "Kanał Alfa, YouTube, selected"
        assert dialog._label(1) == "Kanał Beta, YouTube, not selected"
    finally:
        i18n.configure("pl")
