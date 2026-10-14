from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.shortcuts import Action
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
    for shortcut in ("Ctrl+I", "Alt+R", "Alt+Shift+R"):
        quoted = f'"{shortcut}"'
        assert quoted in frame_hook
        assert quoted in list_hook


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
    assert "Radio internetowe" in transient_preview_unavailable_message(
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
    assert "Radio internetowe" in spoken[0]


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
