"""AMC14: lokalne foldery, pomoc i paleta korzystają z jednego polecenia."""

from __future__ import annotations

from pathlib import Path
from io import StringIO
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
from amc_wx_lite.shell_requests import (
    INVALID_REQUEST_MESSAGE,
    ShellRequest,
    ShellRequestError,
    decode_request,
    start_request_reader,
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


def test_shell_request_decoder_preserves_special_paths_and_rejects_bad_shape() -> None:
    request = decode_request(
        '{"Schema":1,"Operation":"queue","Files":'
        '["C:\\\\Muzyka\\\\Żółć, średnik; (1).mp3"]}'
    )
    assert request.add_to_queue
    assert request.files == (r"C:\Muzyka\Żółć, średnik; (1).mp3",)
    try:
        decode_request('{"Schema":1,"Operation":"open","Files":[] }')
    except ShellRequestError as error:
        assert str(error) == INVALID_REQUEST_MESSAGE
    else:
        raise AssertionError("Puste polecenie powłoki zostało przyjęte")


def test_shell_reader_schedules_requests_and_user_facing_errors() -> None:
    received: list[ShellRequest] = []
    errors: list[str] = []
    source = StringIO(
        '{"Schema":1,"Operation":"open","Files":["C:\\\\Muzyka\\\\a.mp3"]}\n'
        'nie-json\n'
    )
    thread = start_request_reader(
        received.append,
        errors.append,
        schedule=lambda function, value: function(value),
        stream=source,
    )
    thread.join(2)

    assert [request.files for request in received] == [(r"C:\Muzyka\a.mp3",)]
    assert errors == [INVALID_REQUEST_MESSAGE]


def test_shell_queue_add_does_not_switch_session_and_is_idempotent() -> None:
    calls: list[list[dict[str, str]]] = []
    spoken: list[str] = []
    refreshed: list[bool] = []
    frame = SimpleNamespace(
        client=SimpleNamespace(
            queue_add_membership=lambda items: (
                calls.append(items) or {"added": True, "changed": 0}
            )
        ),
        announcer=SimpleNamespace(say=spoken.append),
        runner=SimpleNamespace(
            submit=lambda _slot, work, done, _failed: done(work())
        ),
        navigator=SimpleNamespace(active=SessionId.PODCASTS),
        _note_queue_persistence=lambda _payload: None,
        _refresh_live_queue=lambda: refreshed.append(True),
    )

    gui.LiteFrame._add_shell_files_to_queue(
        frame,
        (r"C:\Muzyka\plik.mp3",),
    )

    assert frame.navigator.active is SessionId.PODCASTS
    assert calls[0][0] == {
        "id": r"file:C:\Muzyka\plik.mp3",
        "title": "plik.mp3",
        "path": r"C:\Muzyka\plik.mp3",
    }
    assert spoken == ["Plik jest już w kolejce"]
    assert refreshed == [True]
