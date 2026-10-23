"""Dodawanie źródła podcastów ma czystą mowę i wąski zapis przez host."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gui_logic import install_wx_stub  # noqa: E402

install_wx_stub()

import amc_wx_lite.gui as gui  # noqa: E402
from amc_wx_lite.host_client import HostError, HostUnavailable  # noqa: E402
from amc_wx_lite.navigation import LibraryView, SessionId, View  # noqa: E402


class _Dialog:
    values = ("https://example.invalid/feed.xml", "Moja nazwa")
    instances = []

    def __init__(self, _parent):
        self.payload = {}
        self.transitions = []
        self.modal_result = gui.wx.ID_CANCEL
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def run_modal(self, submit):
        submit(*self.values)
        return self.modal_result

    def show_waiting(self, message):
        self.transitions.append(("waiting", message))

    def show_error(self, message):
        self.transitions.append(("error", message))

    def finish(self, payload):
        self.payload = dict(payload)
        self.modal_result = gui.wx.ID_OK


def _frame():
    calls: list[tuple[str, str]] = []
    spoken: list[str] = []
    statuses: list[str] = []
    reopened: list[tuple[str | None, str]] = []
    state = SimpleNamespace(
        view=View.LIST,
        library_view=LibraryView.PODCAST_LIBRARY,
    )

    def add(address, title):
        calls.append((address, title))
        return {
            "subscriptionId": "private-subscription-id",
            "title": "Moja nazwa",
            "sourceLabel": "podcast",
            "added": True,
            "restored": False,
            "itemCount": 12,
        }

    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:
            failed(error)

    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.PODCASTS,
            sessions={SessionId.PODCASTS: state},
        ),
        client=SimpleNamespace(add_podcast_source=add),
        runner=SimpleNamespace(submit=submit),
        announcer=SimpleNamespace(say=spoken.append),
        status_field=SimpleNamespace(SetLabel=statuses.append),
        status_bar=SimpleNamespace(show=statuses.append),
        _podcast_add_pending=False,
        _open_podcast_library=lambda preferred_id=None, completion_message="": (
            reopened.append((preferred_id, completion_message))
        ),
        calls=calls,
        spoken=spoken,
        statuses=statuses,
        reopened=reopened,
    )
    return frame


def test_ctrl_n_adds_source_without_speaking_private_identifier() -> None:
    frame = _frame()
    _Dialog.instances.clear()
    original = gui.PodcastSourceDialog
    gui.PodcastSourceDialog = _Dialog
    try:
        gui.LiteFrame._add_podcast_source(frame)
    finally:
        gui.PodcastSourceDialog = original

    assert frame.calls == [
        ("https://example.invalid/feed.xml", "Moja nazwa")
    ]
    assert frame._podcast_add_pending is False
    assert frame.spoken == ["Sprawdzanie i dodawanie źródła. Czekaj"]
    assert _Dialog.instances[-1].transitions == [
        ("waiting", "Sprawdzanie i dodawanie źródła. Czekaj")
    ]
    assert frame.reopened == [
        (
            "private-subscription-id",
            "Dodano: podcast: Moja nazwa. Pozycji: 12",
        )
    ]
    exposed = " ".join(frame.spoken + frame.statuses + [frame.reopened[0][1]])
    assert "private-subscription-id" not in exposed


def test_reopening_ctrl_n_creates_a_fresh_dialog_and_focus_contract() -> None:
    frame = _frame()
    _Dialog.instances.clear()
    original = gui.PodcastSourceDialog
    gui.PodcastSourceDialog = _Dialog
    try:
        gui.LiteFrame._add_podcast_source(frame)
        gui.LiteFrame._add_podcast_source(frame)
    finally:
        gui.PodcastSourceDialog = original

    assert len(_Dialog.instances) == 2
    assert _Dialog.instances[0] is not _Dialog.instances[1]
    assert all(
        dialog.transitions == [
            ("waiting", "Sprawdzanie i dodawanie źródła. Czekaj")
        ]
        for dialog in _Dialog.instances
    )
    assert frame.calls == [
        ("https://example.invalid/feed.xml", "Moja nazwa"),
        ("https://example.invalid/feed.xml", "Moja nazwa"),
    ]


def test_empty_address_is_rejected_before_host_call() -> None:
    frame = _frame()

    class EmptyDialog(_Dialog):
        values = ("", "")

    original = gui.PodcastSourceDialog
    gui.PodcastSourceDialog = EmptyDialog
    try:
        gui.LiteFrame._add_podcast_source(frame)
    finally:
        gui.PodcastSourceDialog = original

    assert frame.calls == []
    assert frame.spoken == ["Wpisz adres źródła"]
    assert isinstance(EmptyDialog.instances[-1], EmptyDialog)
    assert EmptyDialog.instances[-1].transitions == [
        ("error", "Wpisz adres źródła")
    ]


def test_dialog_help_names_supported_youtube_handle_address() -> None:
    source = inspect.getsource(gui.PodcastSourceDialog)
    assert "https://www.youtube.com/@NazwaKanału" in source
    assert 'add_button.SetName("Sprawdź i dodaj źródło")' in source
    assert "self.Bind(wx.EVT_CHAR_HOOK, self._on_key)" in source
    assert 'canonical == "Ctrl+V"' in source
    assert "wx.CallAfter(target.Paste)" in source


def test_ctrl_v_is_deferred_to_the_modal_address_field(monkeypatch) -> None:
    calls = []

    class Field:
        def SetFocus(self):
            calls.append("focus")

        def Paste(self):
            calls.append("paste")

    class Event:
        def Skip(self):
            calls.append("skip")

    address = Field()
    title = Field()
    dialog = SimpleNamespace(
        _busy=False,
        address_field=address,
        title_field=title,
    )
    monkeypatch.setattr(
        gui,
        "chord_from_event",
        lambda _event: SimpleNamespace(canonical="Ctrl+V"),
    )
    monkeypatch.setattr(gui.wx.Window, "FindFocus", lambda: None, raising=False)
    monkeypatch.setattr(gui.wx, "CallAfter", lambda callback: callback())

    gui.PodcastSourceDialog._on_key(dialog, Event())

    assert calls == ["focus", "paste"]


def test_waiting_state_blocks_second_enter_and_keeps_named_field_focused() -> None:
    class Control:
        def __init__(self):
            self.enabled = True
            self.editable = True
            self.focused = False
            self.selected = False
            self.label = ""
            self.name = ""

        def Enable(self, value):  # noqa: N802
            self.enabled = value

        def SetEditable(self, value):  # noqa: N802
            self.editable = value

        def SetFocus(self):  # noqa: N802
            self.focused = True

        def SelectAll(self):  # noqa: N802
            self.selected = True

        def SetLabel(self, value):  # noqa: N802
            self.label = value

        def SetName(self, value):  # noqa: N802
            self.name = value

    address = Control()
    title = Control()
    add = Control()
    cancel = Control()
    status = Control()
    dialog = SimpleNamespace(
        _busy=False,
        address_field=address,
        title_field=title,
        add_button=add,
        cancel_button=cancel,
        status_label=status,
        Layout=lambda: None,
    )

    gui.PodcastSourceDialog.show_waiting(
        dialog, "Sprawdzanie i dodawanie źródła. Czekaj"
    )

    assert dialog._busy is True
    assert address.focused is True
    assert address.editable is False and title.editable is False
    assert add.enabled is False and cancel.enabled is False
    assert status.name == "Sprawdzanie i dodawanie źródła. Czekaj"

    submissions = []
    blocked = SimpleNamespace(
        _busy=True,
        _submit=lambda *values: submissions.append(values),
        values=("https://www.youtube.com/@WieniawskiSociety", ""),
    )
    gui.PodcastSourceDialog._on_add(blocked, None)
    assert submissions == []


def test_error_restores_editing_focus_and_reopening_uses_a_fresh_dialog() -> None:
    class Control:
        def __init__(self):
            self.enabled = False
            self.editable = False
            self.focused = False
            self.selected = False

        def Enable(self, value):  # noqa: N802
            self.enabled = value

        def SetEditable(self, value):  # noqa: N802
            self.editable = value

        def SetFocus(self):  # noqa: N802
            self.focused = True

        def SelectAll(self):  # noqa: N802
            self.selected = True

        def SetLabel(self, _value):  # noqa: N802
            pass

        def SetName(self, _value):  # noqa: N802
            pass

    dialog = SimpleNamespace(
        _busy=True,
        address_field=Control(),
        title_field=Control(),
        add_button=Control(),
        cancel_button=Control(),
        status_label=Control(),
        Layout=lambda: None,
    )

    gui.PodcastSourceDialog.show_error(dialog, "Popraw adres i spróbuj ponownie")

    assert dialog._busy is False
    assert dialog.address_field.editable and dialog.title_field.editable
    assert dialog.add_button.enabled and dialog.cancel_button.enabled
    assert dialog.address_field.focused and dialog.address_field.selected


def test_technical_process_details_are_never_returned_for_nvda_speech() -> None:
    safe = HostError("Adres YouTube nie prowadzi do publicznego kanału ani playlisty")
    assert gui.podcast_add_error_message(safe) == str(safe)

    technical = HostError(
        "Windows 32: uruchamianie procesu terminal yt-dlp.exe "
        "at C:\\AMC\\host { Process = 32 }"
    )
    unavailable = HostUnavailable("Silnik nie odpowiedział na podcast.add")
    for error in (technical, unavailable):
        message = gui.podcast_add_error_message(error)
        assert "Win32" not in message
        assert "Windows 32" not in message
        assert "terminal" not in message
        assert "yt-dlp" not in message
        assert "C:\\" not in message
        assert "podcast.add" not in message
        assert "{" not in message
