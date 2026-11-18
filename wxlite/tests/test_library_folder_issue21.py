"""Regresje #21: mowa operacji i jednoznaczne korzenie Biblioteki."""

from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from typing import cast

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gui_logic import install_wx_stub

install_wx_stub()

from amc_wx_lite import gui
from amc_wx_lite.gui import Announcer, LibraryFoldersDialog
from amc_wx_lite.library_db import LibraryDatabase, FolderSource, disambiguate_folder_source_names, folder_rows


def _source(identifier: str, path: str, display_name: str) -> FolderSource:
    return FolderSource(
        id=identifier,
        ordinal=0,
        path=path,
        display_name=display_name,
        resume_mode=0,
    )


def test_same_folder_display_names_get_case_insensitive_parent_labels() -> None:
    sources = [
        _source("one", r"X:\a\cd", "cd"),
        _source("two", r"X:\b\CD\\", "CD"),
        _source("three", r"X:\muzyka", "Muzyka"),
    ]

    assert disambiguate_folder_source_names(sources) == {
        "one": r"cd (X:\a)",
        "two": r"CD (X:\b)",
        "three": "Muzyka",
    }


def test_root_folder_rows_use_disambiguated_source_labels() -> None:
    sources = [
        FolderSource(id="one", ordinal=0, path=r"X:\a\cd", display_name="cd", resume_mode=0),
        FolderSource(id="two", ordinal=1, path=r"X:\b\CD\\", display_name="CD", resume_mode=0),
    ]
    database = SimpleNamespace(folder_sources=lambda: sources, active_items_under=lambda _root: [])

    assert [row.title for row in folder_rows(cast(LibraryDatabase, database), None)] == ["cd (X:\\a)", "CD (X:\\b)"]


class _Control:
    def __init__(self) -> None:
        self.focused = False

    def SetFocus(self) -> None:  # noqa: N802 - wx API
        self.focused = True


class _Status:
    def __init__(self) -> None:
        self.label = ""
        self.name = ""

    def SetLabel(self, value: str) -> None:  # noqa: N802 - wx API
        self.label = value

    def SetName(self, value: str) -> None:  # noqa: N802 - wx API
        self.name = value

    def GetLabel(self) -> str:  # noqa: N802 - wx API
        return self.label

    def GetHandle(self) -> int:  # noqa: N802 - wx API
        return 42


class _Owner:
    def __init__(self, active: bool = True) -> None:
        self.active = active

    def IsActive(self) -> bool:  # noqa: N802 - wx API
        return self.active


def test_library_folder_finish_and_fail_announce_once_through_active_dialog_owner(monkeypatch) -> None:
    notifications: list[tuple[int, int, int, int]] = []
    status = _Status()
    sources, add = _Control(), _Control()
    owner = _Owner()
    monkeypatch.setattr(gui.wx, "GetTopLevelParent", lambda _status: owner, raising=False)
    announcer = Announcer(status, notify=lambda *args: notifications.append(args))
    dialog = SimpleNamespace(
        _busy=True,
        _sources=[{"id": "source"}],
        sources=sources,
        add_button=add,
        status=status,
        announcer=announcer,
        Layout=lambda: None,
        _update_buttons=lambda: None,
    )
    dialog.set_status = lambda message, *, announce=False: LibraryFoldersDialog.set_status(
        cast(LibraryFoldersDialog, dialog), message, announce=announce
    )

    def apply_payload(payload, preferred_id, *, announce):
        dialog.set_status(payload["message"], announce=announce)

    dialog.apply_payload = apply_payload

    dialog_instance = cast(LibraryFoldersDialog, dialog)
    LibraryFoldersDialog.finish(dialog_instance, {"message": "Dodano Folder Biblioteki"})
    LibraryFoldersDialog.fail(dialog_instance, "Nie dodano folderu")

    assert len(notifications) == 2
    assert status.label == "Nie dodano folderu"
    assert status.name == "Nie dodano folderu"
    assert sources.focused

    owner.active = False
    LibraryFoldersDialog.fail(dialog_instance, "Cichy w nieaktywnym ownerze")
    assert len(notifications) == 2
