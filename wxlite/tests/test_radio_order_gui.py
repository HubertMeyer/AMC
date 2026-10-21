"""Ręczna kolejność Biblioteki i Ulubionych Radia z komunikatami NVDA."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gui_logic import install_wx_stub  # noqa: E402

install_wx_stub()

import amc_wx_lite.gui as gui  # noqa: E402
from amc_wx_lite.list_model import ListModel, Row  # noqa: E402
from amc_wx_lite.navigation import LibraryView, SessionId, View  # noqa: E402
from amc_wx_lite.radio_source import SORT_CUSTOM  # noqa: E402


class _Filter:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def GetValue(self) -> str:
        return self.value


def _frame(rows: list[Row], selected: list[Row]):
    model = ListModel()
    model.replace(rows, preferred_id=selected[0].item_id)
    spoken: list[str] = []
    refreshed: list[dict] = []
    calls: list[tuple] = []
    selection = list(selected)

    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:
            failed(error)

    client = SimpleNamespace(
        move_radio_collection_items=lambda *args: (
            calls.append(("move", args))
            or {"status": "moved", "moved": True}
        ),
        place_radio_collection_items_before=lambda *args: (
            calls.append(("place", args))
            or {"status": "moved", "moved": True}
        ),
    )
    state = SimpleNamespace(
        model=model,
        view=View.LIST,
        library_view=None,
        library_playlist_id=None,
    )
    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.RADIO,
            session=state,
            sessions={SessionId.RADIO: state},
        ),
        filter_box=_Filter(),
        announcer=SimpleNamespace(say=spoken.append),
        runner=SimpleNamespace(submit=submit),
        client=client,
        _selected_action_rows=lambda: list(selection),
        _pending_internal_playlist_move=None,
        _pending_radio_collection_move=None,
        _playlist_order_pending=False,
        _radio_effective_sort_modes={
            "library": SORT_CUSTOM,
            "favorites": SORT_CUSTOM,
        },
        pending_external_moves={"old": "D:/stary.mp3"},
    )
    frame._radio_manual_order_context = (
        lambda: gui.LiteFrame._radio_manual_order_context(frame)
    )
    frame._radio_collection_order_rows = (
        lambda: gui.LiteFrame._radio_collection_order_rows(frame)
    )
    frame._move_radio_collection_selection = (
        lambda direction: gui.LiteFrame._move_radio_collection_selection(
            frame, direction
        )
    )
    frame._cut_radio_collection_move = (
        lambda: gui.LiteFrame._cut_radio_collection_move(frame)
    )
    frame._paste_radio_collection_move = (
        lambda: gui.LiteFrame._paste_radio_collection_move(frame)
    )
    frame._clear_pending_external_moves = frame.pending_external_moves.clear

    def refresh(preferred_id=None, **kwargs):
        refreshed.append({"preferred_id": preferred_id, **kwargs})
        callback = kwargs.get("after_refresh")
        if callback is not None:
            callback()

    frame._refresh_profile_view = refresh
    return frame, selection, spoken, calls, refreshed


def test_alt_down_moves_radio_station_and_names_the_station_below() -> None:
    rows = [
        Row("private-a", "Jedynka", "station"),
        Row("private-b", "Dwójka", "station"),
        Row("private-c", "Trójka", "station"),
    ]
    frame, _selection, spoken, calls, refreshed = _frame(rows, [rows[1]])

    gui.LiteFrame._move_playlist_selection(frame, 1)

    assert calls == [(
        "move",
        (
            "library",
            ["private-b"],
            ["private-a", "private-b", "private-c"],
            1,
        ),
    )]
    assert refreshed[0]["selected_ids"] == ["private-b"]
    assert spoken == ["Przeniesiono stację w dół, pod Trójka"]
    assert all("private" not in message for message in spoken)


def test_ctrl_x_then_ctrl_v_places_radio_stations_before_focused_target() -> None:
    rows = [
        Row("private-a", "Jedynka", "station"),
        Row("private-b", "Dwójka", "station"),
        Row("private-c", "Trójka", "station"),
    ]
    frame, selection, spoken, calls, refreshed = _frame(
        rows, [rows[0], rows[2]]
    )

    gui.LiteFrame._cut_or_start_internal_playlist_move(frame)
    assert frame._pending_radio_collection_move == (
        "library", ("private-a", "private-c")
    )
    assert frame.pending_external_moves == {}

    selection[:] = [rows[1]]
    frame.navigator.session.model.select_id("private-b")
    gui.LiteFrame._paste_internal_playlist_move(frame)

    assert calls == [(
        "place",
        (
            "library",
            ["private-a", "private-c"],
            ["private-a", "private-b", "private-c"],
            "private-b",
        ),
    )]
    assert refreshed[0]["selected_ids"] == ["private-a", "private-c"]
    assert frame._pending_radio_collection_move is None
    assert spoken == [
        "Zaznaczono stacje do przeniesienia: 2. "
        "Wybierz miejsce i naciśnij Ctrl+V",
        "Przeniesiono stacje: 2, przed Dwójka",
    ]
    assert all("private" not in message for message in spoken)


def test_radio_manual_order_requires_custom_sort_and_no_filter() -> None:
    row = Row("private-a", "Jedynka", "station")
    frame, _selection, spoken, calls, _refreshed = _frame([row], [row])
    frame._radio_effective_sort_modes["library"] = "Alphabetical"

    gui.LiteFrame._move_playlist_selection(frame, -1)

    assert calls == []
    assert spoken == [
        "Przenoszenie działa w kolejności własnej. Naciśnij Alt 3"
    ]

    spoken.clear()
    frame._radio_effective_sort_modes["library"] = SORT_CUSTOM
    frame.filter_box.value = "jed"
    gui.LiteFrame._move_playlist_selection(frame, -1)

    assert calls == []
    assert spoken == [
        "Wyczyść filtr klawiszem Escape przed zmianą kolejności"
    ]


def test_radio_favorites_use_a_separate_manual_order_scope() -> None:
    rows = [
        Row("private-a", "Jedynka", "station"),
        Row("private-b", "Dwójka", "station"),
    ]
    frame, _selection, _spoken, calls, _refreshed = _frame(rows, [rows[1]])
    frame.navigator.session.library_view = LibraryView.FAVORITES

    gui.LiteFrame._move_playlist_selection(frame, -1)

    assert calls == [(
        "move",
        (
            "favorites",
            ["private-b"],
            ["private-a", "private-b"],
            -1,
        ),
    )]
