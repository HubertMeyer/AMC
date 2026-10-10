"""Ctrl+Shift+P przekazuje wielokrotne zaznaczenie i atomowo zapisuje dialog."""

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


class _Dialog:
    def __init__(self, _parent, *, choices, selected_item_ids, target_label) -> None:
        assert selected_item_ids == ["local-1", "local-2"]
        assert target_label == "2 elementy"
        choices[0].toggle(selected_item_ids)
        self.result_playlists = [choice.payload() for choice in choices]

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def ShowModal(self) -> int:
        return gui.wx.ID_OK


def test_local_multiselection_reaches_atomic_playlist_replace() -> None:
    rows = [
        Row("local-1", "Pierwszy", "track", path="D:/pierwszy.mp3"),
        Row("local-2", "Drugi", "track", path="D:/drugi.mp3"),
    ]
    model = ListModel()
    model.replace(rows)
    calls: list[tuple[str, object]] = []
    spoken: list[str] = []
    refreshed: list[str | None] = []

    def profile_playlists(session_id: str):
        calls.append(("load", session_id))
        return {
            "sessionId": "local",
            "playlists": [
                {
                    "playlistId": "p1",
                    "name": "Poranek",
                    "createdUtcTicks": 638000000000000000,
                    "itemIds": ["local-1"],
                }
            ],
        }

    def replace(session_id: str, playlists):
        calls.append(("save", (session_id, playlists)))
        return {"sessionId": session_id, "saved": len(playlists)}

    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:
            failed(error)

    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.FILES,
            session=SimpleNamespace(model=model, view=View.LIST),
        ),
        client=SimpleNamespace(
            profile_playlists=profile_playlists,
            replace_profile_playlists=replace,
        ),
        runner=SimpleNamespace(submit=submit),
        announcer=SimpleNamespace(say=spoken.append),
        _playlist_membership_pending=False,
        _selected_action_rows=lambda: rows,
        _restore_focus_after_dialog=lambda: None,
        _refresh_profile_view=lambda preferred_id=None: refreshed.append(preferred_id),
    )
    previous = gui.PlaylistMembershipDialog
    gui.PlaylistMembershipDialog = _Dialog
    try:
        gui.LiteFrame._manage_playlist_membership(frame)
    finally:
        gui.PlaylistMembershipDialog = previous

    assert calls[0] == ("load", "local")
    saved_session, saved_playlists = calls[1][1]
    assert saved_session == "local"
    assert saved_playlists[0]["itemIds"] == ["local-1", "local-2"]
    assert refreshed == ["local-1"]
    assert spoken == ["Zapisano zmiany playlist dla: 2 elementy"]
    assert frame._playlist_membership_pending is False


def test_playlist_container_is_rejected_without_sending_its_id() -> None:
    row = Row("playlist:private", "Poranek", "playlist")
    spoken: list[str] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.FILES),
        client=SimpleNamespace(),
        announcer=SimpleNamespace(say=spoken.append),
        _playlist_membership_pending=False,
        _selected_action_rows=lambda: [row],
    )

    gui.LiteFrame._manage_playlist_membership(frame)

    assert spoken == ["Wybierz plik"]
    assert "private" not in spoken[0]
