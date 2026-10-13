from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.list_model import Row
from amc_wx_lite.navigation import (
    LibraryView,
    SessionId,
    View,
)
from amc_wx_lite.search_catalog import SearchEntry
from amc_wx_lite.search_catalog import SearchResultAction
from amc_wx_lite.search_sources import SearchCollection
from amc_wx_lite.shortcuts import Action


def frame_stub():
    calls = []
    frame = SimpleNamespace(
        _transient_preview_return="old",
        _switch_session=lambda session: calls.append(("session", session)),
        _open_library_view=lambda intent, **kwargs: calls.append(
            ("library", intent, kwargs)
        ),
        _open_radio_view=lambda intent, **kwargs: calls.append(
            ("radio", intent, kwargs)
        ),
        _open_podcast_view=lambda intent, **kwargs: calls.append(
            ("podcast", intent, kwargs)
        ),
        _open_podcast_library=lambda preferred_id=None, **kwargs: calls.append(
            ("podcast-library", preferred_id, kwargs)
        ),
        _open_tidal_view=lambda intent, **kwargs: calls.append(
            ("tidal", intent, kwargs)
        ),
    )
    return frame, calls


def test_file_result_returns_to_all_files_and_stable_item() -> None:
    frame, calls = frame_stub()
    result = SearchEntry(
        SessionId.FILES,
        Row("file-1", "Nagranie", "track", path=r"D:\Nagranie.mp3"),
        LibraryView.ALL_FILES,
    )
    LiteFrame._open_search_result(frame, result)
    assert calls[0] == ("session", SessionId.FILES)
    intent = calls[1][1]
    assert intent.view is LibraryView.ALL_FILES
    assert intent.preferred_id == "file-1"
    assert intent.target_session_id is SessionId.FILES
    assert frame._transient_preview_return is None


def test_radio_result_returns_to_radio_library() -> None:
    frame, calls = frame_stub()
    result = SearchEntry(
        SessionId.RADIO,
        Row("radio-1", "Radio Poznań", "station", url="https://radio"),
    )
    LiteFrame._open_search_result(frame, result)
    intent = calls[1][1]
    assert calls[0] == ("session", SessionId.RADIO)
    assert calls[1][0] == "radio"
    assert intent.view is None
    assert intent.preferred_id == "radio-1"


def test_episode_result_opens_parent_and_selects_episode() -> None:
    frame, calls = frame_stub()
    result = SearchEntry(
        SessionId.PODCASTS,
        Row("episode-1", "Odcinek", "episode", parent_id="podcast-1"),
        LibraryView.PODCAST_EPISODES,
        parent_id="podcast-1",
    )
    LiteFrame._open_search_result(frame, result)
    intent = calls[1][1]
    assert calls[0] == ("session", SessionId.PODCASTS)
    assert intent.subscription_id == "podcast-1"
    assert intent.preferred_id == "episode-1"


def test_tidal_result_returns_to_collection_it_came_from() -> None:
    frame, calls = frame_stub()
    result = SearchEntry(
        SessionId.TIDAL,
        Row("tidal-1", "Album", "album"),
        LibraryView.TIDAL_LIBRARY,
    )
    LiteFrame._open_search_result(frame, result)
    intent = calls[1][1]
    assert calls[0] == ("session", SessionId.TIDAL)
    assert intent.view is LibraryView.TIDAL_LIBRARY
    assert intent.preferred_id == "tidal-1"


def test_search_from_player_is_refused_with_the_full_amc_message() -> None:
    messages = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(view=View.PLAYER),
        announcer=SimpleNamespace(say=messages.append),
    )
    LiteFrame._show_search(frame, all_services=False)
    assert messages == ["Wyszukiwanie jest dostępne na listach"]


def test_search_favorite_uses_the_same_command_as_the_real_list() -> None:
    opened = []
    dispatched = []
    frame = SimpleNamespace(
        _open_search_result=lambda entry, **kwargs: opened.append((entry, kwargs)),
        _dispatch=dispatched.append,
    )
    result = SearchEntry(
        SessionId.FILES,
        Row("file-1", "Nagranie", "track", path=r"D:\Nagranie.mp3"),
        LibraryView.ALL_FILES,
    )
    LiteFrame._complete_search_result_action(
        frame,
        result,
        [result],
        SearchResultAction.FAVORITE,
    )
    assert opened[0][1]["selected_ids"] == ["file-1"]
    opened[0][1]["after_open"]()
    assert dispatched == [Action.TOGGLE_FAVORITE]


def test_search_open_does_not_invent_a_second_action() -> None:
    opened = []
    frame = SimpleNamespace(_open_search_result=opened.append)
    result = SearchEntry(SessionId.RADIO, Row("r", "Radio", "station"))
    LiteFrame._complete_search_result_action(
        frame,
        result,
        [result],
        SearchResultAction.OPEN,
    )
    assert opened == [result]


def test_podcast_search_combines_cached_and_public_results() -> None:
    shown = []
    searched = []
    local = SearchEntry(
        SessionId.PODCASTS,
        Row("saved", "Zapisany podcast", "podcast", url="https://saved.test/feed"),
        LibraryView.PODCAST_LIBRARY,
    )

    class Runner:
        @staticmethod
        def submit(_name, work, done, _failed):
            done(work())

    frame = SimpleNamespace(
        search_sources=SimpleNamespace(
            collect=lambda _sessions: SearchCollection((local,), ())
        ),
        client=SimpleNamespace(
            search_podcast_directories=lambda query: (
                searched.append(query)
                or {
                    "items": [{
                        "id": "remote",
                        "title": "Nowy kanał",
                        "artist": "Autor",
                        "kind": "podcast",
                        "remoteKind": "rss",
                        "address": "https://remote.test/feed",
                        "detail": "Apple Podcasts",
                    }],
                    "warnings": [],
                }
            )
        ),
        runner=Runner(),
        _search_dialog_alive=lambda _dialog: True,
    )
    dialog = SimpleNamespace(
        catalog=None,
        show_results=lambda entries, warnings: shown.append((entries, warnings)),
        search_failed=lambda: shown.append("failed"),
    )

    LiteFrame._run_search_query(
        frame,
        "podcast",
        dialog,
        all_services=False,
        session_before=SessionId.PODCASTS,
    )

    assert searched == ["podcast"]
    assert [entry.row.title for entry in shown[0][0]] == [
        "Zapisany podcast",
        "Nowy kanał",
    ]
    assert shown[0][1] == ()
    assert dialog.catalog.entries == (local,)


def test_public_search_failure_preserves_cached_results() -> None:
    shown = []
    local = SearchEntry(
        SessionId.PODCASTS,
        Row("saved", "Audycja", "podcast", url="https://saved.test/feed"),
        LibraryView.PODCAST_LIBRARY,
    )

    class Runner:
        @staticmethod
        def submit(_name, work, done, _failed):
            done(work())

    def unavailable(_query):
        raise ValueError("technical details must not be spoken")

    frame = SimpleNamespace(
        search_sources=SimpleNamespace(
            collect=lambda _sessions: SearchCollection((local,), ())
        ),
        client=SimpleNamespace(search_podcast_directories=unavailable),
        runner=Runner(),
        _search_dialog_alive=lambda _dialog: True,
    )
    dialog = SimpleNamespace(
        catalog=None,
        show_results=lambda entries, warnings: shown.append((entries, warnings)),
        search_failed=lambda: shown.append("failed"),
    )

    LiteFrame._run_search_query(
        frame,
        "audycja",
        dialog,
        all_services=False,
        session_before=SessionId.PODCASTS,
    )

    assert [entry.row.item_id for entry in shown[0][0]] == ["saved"]
    assert shown[0][1] == (
        "Nie udało się przeszukać publicznych katalogów podcastów i YouTube",
    )
    assert "technical" not in shown[0][1][0]


def test_remote_result_uses_materialization_instead_of_local_navigation() -> None:
    calls = []
    frame = SimpleNamespace(
        _complete_remote_search_result_action=lambda entries, action: calls.append(
            (entries, action)
        )
    )
    result = SearchEntry(
        SessionId.PODCASTS,
        Row(
            "remote-id",
            "Kanał",
            "podcast",
            url="https://www.youtube.com/channel/UCexample/videos",
        ),
        LibraryView.PODCAST_LIBRARY,
        remote_kind="youtubeChannel",
    )

    LiteFrame._complete_search_result_action(
        frame,
        result,
        [result],
        SearchResultAction.OPEN,
    )

    assert calls == [([result], SearchResultAction.OPEN)]


def test_remote_youtube_queue_materializes_then_uses_real_list_action() -> None:
    calls = []
    selected = []
    dispatched = []

    class Runner:
        @staticmethod
        def submit(_name, work, done, _failed):
            done(work())

    client = SimpleNamespace(
        add_podcast_source=lambda address, title: (
            calls.append(("add", address, title))
            or {
                "subscriptionId": "internet-media",
                "preferredEpisodeId": "saved-episode",
                "title": title,
            }
        )
    )
    opened = []
    frame = SimpleNamespace(
        _podcast_add_pending=False,
        client=client,
        status_field=SimpleNamespace(SetLabel=lambda value: calls.append(("status", value))),
        status_bar=SimpleNamespace(show=lambda value: calls.append(("bar", value))),
        announcer=SimpleNamespace(say=lambda value: calls.append(("say", value))),
        runner=Runner(),
        _switch_session=lambda session: calls.append(("session", session)),
        _open_podcast_view=lambda intent, **kwargs: opened.append((intent, kwargs)),
        _active_list=lambda: SimpleNamespace(
            select_item_ids=lambda values: selected.extend(values)
        ),
        _dispatch=dispatched.append,
    )
    result = SearchEntry(
        SessionId.PODCASTS,
        Row(
            "remote-video",
            "Materiał",
            "episode",
            url="https://www.youtube.com/watch?v=abc123",
        ),
        LibraryView.PODCAST_EPISODES,
        parent_id="remote:internet-media",
        remote_kind="youtubeVideo",
    )

    LiteFrame._complete_remote_search_result_action(
        frame,
        [result],
        SearchResultAction.QUEUE,
    )

    assert ("add", result.row.url, "Materiał") in calls
    assert opened[0][0].subscription_id == "internet-media"
    assert opened[0][0].preferred_id == "saved-episode"
    opened[0][1]["after_refresh"]()
    assert selected == ["saved-episode"]
    assert dispatched == [Action.ADD_TO_QUEUE]
    assert frame._podcast_add_pending is False


def test_remote_podcast_favorite_is_added_then_favorited_without_navigation() -> None:
    calls = []

    class Runner:
        @staticmethod
        def submit(_name, work, done, _failed):
            done(work())

    client = SimpleNamespace(
        add_podcast_source=lambda _address, title: {
            "subscriptionId": "saved-podcast",
            "preferredEpisodeId": None,
            "title": title,
        },
        toggle_podcast_favorites=lambda subscriptions, episodes: calls.append(
            ("favorite", subscriptions, episodes)
        ),
    )
    frame = SimpleNamespace(
        _podcast_add_pending=False,
        client=client,
        status_field=SimpleNamespace(SetLabel=lambda value: calls.append(("status", value))),
        status_bar=SimpleNamespace(show=lambda value: calls.append(("bar", value))),
        announcer=SimpleNamespace(say=lambda value: calls.append(("say", value))),
        runner=Runner(),
    )
    result = SearchEntry(
        SessionId.PODCASTS,
        Row(
            "remote-podcast",
            "Podcast",
            "podcast",
            url="https://example.test/feed.xml",
        ),
        LibraryView.PODCAST_LIBRARY,
        remote_kind="rss",
    )

    LiteFrame._complete_remote_search_result_action(
        frame,
        [result],
        SearchResultAction.FAVORITE,
    )

    assert ("favorite", ["saved-podcast"], []) in calls
    assert ("say", "Dodano do ulubionych: Podcast") in calls
    assert frame._podcast_add_pending is False


def test_search_dialog_intercepts_enter_before_default_ok_processing() -> None:
    source = Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"
    text = source.read_text(encoding="utf-8")
    dialog = text[
        text.index("class SearchDialog") :
        text.index("class GeneralPlaybackOptionsDialog")
    ]
    assert "self.Bind(wx.EVT_CHAR_HOOK, self._on_dialog_shortcut_hook)" in dialog
    assert "if focus is self.query:" in dialog
    assert "self._on_query_key(event)" in dialog
    assert "if focus is self.results:" in dialog
