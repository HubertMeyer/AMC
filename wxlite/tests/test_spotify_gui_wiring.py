from __future__ import annotations

from types import SimpleNamespace

import amc_wx_lite.gui as gui_module
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.host_client import HostError
from amc_wx_lite.navigation import (
    Announce,
    OpenSpotifyCollectionView,
    OpenSpotifyContainer,
    OpenSpotifyView,
    PlaySpotifyItem,
    SessionId,
)
from amc_wx_lite.shortcuts import Action


class ImmediateRunner:
    @staticmethod
    def submit(_name, work, done, failed):
        try:
            done(work())
        except Exception as error:  # pragma: no cover - diagnostics path
            failed(error)


def test_spotify_album_shortcut_opens_the_same_collection_path_as_enter() -> None:
    received = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.SPOTIFY),
        _open_spotify_collection_view=received.append,
        messages=SimpleNamespace(custom_seek_seconds=300),
    )

    LiteFrame._dispatch(frame, Action.SPOTIFY_VIEW_ALBUMS)

    assert received == [OpenSpotifyCollectionView(
        "spotify-collection:albums", "albums", "Albumy"
    )]


def test_spotify_root_reads_status_and_applies_only_user_labels() -> None:
    calls = []
    messages = []
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_collection_root=lambda: {
                "heading": "Biblioteka Spotify",
                "views": [
                    {"view": "liked", "label": "Polubione utwory"},
                    {"view": "artists", "label": "Wykonawcy"},
                ],
            },
            spotify_account_status=lambda: {
                "catalog": {
                    "connected": False,
                    "label": "Katalog Spotify nie jest skonfigurowany.",
                }
            },
        ),
        _spotify_navigation_version=0,
        navigator=SimpleNamespace(
            active=SessionId.SPOTIFY,
            apply_spotify_view=lambda heading, rows, preferred_id=None: (
                calls.append((heading, rows, preferred_id))
                or [Announce(heading)]
            ),
        ),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=messages.append),
        _run=lambda events: calls.append(events),
    )

    LiteFrame._open_spotify_view(frame, OpenSpotifyView("spotify-collection:artists"))

    heading, rows, preferred_id = calls[0]
    assert heading == "Biblioteka Spotify"
    assert [row.title for row in rows] == ["Polubione utwory", "Wykonawcy"]
    assert preferred_id == "spotify-collection:artists"
    assert messages == ["Katalog Spotify nie jest skonfigurowany."]


def test_spotify_collection_view_passes_only_the_private_view_key_to_host() -> None:
    calls = []
    intent = OpenSpotifyCollectionView(
        "spotify-collection:artists", "artists", "Wykonawcy"
    )
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_collection_view=lambda view: (
                calls.append(("host", view))
                or {"heading": "Wykonawcy Spotify", "items": [], "warning": ""}
            )
        ),
        _spotify_navigation_version=0,
        navigator=SimpleNamespace(
            active=SessionId.SPOTIFY,
            apply_spotify_collection_view=lambda received, heading, rows: (
                calls.append(("apply", received, heading, rows)) or []
            ),
        ),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=lambda message: calls.append(("say", message))),
        _run=lambda events: calls.append(("run", events)),
    )

    LiteFrame._open_spotify_collection_view(frame, intent)

    assert calls[0] == ("host", "artists")
    assert calls[1] == ("apply", intent, "Wykonawcy Spotify", [])


def test_spotify_artist_section_uses_the_read_only_container_contract() -> None:
    received = []
    intent = OpenSpotifyContainer(
        "private-row", "privateartist", "Wykonawca", "artist", section="tracks"
    )
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_container_items=lambda **values: (
                received.append(values)
                or {"heading": "Utwory wykonawcy, Wykonawca", "items": []}
            )
        ),
        _spotify_navigation_version=0,
        navigator=SimpleNamespace(
            active=SessionId.SPOTIFY,
            apply_spotify_container=lambda *_args: [],
        ),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=lambda _message: None),
        _run=lambda _events: None,
    )

    LiteFrame._open_spotify_container(frame, intent)

    assert received == [{
        "external_id": "privateartist",
        "title": "Wykonawca",
        "kind": "artist",
        "artist": "",
        "artist_section": "tracks",
    }]


def test_busy_spotify_collection_enter_is_retried_without_speaking_error() -> None:
    submissions = []
    scheduled = []
    messages = []
    intent = OpenSpotifyCollectionView(
        "spotify-collection:artists", "artists", "Wykonawcy"
    )
    frame = SimpleNamespace(
        client=SimpleNamespace(spotify_collection_view=lambda _view: {}),
        _spotify_navigation_version=0,
        navigator=SimpleNamespace(active=SessionId.SPOTIFY),
        runner=SimpleNamespace(submit=lambda *args: submissions.append(args)),
        announcer=SimpleNamespace(say=messages.append),
    )
    frame._open_spotify_collection_view = lambda received, *, attempt=0: (
        LiteFrame._open_spotify_collection_view(
            frame,
            received,
            attempt=attempt,
        )
    )
    original_call_later = getattr(gui_module.wx, "CallLater", None)
    gui_module.wx.CallLater = (
        lambda _milliseconds, callback: scheduled.append(callback)
    )
    try:
        LiteFrame._open_spotify_collection_view(frame, intent)
        submissions[0][3](HostError(
            "Trwa odczyt informacji. Powtórz skrót za chwilę.",
            code="operation_busy",
        ))

        assert messages == []
        assert len(scheduled) == 1
        scheduled[0]()
        assert len(submissions) == 2
        assert frame._spotify_navigation_version == 2
    finally:
        if original_call_later is None:
            del gui_module.wx.CallLater
        else:
            gui_module.wx.CallLater = original_call_later


def test_new_spotify_enter_cancels_an_older_busy_retry() -> None:
    submissions = []
    scheduled = []
    first = OpenSpotifyContainer(
        "album-one", "one", "Pierwszy album", "album"
    )
    second = OpenSpotifyContainer(
        "album-two", "two", "Drugi album", "album"
    )
    frame = SimpleNamespace(
        client=SimpleNamespace(spotify_container_items=lambda **_values: {}),
        _spotify_navigation_version=0,
        navigator=SimpleNamespace(active=SessionId.SPOTIFY),
        runner=SimpleNamespace(submit=lambda *args: submissions.append(args)),
        announcer=SimpleNamespace(say=lambda _message: None),
    )
    frame._open_spotify_container = lambda received, *, attempt=0: (
        LiteFrame._open_spotify_container(frame, received, attempt=attempt)
    )
    original_call_later = getattr(gui_module.wx, "CallLater", None)
    gui_module.wx.CallLater = (
        lambda _milliseconds, callback: scheduled.append(callback)
    )
    try:
        LiteFrame._open_spotify_container(frame, first)
        submissions[0][3](HostError("Trwa odczyt", code="operation_busy"))
        LiteFrame._open_spotify_container(frame, second)

        assert len(submissions) == 2
        assert frame._spotify_navigation_version == 2
        scheduled[0]()
        assert len(submissions) == 2
    finally:
        if original_call_later is None:
            del gui_module.wx.CallLater
        else:
            gui_module.wx.CallLater = original_call_later


def test_spotify_playback_is_handed_to_librespot_without_committing_early() -> None:
    host_calls = []
    restored = []
    messages = []
    refreshed = []
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_play=lambda **values: host_calls.append(values) or {"ok": True}
        ),
        navigator=SimpleNamespace(
            restore_spotify_playback_after_failed_handoff=(
                lambda item_id, title: restored.append((item_id, title))
            )
        ),
        announcer=SimpleNamespace(say=messages.append),
        runner=ImmediateRunner(),
        options=SimpleNamespace(volume=37),
        _pending_spotify_playback=None,
        _pending_playback_session=None,
        _refresh_status=lambda: refreshed.append(True),
    )
    intent = PlaySpotifyItem(
        "new", "Nowy utwór", "private", "track",
        previous_item_id="old", previous_title="Poprzedni utwór",
    )

    LiteFrame._play_spotify(frame, intent)

    assert host_calls == [{
        "item_id": "new",
        "title": "Nowy utwór",
        "external_id": "private",
        "kind": "track",
        "volume": 37,
    }]
    assert frame._pending_spotify_playback is intent
    assert frame._pending_playback_session is SessionId.SPOTIFY
    assert restored == []
    assert messages == []
    assert refreshed == [True]


def test_spotify_started_event_commits_the_pending_item() -> None:
    committed = []
    intent = PlaySpotifyItem("new", "Nowy utwór", "private", "track")
    frame = SimpleNamespace(
        _window_alive=lambda: True,
        _pending_spotify_playback=intent,
        _pending_playback_session=SessionId.SPOTIFY,
        _playing_session=None,
        _playing_sessions=set(),
        navigator=SimpleNamespace(
            note_spotify_playback_started=(
                lambda item_id, title: committed.append((item_id, title))
            )
        ),
        announcer=SimpleNamespace(say=lambda _message: None),
    )

    LiteFrame._handle_engine_event(frame, "playback.started", {
        "engine": "spotify",
        "id": "technical-host-id",
        "title": "Techniczny tytuł",
    })

    assert committed == [("new", "Nowy utwór")]
    assert frame._pending_spotify_playback is None
    assert frame._pending_playback_session is None
    assert frame._playing_session is SessionId.SPOTIFY
    assert frame._playing_sessions == {SessionId.SPOTIFY}


def test_spotify_failed_event_restores_prior_item_and_list_context() -> None:
    restored = []
    messages = []
    intent = PlaySpotifyItem(
        "new", "Nowy utwór", "private", "track",
        previous_item_id="old", previous_title="Poprzedni utwór",
    )
    frame = SimpleNamespace(
        _window_alive=lambda: True,
        _pending_spotify_playback=intent,
        _pending_playback_session=SessionId.SPOTIFY,
        _playing_session=SessionId.SPOTIFY,
        _playing_sessions={SessionId.SPOTIFY},
        navigator=SimpleNamespace(
            restore_spotify_playback_after_failed_handoff=(
                lambda item_id, title: restored.append((item_id, title))
            )
        ),
        announcer=SimpleNamespace(say=messages.append),
    )

    LiteFrame._handle_engine_event(frame, "playback.failed", {
        "engine": "spotify",
        "message": "Brak połączenia",
    })

    assert restored == [("old", "Poprzedni utwór")]
    assert frame._pending_spotify_playback is None
    assert frame._pending_playback_session is None
    assert SessionId.SPOTIFY not in frame._playing_sessions
    assert messages == ["Nie udało się odtworzyć Spotify: Brak połączenia"]
