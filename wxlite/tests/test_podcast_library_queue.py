"""Biblioteka i kolejka podcastów nie mogą wpadać do operacji plikowych."""

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


def _submit(_name, work, done, failed):
    try:
        done(work())
    except Exception as error:  # pragma: no cover - wyłącznie ścieżka atrapy
        failed(error)


def test_ctrl_shift_l_on_episodes_targets_each_parent_once() -> None:
    rows = [
        Row("episode-1", "Pierwszy", "episode", parent_id="podcast-1"),
        Row("episode-2", "Drugi", "episode", parent_id="podcast-1"),
        Row("episode-3", "Trzeci", "episode", parent_id="podcast-2"),
    ]
    state = SimpleNamespace(
        view=View.LIST,
        library_view=LibraryView.PODCAST_INBOX,
        library_playlist_id=None,
        model=ListModel(),
    )
    calls = []
    reloaded = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.PODCASTS,
            sessions={SessionId.PODCASTS: state},
        ),
        client=SimpleNamespace(
            toggle_podcast_library=lambda ids: calls.append(list(ids))
            or {"added": True, "changed": 2}
        ),
        runner=SimpleNamespace(submit=_submit),
        announcer=SimpleNamespace(say=lambda text: None),
        _podcast_library_pending=False,
        _selected_action_rows=lambda: rows,
        _open_podcast_library=lambda **_kwargs: None,
        _reload_podcast_list_after_download=lambda preferred, message: (
            reloaded.append((preferred, message)) or True
        ),
    )

    gui.LiteFrame._toggle_podcast_library(frame)

    assert calls == [["podcast-1", "podcast-2"]]
    assert reloaded == [("episode-1", "Dodano do Biblioteki: 3 elementy")]
    assert not frame._podcast_library_pending


def test_removing_open_podcast_returns_to_main_library() -> None:
    row = Row("episode-1", "Odcinek", "episode", parent_id="podcast-1")
    state = SimpleNamespace(
        view=View.LIST,
        library_view=LibraryView.PODCAST_EPISODES,
        library_playlist_id="podcast-1",
        model=ListModel(),
    )
    opened = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.PODCASTS,
            sessions={SessionId.PODCASTS: state},
        ),
        client=SimpleNamespace(
            toggle_podcast_library=lambda _ids: {"added": False, "changed": 1}
        ),
        runner=SimpleNamespace(submit=_submit),
        announcer=SimpleNamespace(say=lambda text: None),
        _podcast_library_pending=False,
        _selected_action_rows=lambda: [row],
        _open_podcast_library=lambda **kwargs: opened.append(kwargs),
        _reload_podcast_list_after_download=lambda *_args: False,
    )

    gui.LiteFrame._toggle_podcast_library(frame)

    assert state.library_view is LibraryView.PODCAST_LIBRARY
    assert state.library_playlist_id is None
    assert opened == [{"completion_message": "Usunięto z Biblioteki: Odcinek"}]


def test_podcast_queue_sends_only_episode_ids_and_keeps_local_queue_separate() -> None:
    rows = [
        Row("episode-1", "Pierwszy", "episode", parent_id="podcast-1"),
        Row("podcast-1", "Podcast", "podcast"),
    ]
    state = SimpleNamespace(
        view=View.LIST,
        library_view=LibraryView.PODCAST_EPISODES,
    )
    calls = []
    spoken = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.PODCASTS,
            sessions={SessionId.PODCASTS: state},
        ),
        client=SimpleNamespace(
            toggle_podcast_queue=lambda ids, play_next=False: (
                calls.append((list(ids), play_next))
                or {"added": True, "changed": 1}
            )
        ),
        runner=SimpleNamespace(submit=_submit),
        announcer=SimpleNamespace(say=spoken.append),
        _podcast_queue_pending=False,
        _selected_action_rows=lambda: rows,
        _open_podcast_aggregate=lambda *_args, **_kwargs: None,
    )

    gui.LiteFrame._toggle_podcast_queue(frame, False)

    assert calls == [(["episode-1"], False)]
    assert spoken == ["Dodano do kolejki: Pierwszy"]


def test_generic_queue_dispatches_podcasts_before_local_files() -> None:
    calls = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.PODCASTS),
        _toggle_podcast_queue=lambda play_next: calls.append(play_next),
    )

    gui.LiteFrame._toggle_queue_membership(frame, True)

    assert calls == [True]
