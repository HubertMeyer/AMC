from __future__ import annotations

from amc_wx_lite.navigation import SessionId
from amc_wx_lite import menu_model
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.session_order import (
    action_for_slot,
    adjacent,
    normalize,
    selection_labels,
    slot_for_session,
    values,
)
from amc_wx_lite.shortcuts import Action


def test_default_order_preserves_existing_wx_shortcuts() -> None:
    assert values(None) == [
        "files", "radio", "podcasts", "tidal", "wiim", "sonos", "spotify"
    ]
    assert action_for_slot(1, None) is Action.SESSION_FILES
    assert action_for_slot(6, None) is Action.SESSION_SONOS
    assert action_for_slot(7, None) is Action.SESSION_SPOTIFY
    assert action_for_slot(8, None) is None


def test_custom_order_drives_slots_labels_and_actions_without_model_leaks() -> None:
    raw = ["sonos", "radio", "files", "wiim", "tidal", "podcasts", "spotify"]

    assert slot_for_session(SessionId.FILES, raw) == 3
    assert action_for_slot(1, raw) is Action.SESSION_SONOS
    assert selection_labels(raw)[:3] == (
        "Ctrl+1, Sonos",
        "Ctrl+2, Radio internetowe",
        "Ctrl+3, Pliki lokalne",
    )
    assert all("SessionId" not in label for label in selection_labels(raw))


def test_invalid_duplicates_are_removed_and_missing_sessions_are_appended() -> None:
    assert normalize(["tidal", "tidal", "TechnicalEnum.Value", 7]) == (
        SessionId.TIDAL,
        SessionId.FILES,
        SessionId.RADIO,
        SessionId.PODCASTS,
        SessionId.WIIM,
        SessionId.SONOS,
        SessionId.SPOTIFY,
    )


def test_adjacent_session_wraps_in_custom_order() -> None:
    raw = ["wiim", "files", "radio", "podcasts", "tidal", "sonos", "spotify"]
    assert adjacent(SessionId.WIIM, -1, raw) is SessionId.SPOTIFY
    assert adjacent(SessionId.WIIM, 1, raw) is SessionId.FILES
    assert adjacent(SessionId.SPOTIFY, 1, raw) is SessionId.WIIM


def test_custom_order_drives_menu_shortcuts_and_palette_labels() -> None:
    raw = ["sonos", "radio", "files", "wiim", "tidal", "podcasts", "spotify"]
    view = next(menu for menu in menu_model.build_menus(raw) if menu.title == "&Widok")
    sessions = [
        item for item in view.items
        if item.action in {
            Action.SESSION_FILES,
            Action.SESSION_RADIO,
            Action.SESSION_PODCASTS,
            Action.SESSION_TIDAL,
            Action.SESSION_WIIM,
            Action.SESSION_SONOS,
            Action.SESSION_SPOTIFY,
        }
    ]
    assert [(item.action, item.shortcut) for item in sessions] == [
        (Action.SESSION_SONOS, "Ctrl+1"),
        (Action.SESSION_RADIO, "Ctrl+2"),
        (Action.SESSION_FILES, "Ctrl+3"),
        (Action.SESSION_WIIM, "Ctrl+4"),
        (Action.SESSION_TIDAL, "Ctrl+5"),
        (Action.SESSION_PODCASTS, "Ctrl+6"),
        (Action.SESSION_SPOTIFY, "Ctrl+7"),
    ]
    palette = {entry.action: entry.shortcut for entry in entries_for_session(SessionId.FILES, raw)}
    assert palette[Action.SESSION_SONOS] == "Ctrl+1"
    assert palette[Action.SESSION_FILES] == "Ctrl+3"


def test_session_list_has_one_shortcut_and_ctrl_zero_is_unused() -> None:
    view = next(menu for menu in menu_model.build_menus() if menu.title == "&Widok")
    item = next(entry for entry in view.items if entry.action is Action.SESSION_LIST)
    assert item.shortcut == "Ctrl+Shift+S"
