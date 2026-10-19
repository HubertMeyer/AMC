"""AMC14: lokalne foldery, pomoc i paleta korzystają z jednego polecenia."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from amc_wx_lite import gui
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.list_model import ListModel, Row
from amc_wx_lite.navigation import SessionId, SessionState
from amc_wx_lite.shell_paths import (
    MISSING_LOCAL_FILE_MESSAGE,
    NO_LOCAL_FILE_MESSAGE,
    ShellPathError,
    explorer_target,
    looks_like_local_path,
    open_in_explorer,
)
from amc_wx_lite.shortcuts import Action, describe


def test_local_path_recognition_never_accepts_internet_address() -> None:
    assert looks_like_local_path(r"C:\Nagrania\audycja.mp3")
    assert looks_like_local_path(r"\\serwer\muzyka\audycja.mp3")
    assert not looks_like_local_path("https://example.test/audycja.mp3")
    assert not looks_like_local_path("spotify:track:123")
    assert not looks_like_local_path("")


def test_explorer_target_selects_file_and_opens_directory(tmp_path: Path) -> None:
    folder = tmp_path / "Żółć i przecinek, średnik;"
    folder.mkdir()
    media = folder / "nagranie (1).mp3"
    media.write_bytes(b"test")

    file_target = explorer_target(str(media))
    assert file_target.select_file
    assert file_target.arguments == ("explorer.exe", "/select,", str(media))

    folder_target = explorer_target(str(folder))
    assert not folder_target.select_file
    assert folder_target.arguments == ("explorer.exe", str(folder))


def test_open_in_explorer_passes_an_argument_list_without_shell(tmp_path: Path) -> None:
    media = tmp_path / "plik ze spacją.mp3"
    media.write_bytes(b"test")
    calls: list[tuple[list[str], dict[str, object]]] = []

    open_in_explorer(
        str(media),
        start=lambda arguments, **options: calls.append((arguments, options)),
    )

    assert calls == [
        (["explorer.exe", "/select,", str(media)], {"shell": False, "close_fds": True})
    ]


def test_explorer_target_reports_short_user_facing_errors(tmp_path: Path) -> None:
    try:
        explorer_target("https://example.test/file.mp3")
    except ShellPathError as error:
        assert str(error) == NO_LOCAL_FILE_MESSAGE
    else:
        raise AssertionError("Adres internetowy został uznany za lokalny plik")
    try:
        explorer_target(str(tmp_path / "brak.mp3"))
    except ShellPathError as error:
        assert str(error) == MISSING_LOCAL_FILE_MESSAGE
    else:
        raise AssertionError("Nieistniejący plik został przekazany do Eksploratora")


def test_containing_folder_is_one_action_in_menu_help_and_palette() -> None:
    action = Action.OPEN_CONTAINING_FOLDER
    files = {entry.action: entry for entry in entries_for_session(SessionId.FILES)}
    podcasts = {
        entry.action: entry for entry in entries_for_session(SessionId.PODCASTS)
    }
    radio = {entry.action for entry in entries_for_session(SessionId.RADIO)}

    assert files[action].name == "Otwórz folder zawierający"
    assert files[action].shortcut is None
    assert podcasts[action].name == files[action].name
    assert action not in radio
    assert ("Bez skrótu", "Otwórz folder zawierający") in describe()


def _frame_with_row(row: Row) -> SimpleNamespace:
    state = SessionState(SessionId.FILES, model=ListModel([row]))
    state.model.select_id(row.item_id)
    return SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.FILES,
            sessions={SessionId.FILES: state},
        ),
        announcer=SimpleNamespace(say=lambda _message: None),
    )


def test_gui_opens_path_of_selected_row() -> None:
    row = Row("file:1", "Nagranie", "track", path=r"C:\Nagrania\plik.mp3")
    frame = _frame_with_row(row)
    opened: list[str] = []
    original = gui.open_in_explorer
    try:
        gui.open_in_explorer = opened.append
        gui.LiteFrame._open_containing_folder(frame)
    finally:
        gui.open_in_explorer = original

    assert opened == [row.path]


def test_gui_refuses_internet_item_without_exposing_its_address() -> None:
    row = Row("episode:1", "Odcinek", "episode", url="https://example.test/1")
    frame = _frame_with_row(row)
    spoken: list[str] = []
    frame.announcer.say = spoken.append

    gui.LiteFrame._open_containing_folder(frame)

    assert spoken == [NO_LOCAL_FILE_MESSAGE]
