import ast
from pathlib import Path

from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.menu_model import build_menus, menus_for_session
from amc_wx_lite.navigation import Navigator, SessionId, View
from amc_wx_lite.shortcuts import (
    SPOTIFY_SUPPORTED_ACTIONS,
    Action,
    Chord,
    describe,
    describe_action,
    keyboard_help_announcement,
    resolve,
)


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
    client.prepare_chapters(session_id="podcasts")
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
        ("chapter.prepare", {"sessionId": "podcasts"}, 40.0),
        ("chapter.list", {"sessionId": "podcasts"}, 15.0),
        ("chapter.navigate", {"sessionId": "files", "direction": -1}, 15.0),
    ]


def test_podcast_chapter_actions_prepare_sources_before_using_the_index() -> None:
    source = (
        Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    methods = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    def call_lines(method: str, attribute: str) -> list[int]:
        return sorted(
            node.lineno
            for node in ast.walk(methods[method])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == attribute
        )

    navigate_prepare = call_lines("_navigate_chapter", "prepare_chapters")
    navigate_use = call_lines("_navigate_chapter", "navigate_chapter")
    list_prepare = call_lines("_show_chapters", "prepare_chapters")
    list_use = call_lines("_show_chapters", "list_chapters")
    assert navigate_prepare and navigate_use and navigate_prepare[0] < navigate_use[0]
    assert list_prepare and list_use and list_prepare[0] < list_use[0]
    assert source.count('self.announcer.say("Sprawdzanie rozdziałów")') >= 2
    assert source.count("Sprawdzanie rozdziałów użytkownika") >= 2
    assert source.count('"spotify:episode:"') >= 3


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


def test_spotify_exposes_bookmarks_and_chapters_through_every_command_surface() -> None:
    actions = {
        Action.ADD_BOOKMARK,
        Action.ADD_NAMED_BOOKMARK,
        Action.PREVIOUS_BOOKMARK,
        Action.NEXT_BOOKMARK,
        Action.PREVIOUS_NAMED_BOOKMARK,
        Action.NEXT_NAMED_BOOKMARK,
        Action.VIEW_CHAPTERS,
        Action.ADD_NAMED_CHAPTER,
        Action.PREVIOUS_CHAPTER,
        Action.NEXT_CHAPTER,
    }
    assert actions <= SPOTIFY_SUPPORTED_ACTIONS
    spotify_menu_actions = {
        item.action
        for menu in menus_for_session(SessionId.SPOTIFY)
        for item in menu.items
        if item.action is not None
    }
    assert actions <= spotify_menu_actions


def test_spotify_chapter_scope_is_honest_and_shared_by_command_surfaces() -> None:
    action = Action.VIEW_CHAPTERS
    expected = (
        "Pokaż rozdziały użytkownika oraz, w odcinku, "
        "znaczniki czasu z opisu"
    )
    assert describe_action(action, "Spotify") == expected

    menu_item = next(
        item
        for menu in menus_for_session(SessionId.SPOTIFY)
        for item in menu.items
        if item.action is action
    )
    assert expected in menu_item.label.replace("&", "")

    palette_entry = next(
        entry
        for entry in entries_for_session(SessionId.SPOTIFY)
        if entry.action is action
    )
    assert expected in palette_entry.name

    full_help = dict(describe("Spotify", {action}))
    assert list(full_help.values()) == [expected]
    assert expected in keyboard_help_announcement(
        Chord("B", ctrl=True, alt=True),
        action,
        "Spotify",
    )


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
