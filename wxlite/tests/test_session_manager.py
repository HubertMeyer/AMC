from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from test_gui_logic import install_wx_stub

install_wx_stub()

from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.navigation import SessionId


SOURCE = Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"


class _Announcer:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def say(self, message: str) -> None:
        self.messages.append(message)


def _frame(order: list[str], current: SessionId) -> SimpleNamespace:
    frame = SimpleNamespace(
        options=SimpleNamespace(session_order=list(order)),
        navigator=SimpleNamespace(active=current),
        announcer=_Announcer(),
        _playing_sessions=set(),
        _pending_playback_session=None,
        _last_recording_status={},
        _transient_preview_return="unchanged",
        save_snapshots=[],
        menu_rebuilds=0,
        switches=[],
    )
    frame._sessions_blocked_from_disabling = lambda: (
        LiteFrame._sessions_blocked_from_disabling(frame)
    )
    frame._save_state = lambda: frame.save_snapshots.append((
        list(frame.options.session_order), frame.navigator.active
    )) or True
    frame._build_menu = lambda: setattr(
        frame, "menu_rebuilds", frame.menu_rebuilds + 1
    )

    def switch(session: SessionId) -> None:
        frame.switches.append(session)
        frame.navigator.active = session

    frame._switch_session = switch
    return frame


def test_disabling_external_sonos_or_wiim_never_sends_a_device_command() -> None:
    for session in (SessionId.SONOS, SessionId.WIIM):
        frame = _frame(["files", session.value], SessionId.FILES)

        changed, message = LiteFrame._toggle_session_enabled(frame, session)

        assert tuple(item.value for item in changed) == ("files",)
        expected_name = "Sonos" if session is SessionId.SONOS else "WiiM"
        assert message == f"Wyłączono sesję {expected_name}"
        assert frame.switches == []
        assert frame.save_snapshots == [(["files"], SessionId.FILES)]
        assert frame.menu_rebuilds == 1
        assert not hasattr(frame, "client")


def test_disabling_current_session_saves_valid_fallback_before_switching() -> None:
    frame = _frame(["files", "radio", "podcasts"], SessionId.RADIO)

    changed, message = LiteFrame._toggle_session_enabled(frame, SessionId.RADIO)

    assert tuple(item.value for item in changed) == ("files", "podcasts")
    assert frame.save_snapshots == [(["files", "podcasts"], SessionId.PODCASTS)]
    assert frame.switches == [SessionId.PODCASTS]
    assert frame.navigator.active is SessionId.PODCASTS
    assert "Aktywna sesja: Podcasty i YouTube, Ctrl+2" in message


def test_internal_playback_and_recording_block_only_the_owned_sessions() -> None:
    frame = _frame(["files", "radio", "sonos", "wiim"], SessionId.FILES)
    frame._playing_sessions = {SessionId.FILES, SessionId.SONOS, SessionId.WIIM}
    frame._pending_playback_session = SessionId.PODCASTS
    frame._last_recording_status = {"count": 1, "recordings": []}

    blocked = LiteFrame._sessions_blocked_from_disabling(frame)

    assert blocked == {SessionId.FILES, SessionId.PODCASTS, SessionId.RADIO}
    assert SessionId.SONOS not in blocked
    assert SessionId.WIIM not in blocked


def test_direct_switch_to_disabled_session_is_refused_with_user_facing_help() -> None:
    frame = _frame(["files", "radio", "podcasts"], SessionId.FILES)

    LiteFrame._switch_session(frame, SessionId.SPOTIFY)

    assert frame.announcer.messages == [
        "Sesja Spotify jest wyłączona. Otwórz Menedżer sesji skrótem Ctrl+Shift+S"
    ]
    assert frame.switches == []


def test_manager_dialog_has_explicit_names_keys_and_focus_restoration_contract() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    dialog = source[source.index("class SessionSelectionDialog") :]
    dialog = dialog[:dialog.index("class LiteFrame")]
    assert 'title="Menedżer sesji"' in dialog
    assert 'self.SetName("Menedżer sesji")' in dialog
    assert 'self.session_list.SetName("Sesje")' in dialog
    assert 'SetName("Przełącz do wybranej sesji")' in dialog
    assert 'SetName("Włącz lub wyłącz wybraną sesję")' in dialog
    assert 'SetName("Konfiguruj wybrane konto lub urządzenie")' in dialog
    assert "event.AltDown()" in dialog
    assert "event.GetKeyCode() == wx.WXK_UP" in dialog
    assert "event.GetKeyCode() == wx.WXK_DOWN" in dialog
    assert "self._refresh_rows(selected)" in dialog
    assert "self.session_list.SetFocus()" in dialog


def test_opening_manager_reads_only_cached_readiness_and_does_not_authenticate() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    readiness = source[source.index("    def _session_readiness") :]
    readiness = readiness[:readiness.index("    def _sessions_blocked_from_disabling")]
    assert "load_view" in readiness
    assert "login" not in readiness.casefold()
    assert "oauth" not in readiness.casefold()
    assert "open_browser" not in readiness.casefold()
