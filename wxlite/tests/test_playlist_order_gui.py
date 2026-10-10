"""Ręczna kolejność otwartej playlisty bez ujawniania identyfikatorów."""

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

    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:
            failed(error)

    client = SimpleNamespace(
        move_profile_playlist_items=lambda *args: (
            calls.append(("move", args))
            or {"status": "moved", "moved": True}
        ),
        place_profile_playlist_items_before=lambda *args: (
            calls.append(("place", args))
            or {"status": "moved", "moved": True}
        ),
    )
    state = SimpleNamespace(
        model=model,
        view=View.LIST,
        library_view=LibraryView.PLAYLIST_CONTENTS,
        library_playlist_id="playlist-private-id",
    )
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.FILES, session=state),
        filter_box=_Filter(),
        announcer=SimpleNamespace(say=spoken.append),
        runner=SimpleNamespace(submit=submit),
        client=client,
        _selected_action_rows=lambda: selected,
        _pending_internal_playlist_move=None,
        _playlist_order_pending=False,
        pending_external_moves={},
    )
    frame._open_profile_playlist_context = (
        lambda: gui.LiteFrame._open_profile_playlist_context(frame)
    )
    frame._playlist_order_rows = (
        lambda item_kind: gui.LiteFrame._playlist_order_rows(frame, item_kind)
    )
    frame._clear_pending_external_moves = frame.pending_external_moves.clear

    def refresh(preferred_id=None, **kwargs):
        refreshed.append({"preferred_id": preferred_id, **kwargs})
        callback = kwargs.get("after_refresh")
        if callback is not None:
            callback()

    frame._refresh_profile_view = refresh
    return frame, spoken, calls, refreshed


def test_alt_down_moves_contiguous_multiselection_and_restores_it_by_id() -> None:
    rows = [
        Row("private-a", "Alfa", "track"),
        Row("private-b", "Beta", "track"),
        Row("private-c", "Gamma", "track"),
    ]
    frame, spoken, calls, refreshed = _frame(rows, rows[:2])

    gui.LiteFrame._move_playlist_selection(frame, 1)

    assert calls == [(
        "move",
        (
            "local",
            "playlist-private-id",
            ["private-a", "private-b"],
            ["private-a", "private-b", "private-c"],
            1,
        ),
    )]
    assert refreshed[0]["preferred_id"] == "private-a"
    assert refreshed[0]["selected_ids"] == ["private-a", "private-b"]
    assert spoken == ["Przeniesiono 2 elementy w dół, pod Gamma"]
    assert all("private" not in message for message in spoken)


def test_ctrl_x_then_ctrl_v_places_nonadjacent_selection_before_focus() -> None:
    rows = [
        Row("private-a", "Alfa", "track"),
        Row("private-b", "Beta", "track"),
        Row("private-c", "Gamma", "track"),
    ]
    frame, spoken, calls, refreshed = _frame(rows, [rows[0], rows[2]])
    frame.pending_external_moves["old"] = "D:/stary.mp3"

    gui.LiteFrame._cut_or_start_internal_playlist_move(frame)
    assert frame._pending_internal_playlist_move == (
        "local", "playlist-private-id", ("private-a", "private-c")
    )
    assert frame.pending_external_moves == {}

    frame.navigator.session.model.select_id("private-b")
    gui.LiteFrame._paste_internal_playlist_move(frame)

    assert calls == [(
        "place",
        (
            "local",
            "playlist-private-id",
            ["private-a", "private-c"],
            "private-b",
        ),
    )]
    assert refreshed[0]["selected_ids"] == ["private-a", "private-c"]
    assert frame._pending_internal_playlist_move is None
    assert spoken == [
        "Zaznaczono do przeniesienia: 2 elementy. Wybierz miejsce i naciśnij Ctrl+V",
        "Przeniesiono 2 elementy przed Beta",
    ]
    assert all("private" not in message for message in spoken)


def test_filter_blocks_order_change_before_calling_host() -> None:
    row = Row("private-a", "Alfa", "track")
    frame, spoken, calls, _refreshed = _frame([row], [row])
    frame.filter_box.value = "alf"

    gui.LiteFrame._move_playlist_selection(frame, -1)

    assert calls == []
    assert spoken == [
        "Wyczyść filtr klawiszem Escape przed zmianą kolejności"
    ]


def test_radio_playlist_order_uses_radio_session_and_station_rows() -> None:
    rows = [
        Row("private-radio-a", "Radio Alfa", "station"),
        Row("private-radio-b", "Radio Beta", "station"),
        Row("private-radio-c", "Radio Gamma", "station"),
    ]
    frame, spoken, calls, refreshed = _frame(rows, rows[1:])
    frame.navigator.active = SessionId.RADIO

    gui.LiteFrame._move_playlist_selection(frame, -1)

    assert calls == [(
        "move",
        (
            "radio",
            "playlist-private-id",
            ["private-radio-b", "private-radio-c"],
            ["private-radio-a", "private-radio-b", "private-radio-c"],
            -1,
        ),
    )]
    assert refreshed[0]["selected_ids"] == [
        "private-radio-b", "private-radio-c"
    ]
    assert spoken == ["Przeniesiono 2 elementy w górę, nad Radio Alfa"]
    assert all("private" not in message for message in spoken)

