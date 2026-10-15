"""Regresje Shift+F2 i Shift+Delete na wierszach Historii nagrywania."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from test_gui_logic import install_wx_stub

install_wx_stub()

from amc_wx_lite import gui  # noqa: E402
from amc_wx_lite.list_model import Row  # noqa: E402
from amc_wx_lite.navigation import SessionId  # noqa: E402


class ImmediateRunner:
    def submit(self, _slot, work, done, failed):  # noqa: ANN001
        try:
            done(work())
        except Exception as error:  # pragma: no cover - ścieżka diagnostyczna
            failed(error)


def test_shift_f2_passes_history_path_to_host(tmp_path: Path) -> None:
    old_file = tmp_path / "audycja.mp3"
    new_file = tmp_path / "audycja poprawiona.mp3"
    old_file.write_bytes(b"test")
    old_path = str(old_file)
    new_path = str(new_file)
    row = Row(
        "radio-recording-history:history-1",
        "Radio Test, audycja.mp3",
        "track",
        path=old_path,
    )
    calls: list[tuple[str, str, str | None]] = []
    spoken: list[str] = []
    refreshed: list[str | None] = []
    saved: list[object] = []
    activated: list[bool] = []
    guard_seen_before_dialog_teardown: list[bool] = []

    class Dialog:
        value = "audycja poprawiona"

        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            # Windows może synchronicznie oddać Enter liście właśnie podczas
            # niszczenia dialogu. Bramka musi już wtedy być ustawiona.
            guard_seen_before_dialog_teardown.append(
                frame._local_file_rename_pending
            )
            gui.LiteFrame._activate_selected_if_ready(frame)
            return False

        def ShowModal(self):  # noqa: N802 - wx API
            return gui.wx.ID_OK

    def rename_local_file(item_id, name, path=None):  # noqa: ANN001
        calls.append((item_id, name, path))
        old_file.rename(new_file)
        return {"fileName": "audycja poprawiona.mp3", "path": new_path}

    client = SimpleNamespace(rename_local_file=rename_local_file)
    state = SimpleNamespace(recording_history=[{"id": "history-1", "path": old_path}])
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.FILES),
        _single_edit_row=lambda _what: row,
        _profile_edit_client=lambda: client,
        _activate=lambda: activated.append(True),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=spoken.append),
        state=state,
        store=SimpleNamespace(save=saved.append),
        _restore_focus_after_dialog=(
            lambda: gui.LiteFrame._activate_selected_if_ready(frame)
        ),
        _local_file_rename_pending=False,
        _local_file_rename_activation_guard_until=0.0,
        _refresh_profile_view=lambda preferred_id=None: refreshed.append(preferred_id),
    )
    original = gui.RenameItemDialog
    gui.RenameItemDialog = Dialog
    try:
        gui.LiteFrame._rename_local_file(frame)
    finally:
        gui.RenameItemDialog = original

    assert calls == [(
        "radio-recording-history:history-1",
        "audycja poprawiona",
        old_path,
    )]
    assert guard_seen_before_dialog_teardown == [True]
    assert activated == [], "Enter z dialogu nie może uruchomić wybranego pliku"
    assert not old_file.exists()
    assert new_file.exists()
    assert state.recording_history[0]["path"] == new_path
    assert saved == [state]
    assert refreshed == ["radio-recording-history:history-1"]
    assert spoken == ["Zmieniono nazwę pliku na dysku: audycja poprawiona.mp3"]


def test_shift_f2_failure_keeps_real_file_and_model_and_reports_error(
    tmp_path: Path,
) -> None:
    old_file = tmp_path / "zajete nagranie.mp3"
    target_file = tmp_path / "nowa nazwa.mp3"
    old_file.write_bytes(b"test")
    old_path = str(old_file)
    row = Row(
        "radio-recording-history:history-busy",
        "Radio Test, zajęte nagranie.mp3",
        "track",
        path=old_path,
    )
    spoken: list[str] = []
    refreshed: list[str | None] = []
    saved: list[object] = []

    class Dialog:
        value = "nowa nazwa"

        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def ShowModal(self):  # noqa: N802 - wx API
            return gui.wx.ID_OK

    class Client:
        @staticmethod
        def rename_local_file(_item_id, _name, path=None):  # noqa: ANN001
            assert path == old_path
            raise RuntimeError("plik jest zajęty przez inny program")

    state = SimpleNamespace(
        recording_history=[{"id": "history-busy", "path": old_path}]
    )
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.FILES),
        _single_edit_row=lambda _what: row,
        _profile_edit_client=lambda: Client(),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=spoken.append),
        state=state,
        store=SimpleNamespace(save=saved.append),
        _restore_focus_after_dialog=lambda: None,
        _local_file_rename_pending=False,
        _local_file_rename_activation_guard_until=0.0,
        _refresh_profile_view=lambda preferred_id=None: refreshed.append(preferred_id),
    )
    original = gui.RenameItemDialog
    gui.RenameItemDialog = Dialog
    try:
        gui.LiteFrame._rename_local_file(frame)
    finally:
        gui.RenameItemDialog = original

    assert old_file.exists()
    assert not target_file.exists()
    assert state.recording_history == [{"id": "history-busy", "path": old_path}]
    assert saved == []
    assert refreshed == ["radio-recording-history:history-busy"]
    assert frame._local_file_rename_pending is False
    assert spoken == [
        "Nie zmieniono nazwy pliku: plik jest zajęty przez inny program"
    ]


def test_recording_history_refresh_preserves_selected_item_id() -> None:
    calls: list[tuple[bool, str | None]] = []
    state = SimpleNamespace(library_view=gui.LibraryView.RECORDED_RADIO_FILES)
    frame = SimpleNamespace(
        navigator=SimpleNamespace(
            active=SessionId.FILES,
            session=state,
        ),
        _show_radio_recording_history=lambda *, announce=True, preferred_id=None: (
            calls.append((announce, preferred_id))
        ),
    )

    gui.LiteFrame._refresh_profile_view(
        frame,
        preferred_id="radio-recording-history:history-1",
    )

    assert calls == [(False, "radio-recording-history:history-1")]


def test_enter_confirming_shift_f2_cannot_activate_file_until_rename_finishes() -> None:
    activated: list[bool] = []
    frame = SimpleNamespace(
        _local_file_rename_pending=True,
        _local_file_rename_activation_guard_until=0.0,
        _activate=lambda: activated.append(True),
    )

    gui.LiteFrame._activate_selected_if_ready(frame)
    assert activated == []

    frame._local_file_rename_pending = False
    original_monotonic = gui.time.monotonic
    gui.time.monotonic = lambda: 10.0
    try:
        frame._local_file_rename_activation_guard_until = 11.0
        gui.LiteFrame._activate_selected_if_ready(frame)
        assert activated == []

        frame._local_file_rename_activation_guard_until = 9.0
        gui.LiteFrame._activate_selected_if_ready(frame)
        assert activated == [True]
    finally:
        gui.time.monotonic = original_monotonic


def test_shift_delete_passes_paths_and_removes_private_history_only_after_success() -> None:
    path = r"D:\Nagrania\audycja.mp3"
    row = Row(
        "radio-recording-history:history-1",
        "Radio Test, audycja.mp3",
        "track",
        path=path,
    )
    calls: list[tuple[list[str], list[str] | None]] = []
    forgotten: list[list[str]] = []
    spoken: list[str] = []
    refreshed: list[bool] = []

    class Client:
        def recycle_local_files(self, item_ids, *, paths=None):  # noqa: ANN001
            calls.append((item_ids, paths))
            return {
                "removed": [{"id": "", "title": "audycja", "path": path}],
                "failures": [],
            }

    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.FILES),
        _selected_action_rows=lambda: [row],
        _profile_edit_client=lambda: Client(),
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=spoken.append),
        _forget_private_recording_history_paths=lambda paths: forgotten.append(paths),
        _refresh_profile_view=lambda: refreshed.append(True),
    )
    original = gui.wx.MessageBox
    gui.wx.MessageBox = lambda *_args, **_kwargs: gui.wx.YES
    try:
        gui.LiteFrame._recycle_selected_files(frame)
    finally:
        gui.wx.MessageBox = original

    assert calls == [(["radio-recording-history:history-1"], [path])]
    assert forgotten == [[path]]
    assert refreshed == [True]
    assert spoken == [
        "Przeniesiono do Kosza i usunięto z AMC: Radio Test, audycja.mp3"
    ]
