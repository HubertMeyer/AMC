"""Ctrl+Shift+P w Spotify: dostępne etykiety, fokus i uczciwy zapis."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gui_logic import install_wx_stub  # noqa: E402

install_wx_stub()

import amc_wx_lite.gui as gui  # noqa: E402
from amc_wx_lite.list_model import Row  # noqa: E402
from amc_wx_lite.spotify_playlist_dialog import (  # noqa: E402
    SpotifyPlaylistPayloadError,
    choices_from_payload,
)


def test_playlist_payload_uses_only_explicit_accessible_labels() -> None:
    choices = choices_from_payload({
        "playlists": [{
            "id": "secret-id",
            "name": "Poranek",
            "accessibleLabel": "Poranek, prywatna, właściciel Michał",
            "snapshotId": "secret-snapshot",
        }]
    })

    assert choices[0].label == (
        "Poranek, prywatna, właściciel Michał, niezaznaczona"
    )
    assert "secret-id" not in choices[0].label
    assert "secret-snapshot" not in choices[0].label
    assert str(choices[0]) == choices[0].label


def test_playlist_payload_rejects_missing_accessible_label() -> None:
    try:
        choices_from_payload({"playlists": [{"id": "p1", "name": "Nazwa"}]})
    except SpotifyPlaylistPayloadError as error:
        assert "niepełny wpis" in str(error)
    else:
        raise AssertionError("Niepełny wpis nie został odrzucony")


class _Dialog:
    def __init__(self, _parent, *, choices, target_label) -> None:
        assert target_label == "2 elementy"
        assert [choice.name for choice in choices] == ["Istniejąca"]
        self.selected_playlist_ids = ["existing"]
        self.new_playlists = [("Nowa prywatna", False)]

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def ShowModal(self) -> int:
        return gui.wx.ID_OK


def test_spotify_playlist_flow_creates_then_adds_and_restores_focus() -> None:
    rows = [
        Row("row-1", "Pierwszy", "track", service_id="track-1"),
        Row("row-2", "Drugi", "episode", service_id="episode-2"),
    ]
    calls: list[tuple[str, object]] = []
    spoken: list[str] = []
    focused: list[bool] = []

    client = SimpleNamespace(
        spotify_playlist_targets=lambda: {
            "playlists": [{
                "id": "existing",
                "name": "Istniejąca",
                "accessibleLabel": "Istniejąca, prywatna",
            }]
        },
        spotify_playlist_create=lambda name, is_public=False: (
            calls.append(("create", (name, is_public)))
            or {
                "playlist": {"id": "created"},
                "message": "Utworzono playlistę Spotify: Nowa prywatna, prywatna.",
            }
        ),
        spotify_playlist_add_items=lambda playlist_ids, items: (
            calls.append(("add", (playlist_ids, items)))
            or {"message": "Dodano 4 pozycje do wybranych playlist Spotify."}
        ),
    )

    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:
            failed(error)

    frame = SimpleNamespace(
        client=client,
        runner=SimpleNamespace(submit=submit),
        announcer=SimpleNamespace(say=spoken.append),
        _playlist_membership_pending=False,
        _selected_action_rows=lambda: rows,
        _restore_focus_after_dialog=lambda: focused.append(True),
    )
    previous = gui.SpotifyPlaylistDialog
    gui.SpotifyPlaylistDialog = _Dialog
    try:
        gui.LiteFrame._manage_spotify_playlist_membership(frame)
    finally:
        gui.SpotifyPlaylistDialog = previous

    assert calls[0] == ("create", ("Nowa prywatna", False))
    assert calls[1][0] == "add"
    playlist_ids, items = calls[1][1]
    assert playlist_ids == ["existing", "created"]
    assert [item["kind"] for item in items] == ["track", "episode"]
    assert focused == [True]
    assert spoken[0] == "Pobieram playlisty Spotify"
    assert "Utworzono playlistę Spotify" in spoken[-1]
    assert "Dodano 4 pozycje" in spoken[-1]
    assert frame._playlist_membership_pending is False


def test_spotify_playlist_flow_does_not_claim_unconfirmed_creation() -> None:
    spoken: list[str] = []

    class _NewOnlyDialog(_Dialog):
        def __init__(self, _parent, *, choices, target_label) -> None:
            assert choices == []
            assert target_label == "Pierwszy"
            self.selected_playlist_ids = []
            self.new_playlists = [("Bez identyfikatora", False)]

    client = SimpleNamespace(
        spotify_playlist_targets=lambda: {"playlists": []},
        spotify_playlist_create=lambda _name, is_public=False: {
            "playlist": {},
            "message": "Utworzono playlistę Spotify",
        },
        spotify_playlist_add_items=lambda _playlist_ids, _items: (_ for _ in ()).throw(
            AssertionError("Nie wolno dodawać do niepotwierdzonej playlisty")
        ),
    )

    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:
            failed(error)

    frame = SimpleNamespace(
        client=client,
        runner=SimpleNamespace(submit=submit),
        announcer=SimpleNamespace(say=spoken.append),
        _playlist_membership_pending=False,
        _selected_action_rows=lambda: [
            Row("row-1", "Pierwszy", "track", service_id="track-1")
        ],
        _restore_focus_after_dialog=lambda: None,
    )
    previous = gui.SpotifyPlaylistDialog
    gui.SpotifyPlaylistDialog = _NewOnlyDialog
    try:
        gui.LiteFrame._manage_spotify_playlist_membership(frame)
    finally:
        gui.SpotifyPlaylistDialog = previous

    assert spoken[-1] == (
        "Spotify nie potwierdził utworzenia playlisty Bez identyfikatora"
    )
    assert frame._playlist_membership_pending is False
