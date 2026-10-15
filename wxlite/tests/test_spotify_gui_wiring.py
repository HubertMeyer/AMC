from __future__ import annotations

from types import SimpleNamespace

import amc_wx_lite.gui as gui_module
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.host_client import HostError
from amc_wx_lite.list_model import Row
from amc_wx_lite.navigation import (
    Announce,
    LibraryView,
    Navigator,
    OpenSpotifyCollectionView,
    OpenSpotifyContainer,
    OpenSpotifyView,
    PlaySpotifyItem,
    SessionId,
    ShowSpotifyRelations,
    SpotifyRelationChoice,
)
from amc_wx_lite.shortcuts import Action
from amc_wx_lite.state_store import LiteState


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


def test_spotify_sort_reloads_first_page_without_adding_a_history_level() -> None:
    opened = []
    spoken = []
    context = OpenSpotifyCollectionView(
        "spotify-collection:liked", "liked", "Polubione utwory"
    )
    session = SimpleNamespace(
        view=gui_module.View.LIST,
        spotify_context=context,
        model=SimpleNamespace(selected_id="private-track-row"),
    )
    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.SPOTIFY,
            sessions={SessionId.SPOTIFY: session},
        ),
        state=LiteState(),
        _spotify_effective_sort_modes={"liked": "AddedNewest"},
        _spotify_loaded_counts={"liked": 300},
        _save_state=lambda: True,
        _refresh_menu_state=lambda: None,
        _open_spotify_collection_view=opened.append,
        announcer=SimpleNamespace(say=spoken.append),
    )

    LiteFrame._set_spotify_collection_sort(
        frame,
        Action.SORT_SPOTIFY_COLLECTION_ALPHABETICAL,
    )

    assert frame.state.spotify_sort_modes == {"liked": "Alphabetical"}
    assert frame._spotify_loaded_counts == {}
    assert spoken == ["Alfabetycznie"]
    assert opened == [OpenSpotifyCollectionView(
        "spotify-collection:liked",
        "liked",
        "Polubione utwory",
        preferred_id="private-track-row",
        replace_current=True,
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


def test_spotify_collection_view_requests_first_page_and_adds_load_more_row() -> None:
    calls = []
    intent = OpenSpotifyCollectionView(
        "spotify-collection:artists", "artists", "Wykonawcy"
    )
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_collection_view=lambda view, *, loaded_count, sort_mode: (
                calls.append(("host", view, loaded_count, sort_mode))
                or {
                    "heading": "Wykonawcy Spotify",
                    "items": [],
                    "warning": "",
                    "hasMore": True,
                }
            )
        ),
        _spotify_navigation_version=0,
        _spotify_loaded_counts={},
        navigator=SimpleNamespace(
            active=SessionId.SPOTIFY,
            apply_spotify_collection_view=lambda received, heading, rows, preferred_id=None: (
                calls.append(("apply", received, heading, rows, preferred_id)) or []
            ),
        ),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=lambda message: calls.append(("say", message))),
        _run=lambda events: calls.append(("run", events)),
    )

    LiteFrame._open_spotify_collection_view(frame, intent)

    assert calls[0] == ("host", "artists", 150, "AddedNewest")
    assert calls[1][0:3] == ("apply", intent, "Wykonawcy Spotify")
    assert [row.title for row in calls[1][3]] == ["Załaduj więcej"]
    assert calls[1][4] is None


def test_spotify_load_more_requests_next_page_and_focuses_first_new_item() -> None:
    calls = []
    intent = OpenSpotifyCollectionView(
        "spotify-collection:liked",
        "liked",
        "Polubione utwory",
        load_more=True,
    )
    items = [
        {
            "id": f"private-row-{index}",
            "externalId": f"track{index}",
            "title": f"Utwór {index}",
            "kind": "track",
        }
        for index in range(151)
    ]
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_collection_view=lambda view, *, loaded_count, sort_mode: (
                calls.append(("host", view, loaded_count, sort_mode))
                or {
                    "heading": "Polubione utwory Spotify",
                    "items": items,
                    "warning": "",
                    "hasMore": False,
                }
            )
        ),
        _spotify_navigation_version=0,
        _spotify_loaded_counts={"liked": 150},
        navigator=SimpleNamespace(
            active=SessionId.SPOTIFY,
            apply_spotify_collection_view=(
                lambda received, heading, rows, preferred_id=None: (
                    calls.append(("apply", received, heading, rows, preferred_id))
                    or []
                )
            ),
        ),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=lambda message: calls.append(("say", message))),
        _run=lambda events: calls.append(("run", events)),
    )

    LiteFrame._open_spotify_collection_view(frame, intent)

    assert calls[0] == ("host", "liked", 300, "AddedNewest")
    assert calls[1][0:3] == (
        "apply",
        intent,
        "Polubione utwory Spotify",
    )
    assert len(calls[1][3]) == 151
    assert calls[1][4] == "private-row-150"
    assert frame._spotify_loaded_counts == {"liked": 151}


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


def test_unavailable_spotify_playlist_stays_on_the_current_list() -> None:
    applied = []
    spoken = []
    intent = OpenSpotifyContainer(
        "private-playlist-row", "privateplaylist", "Moja playlista", "playlist"
    )
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_container_items=lambda **_values: {
                "heading": "Playlista, Moja playlista",
                "items": [],
                "warning": "Spotify nie udostępnił zawartości tego elementu.",
                "available": False,
            }
        ),
        _spotify_navigation_version=0,
        navigator=SimpleNamespace(
            active=SessionId.SPOTIFY,
            apply_spotify_container=lambda *_args: applied.append(True) or [],
        ),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=spoken.append),
        _run=lambda events: applied.append(events),
    )

    LiteFrame._open_spotify_container(frame, intent)

    assert applied == []
    assert spoken == ["Spotify nie udostępnił zawartości tego elementu."]


def test_spotify_right_arrow_uses_two_real_destinations_without_context_menu() -> None:
    created = []
    activated = []
    run = []
    focused = []
    choices = (
        SpotifyRelationChoice(
            "Przejdź do albumu",
            OpenSpotifyContainer("album", "album-id", "Album", "album"),
        ),
        SpotifyRelationChoice(
            "Przejdź do wykonawcy",
            OpenSpotifyContainer("artist", "artist-id", "Wykonawca", "artist"),
        ),
    )
    intent = ShowSpotifyRelations("Przejdź do", choices)

    class FakeDialog:
        def __init__(self, _parent, *, title, labels):
            self.selected_index = len(created) % 2
            created.append((title, labels, self.selected_index))

        @staticmethod
        def ShowModal():
            return gui_module.wx.ID_OK

        @staticmethod
        def Destroy():
            return None

    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            activate_spotify_relation=(
                lambda choice: activated.append(choice) or [choice.label]
            )
        ),
        _active_list=lambda: SimpleNamespace(SetFocus=lambda: focused.append(True)),
        _run=run.append,
    )
    original_dialog = gui_module.RelationDestinationDialog
    original_call_after = gui_module.wx.CallAfter
    gui_module.RelationDestinationDialog = FakeDialog
    gui_module.wx.CallAfter = lambda callback: callback()
    try:
        LiteFrame._show_spotify_relations(frame, intent)
        LiteFrame._show_spotify_relations(frame, intent)
    finally:
        gui_module.RelationDestinationDialog = original_dialog
        gui_module.wx.CallAfter = original_call_after

    assert created == [
        ("Przejdź do", ("Przejdź do albumu", "Przejdź do wykonawcy"), 0),
        ("Przejdź do", ("Przejdź do albumu", "Przejdź do wykonawcy"), 1),
    ]
    assert activated == [choices[0], choices[1]]
    assert run == [["Przejdź do albumu"], ["Przejdź do wykonawcy"]]
    assert focused == [True, True]


def test_busy_spotify_collection_enter_is_retried_without_speaking_error() -> None:
    submissions = []
    scheduled = []
    messages = []
    intent = OpenSpotifyCollectionView(
        "spotify-collection:artists", "artists", "Wykonawcy"
    )
    frame = SimpleNamespace(
        client=SimpleNamespace(
            spotify_collection_view=lambda _view, *, loaded_count, sort_mode: {}
        ),
        _spotify_navigation_version=0,
        _spotify_loaded_counts={},
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
    recorded = []
    intent = PlaySpotifyItem("new", "Nowy utwór", "private", "track")
    confirmed = Row(
        "new", "Nowy utwór", "track",
        service_id="private", service_kind="track",
    )
    frame = SimpleNamespace(
        _window_alive=lambda: True,
        _pending_spotify_playback=intent,
        _pending_playback_session=SessionId.SPOTIFY,
        _playing_session=None,
        _playing_sessions=set(),
        navigator=SimpleNamespace(
            note_spotify_playback_started=(
                lambda item_id, title: (
                    committed.append((item_id, title)) or confirmed
                )
            )
        ),
        _record_spotify_history=recorded.append,
        announcer=SimpleNamespace(say=lambda _message: None),
    )

    LiteFrame._handle_engine_event(frame, "playback.started", {
        "engine": "spotify",
        "id": "technical-host-id",
        "title": "Techniczny tytuł",
    })

    assert committed == [("new", "Nowy utwór")]
    assert recorded == [confirmed]
    assert frame._pending_spotify_playback is None
    assert frame._pending_playback_session is None
    assert frame._playing_session is SessionId.SPOTIFY
    assert frame._playing_sessions == {SessionId.SPOTIFY}


def test_spotify_started_event_announces_default_output_fallback_once() -> None:
    messages = []
    frame = SimpleNamespace(
        _window_alive=lambda: True,
        _pending_spotify_playback=None,
        _pending_playback_session=SessionId.SPOTIFY,
        _playing_session=None,
        _playing_sessions=set(),
        navigator=SimpleNamespace(
            note_spotify_playback_started=lambda _item_id, _title: None
        ),
        announcer=SimpleNamespace(say=messages.append),
    )

    LiteFrame._handle_engine_event(frame, "playback.started", {
        "engine": "spotify",
        "id": "track-1",
        "title": "Utwór",
        "audioOutputFallbackDeviceName": (
            "Cyfrowy interfejs audio (PMA-1700NE)"
        ),
    })

    assert messages == [
        "Zapamiętane urządzenie audio Cyfrowy interfejs audio "
        "(PMA-1700NE) jest niedostępne. Spotify odtwarza na "
        "domyślnym urządzeniu systemowym"
    ]


def test_ctrl_h_in_spotify_opens_its_own_history_not_local_files() -> None:
    navigator = Navigator()
    navigator.active = SessionId.SPOTIFY
    navigator.apply_spotify_view("Biblioteka Spotify", [Row(
        "album", "Album", "album",
        service_id="album-private", service_kind="album",
    )])
    events = []
    frame = SimpleNamespace(
        navigator=navigator,
        state=LiteState(spotify_playback_history=[{
            "itemId": "track-row",
            "externalId": "track-private",
            "title": "Utwór z historii",
            "kind": "track",
            "artist": "Wykonawca",
        }]),
        _begin_transient_preview=lambda: None,
        _run=events.append,
    )

    LiteFrame._show_playback_history_preview(frame)

    assert navigator.active is SessionId.SPOTIFY
    assert navigator.session.library_view is LibraryView.SPOTIFY_HISTORY
    assert navigator.session.model.selected_row.title == "Utwór z historii"
    assert events == [[Announce("Spotify — Historia odtwarzania, 1 pozycja")]]


def test_confirmed_spotify_history_is_persisted_and_deduplicated() -> None:
    saves = []
    state = LiteState()
    frame = SimpleNamespace(
        state=state,
        _save_state=lambda: saves.append(True) or True,
    )
    first = Row(
        "row-1", "Pierwszy", "track",
        service_id="external-1", service_kind="track",
    )
    second = Row(
        "row-2", "Drugi", "track",
        service_id="external-2", service_kind="track",
    )

    LiteFrame._record_spotify_history(frame, first)
    LiteFrame._record_spotify_history(frame, second)
    LiteFrame._record_spotify_history(frame, first)

    assert [
        item["title"] for item in state.spotify_playback_history
    ] == ["Pierwszy", "Drugi"]
    assert saves == [True, True, True]


def test_delete_in_spotify_history_removes_only_history_and_keeps_focus() -> None:
    messages = []
    saves = []
    synced = []
    state = LiteState(spotify_playback_history=[
        {
            "itemId": "row-1",
            "externalId": "external-1",
            "title": "Pierwszy",
            "kind": "track",
        },
        {
            "itemId": "row-2",
            "externalId": "external-2",
            "title": "Drugi",
            "kind": "track",
        },
    ])
    navigator = Navigator()
    navigator.active = SessionId.SPOTIFY
    navigator.apply_spotify_history(list(
        gui_module.spotify_history_rows(state.spotify_playback_history)
    ))
    selected = navigator.session.model.rows[0]
    frame = SimpleNamespace(
        navigator=navigator,
        state=state,
        announcer=SimpleNamespace(say=messages.append),
        _selected_action_rows=lambda: [selected],
        _save_state=lambda: saves.append(True) or True,
        _sync_views=lambda: synced.append(True),
    )
    frame._remove_spotify_history_entries = (
        lambda: LiteFrame._remove_spotify_history_entries(frame)
    )

    assert LiteFrame._action_available_in_active_session(
        frame, Action.REMOVE_SELECTED
    )
    LiteFrame._remove_selected_items(frame)

    assert [
        item["title"] for item in state.spotify_playback_history
    ] == ["Drugi"]
    assert navigator.session.model.selected_row.title == "Drugi"
    assert saves == [True]
    assert synced == [True]
    assert messages == [
        "Usunięto z Historii Spotify: Pierwszy. "
        "Biblioteka Spotify pozostała bez zmian"
    ]


def test_delete_remains_unavailable_in_spotify_library() -> None:
    navigator = Navigator()
    navigator.active = SessionId.SPOTIFY
    navigator.apply_spotify_view("Biblioteka Spotify", [Row(
        "track", "Utwór", "track",
        service_id="external", service_kind="track",
    )])
    frame = SimpleNamespace(navigator=navigator)

    assert not LiteFrame._action_available_in_active_session(
        frame, Action.REMOVE_SELECTED
    )


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
