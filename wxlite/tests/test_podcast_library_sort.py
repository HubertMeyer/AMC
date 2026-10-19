"""POD-001: one accessible contract for sorting the source library."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

from amc_wx_lite import menu_model
from amc_wx_lite.command_palette import available_entries, entries_for_session
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.list_model import Row
from amc_wx_lite.navigation import LibraryView, Navigator, SessionId, View
from amc_wx_lite.podcast_source import (
    SORT_ADDED_NEWEST,
    SORT_ALPHABETICAL,
    SORT_CUSTOM,
    PodcastSource,
    subscription_rows,
)
from amc_wx_lite.profile_layout import private_sandbox
from amc_wx_lite.shortcuts import Action, Chord, describe, resolve
from amc_wx_lite.state_store import LiteState, StateStore


def _database(base: Path) -> Path:
    path = base / "podcasts.db"
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE podcast_subscriptions (
            id TEXT PRIMARY KEY, ordinal INTEGER NOT NULL, title TEXT NOT NULL,
            feed_url TEXT NOT NULL, is_in_library INTEGER NOT NULL,
            last_refresh_utc_ticks INTEGER NOT NULL, content_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    values = [
        ("youtube", 0, "Żuraw", 2),
        ("podcast", 1, "Alfa", 0),
        ("internet", 2, "Łódź", 1),
        ("hidden", 3, "Ukryty", 3),
    ]
    connection.executemany(
        "INSERT INTO podcast_subscriptions VALUES (?, ?, ?, ?, ?, 0, '', ?)",
        [
            (
                item_id,
                ordinal,
                title,
                f"https://example.invalid/{item_id}",
                0 if item_id == "hidden" else 1,
                json.dumps({"SourceKind": kind}),
            )
            for item_id, ordinal, title, kind in values
        ],
    )
    connection.commit()
    connection.close()
    return path


class _PolishCollation:
    def __init__(self) -> None:
        self.called = False

    def sort_rows(self, rows, *, key, mode):
        assert mode == "TITLE_IGNORE_CASE"
        self.called = True
        order = {"Alfa": 0, "Łódź": 1, "Żuraw": 2}
        return sorted(rows, key=lambda row: order[key(row)])


def _ids(items) -> list[str]:
    return [item.subscription_id for item in items]


def test_three_source_orders_are_read_only_and_do_not_mix_source_types(
    tmp_path: Path,
) -> None:
    database = _database(tmp_path)
    source = PodcastSource(private_sandbox(tmp_path))
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    collation = _PolishCollation()

    custom, custom_exact = source.ordered_subscriptions(SORT_CUSTOM)
    added, added_exact = source.ordered_subscriptions(SORT_ADDED_NEWEST)
    alphabetical, alphabetical_exact = source.ordered_subscriptions(
        SORT_ALPHABETICAL,
        collation=collation,
    )

    assert _ids(custom) == ["youtube", "podcast", "internet"]
    assert _ids(added) == ["internet", "podcast", "youtube"]
    assert _ids(alphabetical) == ["podcast", "internet", "youtube"]
    assert custom_exact and added_exact and alphabetical_exact and collation.called
    rows = subscription_rows(custom)
    assert [row.detail for row in rows] == [
        "kanał YouTube", "podcast", "media internetowe",
    ]
    assert all(row.kind == "podcast" for row in rows)
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_unknown_mode_preserves_custom_order_and_alphabetical_fallback_is_named(
    tmp_path: Path,
) -> None:
    _database(tmp_path)
    source = PodcastSource(private_sandbox(tmp_path))

    unknown, exact = source.ordered_subscriptions("Technical.Enum.Value")
    alphabetical, alphabetical_exact = source.ordered_subscriptions(
        SORT_ALPHABETICAL
    )

    assert _ids(unknown) == ["youtube", "podcast", "internet"]
    assert exact
    assert _ids(alphabetical) == ["podcast", "internet", "youtube"]
    assert not alphabetical_exact


def test_sort_refresh_preserves_stable_selection_and_speaks_mode_name_position() -> None:
    navigator = Navigator()
    first = [
        Row("youtube", "Żuraw", "podcast"),
        Row("podcast", "Alfa", "podcast"),
        Row("internet", "Łódź", "podcast"),
    ]
    navigator.apply_podcast_library(first, preferred_id="youtube")
    sorted_rows = [first[1], first[2], first[0]]

    events = navigator.apply_podcast_library(
        sorted_rows,
        preferred_id="youtube",
        sort_label="Alfabetycznie",
    )

    state = navigator.sessions[SessionId.PODCASTS]
    assert state.model.selected_id == "youtube"
    assert state.model.selected_index == 2
    assert events[0].text == "Alfabetycznie. Żuraw, 3 z 3"
    assert "Row(" not in events[0].text and "podcast" not in events[0].text


def test_private_sort_choice_round_trips_and_rejects_technical_values(
    tmp_path: Path,
) -> None:
    store = StateStore(tmp_path / "state")
    store.save(LiteState(podcast_library_sort_mode=SORT_ALPHABETICAL))
    assert store.load().podcast_library_sort_mode == SORT_ALPHABETICAL

    store.path.write_text(json.dumps({
        "podcast_library_sort_mode": "CollectionSortMode.Custom { value = 1 }",
    }), encoding="utf-8")
    loaded = store.load()
    assert loaded.podcast_library_sort_mode is None
    store.save(loaded)
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert "podcast_library_sort_mode" not in payload


def test_alt_digits_resolve_by_exact_podcast_view() -> None:
    library = {
        "1": Action.SORT_PODCAST_LIBRARY_ADDED,
        "2": Action.SORT_PODCAST_LIBRARY_ALPHABETICAL,
        "3": Action.SORT_PODCAST_LIBRARY_CUSTOM,
    }
    inbox = {
        "1": Action.SORT_PODCAST_INBOX_ADDED,
        "2": Action.SORT_PODCAST_INBOX_ALPHABETICAL,
        "3": Action.SORT_PODCAST_INBOX_BY_PODCAST,
    }
    for key in library:
        chord = Chord(key, alt=True)
        assert resolve(
            chord,
            player_view=False,
            radio_session=False,
            podcast_session=True,
            podcast_library=True,
        ) is library[key]
        assert resolve(
            chord,
            player_view=False,
            radio_session=False,
            podcast_session=True,
            podcast_inbox=True,
        ) is inbox[key]
        assert resolve(
            chord,
            player_view=False,
            radio_session=False,
            podcast_session=True,
        ) is None

    assert resolve(
        Chord("1", alt=True),
        player_view=False,
        radio_session=False,
    ) is Action.VIEW_FOLDERS


def test_menu_palette_and_help_share_user_facing_library_sort_contract() -> None:
    actions = {
        Action.SORT_PODCAST_LIBRARY_ADDED,
        Action.SORT_PODCAST_LIBRARY_ALPHABETICAL,
        Action.SORT_PODCAST_LIBRARY_CUSTOM,
    }
    items = {
        item.action: item
        for menu in menu_model.menus_for_session(SessionId.PODCASTS)
        for item in menu.items
        if item.action in actions
    }
    assert set(items) == actions
    assert all(item.needs_podcast_library for item in items.values())
    assert all(item.checkable and not item.accelerator for item in items.values())
    assert {item.shortcut for item in items.values()} == {"Alt+1", "Alt+2", "Alt+3"}

    palette = available_entries(entries_for_session(SessionId.PODCASTS), actions)
    assert {entry.action for entry in palette} == actions
    assert all("Action." not in entry.label and "{" not in entry.label for entry in palette)

    help_rows = describe("Podcasty i YouTube", actions)
    assert len(help_rows) == 3
    assert {shortcut for shortcut, _label in help_rows} == {"Alt+1", "Alt+2", "Alt+3"}
    assert all("Biblioteka podcastów i kanałów" in label for _shortcut, label in help_rows)


def test_gui_sort_command_persists_mode_and_reopens_with_same_selected_id() -> None:
    model = SimpleNamespace(selected_id="youtube")
    podcast_state = SimpleNamespace(
        view=View.LIST,
        library_view=LibraryView.PODCAST_LIBRARY,
        model=model,
    )
    opened: list[dict] = []
    refreshed: list[bool] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.PODCASTS,
            sessions={SessionId.PODCASTS: podcast_state},
        ),
        state=SimpleNamespace(podcast_library_sort_mode=None),
        _podcast_library_sort_mode=SORT_CUSTOM,
        _save_state=lambda: True,
        _refresh_menu_state=lambda: refreshed.append(True),
        _open_podcast_library=lambda **kwargs: opened.append(kwargs),
        announcer=SimpleNamespace(say=lambda _message: None),
    )

    LiteFrame._set_podcast_library_sort(
        frame,
        Action.SORT_PODCAST_LIBRARY_ALPHABETICAL,
    )

    assert frame.state.podcast_library_sort_mode == SORT_ALPHABETICAL
    assert frame._podcast_library_sort_mode == SORT_ALPHABETICAL
    assert refreshed == [True]
    assert opened == [{
        "preferred_id": "youtube",
        "sort_label": "Alfabetycznie",
    }]

