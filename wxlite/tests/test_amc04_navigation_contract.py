from pathlib import Path

from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.menu_model import build_menus
from amc_wx_lite.navigation import Navigator, SessionId, View
from amc_wx_lite.shortcuts import Action, Chord, describe_action, resolve


def _resolved(chord: Chord, *, player: bool) -> Action | None:
    return resolve(
        chord,
        player_view=player,
        radio_session=False,
        podcast_session=False,
    )


def test_bookmarks_named_bookmarks_and_chapters_are_distinct() -> None:
    assert _resolved(Chord("B"), player=True) is Action.ADD_BOOKMARK
    assert _resolved(Chord("B", ctrl=True, shift=True), player=True) is Action.ADD_NAMED_BOOKMARK
    assert _resolved(Chord("Prior", shift=True), player=True) is Action.PREVIOUS_BOOKMARK
    assert _resolved(Chord("Next", shift=True), player=True) is Action.NEXT_BOOKMARK
    assert _resolved(
        Chord("Prior", ctrl=True, shift=True), player=True
    ) is Action.PREVIOUS_NAMED_BOOKMARK
    assert _resolved(
        Chord("Next", ctrl=True, shift=True), player=True
    ) is Action.NEXT_NAMED_BOOKMARK
    assert _resolved(
        Chord("Left", ctrl=True, shift=True), player=True
    ) is Action.PREVIOUS_CHAPTER
    assert _resolved(
        Chord("Right", ctrl=True, shift=True), player=True
    ) is Action.NEXT_CHAPTER
    assert _resolved(Chord("B", ctrl=True, alt=True), player=True) is Action.VIEW_CHAPTERS
    assert _resolved(
        Chord("B", ctrl=True, alt=True, shift=True), player=True
    ) is Action.ADD_NAMED_CHAPTER
    assert _resolved(
        Chord("Prior", ctrl=True, alt=True), player=True
    ) is Action.PREVIOUS_CHAPTER
    assert _resolved(
        Chord("Next", ctrl=True, alt=True), player=True
    ) is Action.NEXT_CHAPTER


def test_view_history_and_playback_history_have_separate_arrows() -> None:
    for player in (False, True):
        assert _resolved(Chord("Left", alt=True), player=player) is Action.VIEW_BACK
        assert _resolved(Chord("Right", alt=True), player=player) is Action.VIEW_FORWARD
    assert _resolved(Chord("Down", alt=True), player=False) is Action.MOVE_LIST_ITEM_DOWN
    assert _resolved(Chord("Up", alt=True), player=False) is Action.MOVE_LIST_ITEM_UP
    assert _resolved(
        Chord("Down", alt=True), player=True
    ) is Action.PLAYBACK_HISTORY_OLDER
    assert _resolved(
        Chord("Up", alt=True), player=True
    ) is Action.PLAYBACK_HISTORY_NEWER


def test_protocol_keeps_session_and_navigation_mode_explicit() -> None:
    calls: list[tuple[str, dict, float | None]] = []
    client = LiteHostClient(Path("host.exe"))
    client.call = lambda op, args=None, timeout=None: calls.append(
        (op, args or {}, timeout)
    ) or {}

    client.add_bookmark(
        item_id="youtube:film-1",
        item_title="Film",
        session_id="podcasts",
        name="Początek",
    )
    client.navigate_bookmark(1, session_id="podcasts", named_only=True)
    client.add_chapter("Wstęp", session_id="files")
    client.list_chapters(session_id="podcasts")
    client.navigate_chapter(-1, session_id="files")

    assert calls == [
        (
            "bookmark.add",
            {
                "sessionId": "podcasts",
                "itemId": "youtube:film-1",
                "itemTitle": "Film",
                "name": "Początek",
            },
            15.0,
        ),
        (
            "bookmark.navigate",
            {"sessionId": "podcasts", "direction": 1, "namedOnly": True},
            15.0,
        ),
        ("chapter.add", {"sessionId": "files", "name": "Wstęp"}, 20.0),
        ("chapter.list", {"sessionId": "podcasts"}, 15.0),
        ("chapter.navigate", {"sessionId": "files", "direction": -1}, 15.0),
    ]


def test_help_and_menu_use_user_labels_for_every_new_action() -> None:
    actions = {
        Action.PREVIOUS_NAMED_BOOKMARK,
        Action.NEXT_NAMED_BOOKMARK,
        Action.VIEW_CHAPTERS,
        Action.ADD_NAMED_CHAPTER,
        Action.PREVIOUS_CHAPTER,
        Action.NEXT_CHAPTER,
        Action.VIEW_BACK,
        Action.VIEW_FORWARD,
        Action.PLAYBACK_HISTORY_OLDER,
        Action.PLAYBACK_HISTORY_NEWER,
    }
    menu_actions = {
        item.action
        for menu in build_menus()
        for item in menu.items
        if item.action is not None
    }
    assert actions <= menu_actions
    for action in actions:
        label = describe_action(action)
        assert label and label != "Polecenie AMC"
        assert action.name not in label and action.value not in label


def test_transient_snapshot_roundtrip_preserves_navigation_not_playback() -> None:
    navigator = Navigator()
    state = navigator.sessions[SessionId.FILES]
    state.view = View.PLAYER
    state.now_playing_id = "playing"
    state.now_playing_title = "Nagranie"
    snapshot = navigator.capture_transient_navigation()
    state.view = View.LIST
    state.now_playing_title = "Nowszy tytuł transportu"

    navigator.restore_transient_navigation(snapshot)

    assert state.view is View.PLAYER
    assert state.now_playing_title == "Nowszy tytuł transportu"
