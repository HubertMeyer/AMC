from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.list_model import Row
from amc_wx_lite.navigation import LibraryView, Navigator, SessionId, View
from amc_wx_lite.shortcuts import (
    Action,
    Chord,
    GLOBAL_VIEW_SHORTCUTS,
    SONOS_SUPPORTED_ACTIONS,
    WIIM_SUPPORTED_ACTIONS,
    resolve,
)
from amc_wx_lite.state_store import LiteState
from amc_wx_lite.transient_preview_policy import (
    TRANSIENT_PREVIEW_ACTIONS,
    is_transient_preview_available,
    load_global_transient_previews,
    resolve_global_transient_previews,
    transient_preview_unavailable_message,
)


def test_global_mode_exposes_all_three_previews_in_every_session() -> None:
    for action in TRANSIENT_PREVIEW_ACTIONS:
        for session in SessionId:
            assert is_transient_preview_available(
                action, session, global_previews=True
            )


def test_global_preview_shortcuts_reach_dispatch_from_native_lists() -> None:
    """A mapping-only test misses keys swallowed by the Windows list."""

    frame_hook = inspect.getsource(LiteFrame._on_player_shortcut_hook)
    list_hook = inspect.getsource(LiteFrame._on_list_shortcut_hook)
    assert set(GLOBAL_VIEW_SHORTCUTS) == {
        "Ctrl+I", "Alt+R", "Alt+Shift+R", "Ctrl+H", "Ctrl+L",
    }
    # Obie bramki korzystaja z jednej tabeli zamiast kopiowac gesty do
    # adapterow. Sama nazwa tabeli w kodzie jest kontraktem tej sciezki.
    assert "GLOBAL_VIEW_SHORTCUTS" in frame_hook
    assert "GLOBAL_VIEW_SHORTCUTS" in list_hook


def test_global_view_shortcuts_resolve_before_provider_tables() -> None:
    cases = (
        (Chord("H", ctrl=True), Action.VIEW_HISTORY),
        (Chord("L", ctrl=True), Action.VIEW_LIBRARY),
        (Chord("R", alt=True), Action.VIEW_ACTIVE_RECORDINGS),
        (Chord("R", alt=True, shift=True), Action.VIEW_RECORDED_RADIO_FILES),
    )
    sessions = (
        SessionId.RADIO,
        SessionId.PODCASTS,
        SessionId.WIIM,
        SessionId.SONOS,
    )
    for session in sessions:
        for player in (False, True):
            for chord, expected in cases:
                assert resolve(
                    chord,
                    player_view=player,
                    radio_session=session is SessionId.RADIO,
                    podcast_session=session is SessionId.PODCASTS,
                    wiim_session=session is SessionId.WIIM,
                    sonos_session=session is SessionId.SONOS,
                ) is expected


def test_ctrl_h_opens_once_and_escape_restores_origin_and_selected_item() -> None:
    origins = (
        SessionId.RADIO,
        SessionId.PODCASTS,
        SessionId.WIIM,
        SessionId.SONOS,
    )
    for origin in origins:
        navigator = Navigator()
        navigator.active = origin
        original_rows = [
            Row("pierwszy", "Pierwszy", "track"),
            Row("wybrany", "Wybrany", "track"),
        ]
        navigator.session.model.replace(original_rows, preferred_id="wybrany")
        opened: list[SessionId] = []
        syncs: list[str] = []
        frame = SimpleNamespace(
            navigator=navigator,
            state=LiteState(playback_history_by_session={
                origin.value: [{
                    "itemId": f"{origin.value}:observed:test",
                    "title": "Historia streamera",
                    "kind": "track",
                    "replaySupported": False,
                }]
            }),
            _transient_preview_return=None,
            _sync_views=lambda: syncs.append("focus"),
        )
        frame._begin_transient_preview = (
            lambda current=frame: LiteFrame._begin_transient_preview(current)
        )

        def open_radio(_intent, **kwargs) -> None:
            assert kwargs["announce_single_item"] is True
            opened.append(SessionId.RADIO)
            navigator.apply_radio_view(
                LibraryView.HISTORY,
                "Radio — Historia odtwarzania",
                [Row("historia", "Historia", "station")],
            )

        def open_podcasts(_intent, **kwargs) -> None:
            assert kwargs["announce_single_item"] is True
            opened.append(SessionId.PODCASTS)
            navigator.apply_podcast_aggregate(
                LibraryView.PODCAST_HISTORY,
                "Historia odtwarzania",
                [Row("historia", "Historia", "episode")],
            )

        def open_files(_intent, **kwargs) -> None:
            assert kwargs["announce_single_item"] is True
            opened.append(SessionId.FILES)
            navigator.apply_library_view(
                LibraryView.HISTORY,
                "Biblioteka — Historia odtwarzania",
                [Row("historia", "Historia", "track")],
            )

        frame._open_radio_view = open_radio
        frame._open_podcast_aggregate = open_podcasts
        frame._open_library_view = open_files
        frame._run = lambda _events: opened.append(origin)
        frame._announce_transient_preview = lambda _events: opened.append(origin)

        LiteFrame._show_playback_history_preview(frame)

        assert opened == [origin]
        if origin in (SessionId.WIIM, SessionId.SONOS):
            assert navigator.active is origin
            assert navigator.session.library_view is LibraryView.SERVICE_HISTORY
            assert navigator.session.model.selected_row.title == (
                "Historia streamera"
            )
        assert LiteFrame._restore_transient_preview(frame, announce=False)
        assert navigator.active is origin
        assert navigator.session.view is View.LIST
        assert navigator.session.model.selected_id == "wybrany"
        assert syncs == ["focus"]
        assert not LiteFrame._restore_transient_preview(frame, announce=False)


def test_remote_provider_gates_allow_the_global_history_action() -> None:
    assert Action.VIEW_HISTORY in WIIM_SUPPORTED_ACTIONS
    assert Action.VIEW_HISTORY in SONOS_SUPPORTED_ACTIONS
    assert Action.REMOVE_SELECTED in WIIM_SUPPORTED_ACTIONS
    assert Action.REMOVE_SELECTED in SONOS_SUPPORTED_ACTIONS


def test_disabled_global_mode_keeps_only_home_sessions() -> None:
    assert is_transient_preview_available(
        Action.VIEW_ACTIVE_RECORDINGS, SessionId.RADIO, global_previews=False
    )
    assert not is_transient_preview_available(
        Action.VIEW_ACTIVE_RECORDINGS, SessionId.FILES, global_previews=False
    )
    assert is_transient_preview_available(
        Action.VIEW_RECORDED_RADIO_FILES, SessionId.RADIO, global_previews=False
    )
    assert is_transient_preview_available(
        Action.VIEW_RECORDED_RADIO_FILES, SessionId.FILES, global_previews=False
    )
    assert is_transient_preview_available(
        Action.VIEW_PODCAST_INBOX, SessionId.PODCASTS, global_previews=False
    )
    assert not is_transient_preview_available(
        Action.VIEW_PODCAST_INBOX, SessionId.TIDAL, global_previews=False
    )


def test_unavailable_messages_name_user_facing_home_sessions() -> None:
    assert "Radio" in transient_preview_unavailable_message(
        Action.VIEW_ACTIVE_RECORDINGS
    )
    assert "Pliki lokalne" in transient_preview_unavailable_message(
        Action.VIEW_RECORDED_RADIO_FILES
    )
    assert "Podcasty i YouTube" in transient_preview_unavailable_message(
        Action.VIEW_PODCAST_INBOX
    )


def test_profile_value_is_strict_and_private_override_wins(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    assert load_global_transient_previews(state) is True
    state.write_text(
        '{"settings":{"globalTransientPreviews":false}}', encoding="utf-8"
    )
    assert load_global_transient_previews(state) is False
    assert resolve_global_transient_previews(None, False) is False
    assert resolve_global_transient_previews(True, False) is True

    state.write_text(
        '{"settings":{"globalTransientPreviews":"false"}}', encoding="utf-8"
    )
    assert load_global_transient_previews(state) is True


def test_window_blocks_global_shortcut_before_running_foreign_session_action() -> None:
    spoken: list[str] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.TIDAL),
        _global_transient_previews=False,
        announcer=SimpleNamespace(say=spoken.append),
    )

    LiteFrame._dispatch(frame, Action.VIEW_ACTIVE_RECORDINGS)

    assert len(spoken) == 1
    assert "Radio" in spoken[0]


def test_window_runs_preview_in_its_home_session_when_global_mode_is_off() -> None:
    calls: list[str] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.RADIO),
        _global_transient_previews=False,
        announcer=SimpleNamespace(say=lambda _text: None),
        messages=SimpleNamespace(custom_seek_seconds=300),
        _show_active_radio_recordings=lambda: calls.append("active"),
    )

    LiteFrame._dispatch(frame, Action.VIEW_ACTIVE_RECORDINGS)

    assert calls == ["active"]
