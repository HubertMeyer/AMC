"""Regresje Shift+F2 i Shift+Delete na wierszach Historii nagrywania."""

from __future__ import annotations

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


def test_shift_f2_passes_history_path_to_host() -> None:
    old_path = r"D:\Nagrania\audycja.mp3"
    new_path = r"D:\Nagrania\audycja poprawiona.mp3"
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

    class Dialog:
        value = "audycja poprawiona"

        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def ShowModal(self):  # noqa: N802 - wx API
            return gui.wx.ID_OK

    client = SimpleNamespace(
        rename_local_file=lambda item_id, name, path=None: (
            calls.append((item_id, name, path))
            or {"fileName": "audycja poprawiona.mp3", "path": new_path}
        )
    )
    state = SimpleNamespace(recording_history=[{"id": "history-1", "path": old_path}])
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.FILES),
        _single_edit_row=lambda _what: row,
        _profile_edit_client=lambda: client,
        runner=ImmediateRunner(),
        announcer=SimpleNamespace(say=spoken.append),
        state=state,
        store=SimpleNamespace(save=saved.append),
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
    assert state.recording_history[0]["path"] == new_path
    assert saved == [state]
    assert refreshed == ["radio-recording-history:history-1"]
    assert spoken == ["Zmieniono nazwę pliku na dysku: audycja poprawiona.mp3"]


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
