"""Ctrl+Shift+U zmienia Ulubione bez technicznych nazw w komunikatach."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gui_logic import install_wx_stub  # noqa: E402

install_wx_stub()

import amc_wx_lite.gui as gui  # noqa: E402
from amc_wx_lite.list_model import ListModel, Row  # noqa: E402
from amc_wx_lite.navigation import SessionId, View  # noqa: E402


def _frame(active: SessionId, rows: list[Row], *, favorite: bool, player: bool = False):
    model = ListModel()
    model.replace(rows)
    state = SimpleNamespace(model=model, view=View.PLAYER if player else View.LIST)
    calls: list[tuple[str, list[str]]] = []
    spoken: list[str] = []
    refreshed: list[str | None] = []

    def toggle(session_id, item_ids):
        calls.append((session_id, list(item_ids)))
        return {
            "favorite": favorite,
            "requested": len(item_ids),
            "changed": len(item_ids),
        }

    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:
            failed(error)

    return SimpleNamespace(
        navigator=SimpleNamespace(active=active, session=state),
        client=SimpleNamespace(toggle_profile_favorites=toggle),
        runner=SimpleNamespace(submit=submit),
        announcer=SimpleNamespace(say=spoken.append),
        _selected_action_rows=lambda: rows,
        _refresh_profile_view=lambda preferred_id=None: refreshed.append(preferred_id),
        calls=calls,
        spoken=spoken,
        refreshed=refreshed,
    )


def test_local_multiselection_is_sent_in_visible_order_and_refreshed() -> None:
    rows = [
        Row(item_id="local-1", title="Pierwszy plik", kind="track", path="D:/pierwszy.mp3"),
        Row(item_id="local-2", title="Drugi plik", kind="track", path="D:/drugi.mp3"),
    ]
    frame = _frame(SessionId.FILES, rows, favorite=True)

    gui.LiteFrame._toggle_profile_favorite(frame)

    assert frame.calls == [("files", ["local-1", "local-2"])]
    assert frame.refreshed == ["local-1"]
    assert frame.spoken == ["Dodano do ulubionych: 2 elementy"]


def test_radio_uses_station_names_and_does_not_leave_player() -> None:
    row = Row(item_id="station-private", title="Radio Poznań", kind="station")
    frame = _frame(SessionId.RADIO, [row], favorite=False, player=True)

    gui.LiteFrame._toggle_profile_favorite(frame)

    assert frame.calls == [("radio", ["station-private"])]
    assert frame.refreshed == []
    assert frame.spoken == ["Usunięto z ulubionych: Radio Poznań"]


def test_container_is_not_sent_as_an_item_identifier() -> None:
    row = Row(item_id="folder:private", title="Muzyka", kind="folder")
    frame = _frame(SessionId.FILES, [row], favorite=True)

    gui.LiteFrame._toggle_profile_favorite(frame)

    assert frame.calls == []
    assert frame.spoken == ["Wybierz plik"]
