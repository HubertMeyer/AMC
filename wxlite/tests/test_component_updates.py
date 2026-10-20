from __future__ import annotations

from pathlib import Path

from amc_wx_lite import gui
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.menu_model import menus_for_session
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.shortcuts import Action, describe


def test_component_update_command_has_menu_palette_help_and_dispatch_parity() -> None:
    action = Action.UPDATE_MEDIA_COMPONENTS
    for session in SessionId:
        menu_items = {
            item.action: item
            for menu in menus_for_session(session)
            for item in menu.items
            if item.action is not None
        }
        palette = {entry.action: entry for entry in entries_for_session(session)}
        assert action in menu_items
        assert action in palette
        assert "FFmpeg" in palette[action].name
        assert "yt-dlp" in palette[action].name
    assert (
        "Bez skrótu",
        "Sprawdź, pobierz i zweryfikuj składniki FFmpeg i yt-dlp",
    ) in describe()
    source = Path(gui.__file__).read_text(encoding="utf-8")
    assert "elif action is Action.UPDATE_MEDIA_COMPONENTS:" in source
    assert "self._update_media_components()" in source


def test_manual_component_update_announces_one_final_user_facing_result() -> None:
    announcements: list[str] = []
    submissions: list[tuple] = []

    class Client:
        alive = True

        @staticmethod
        def update_media_components(*, automatic: bool = False) -> dict:
            assert not automatic
            return {
                "success": True,
                "performed": True,
                "changed": True,
                "complete": True,
                "message": "Zainstalowano i zweryfikowano oba składniki.",
            }

    class Runner:
        @staticmethod
        def submit(stream, work, done, failed):
            submissions.append((stream, work, done, failed))
            done(work())

    frame = type("Frame", (), {})()
    frame.client = Client()
    frame.runner = Runner()
    frame.store = None
    frame._component_update_pending = False
    frame.announcer = type("Announcer", (), {"say": staticmethod(announcements.append)})()

    gui.LiteFrame._update_media_components(frame)

    assert [entry[0] for entry in submissions] == ["component-update"]
    assert announcements == [
        "Sprawdzanie składników FFmpeg i yt-dlp",
        "Składniki multimedialne są gotowe. "
        "Zainstalowano i zweryfikowano oba składniki.",
    ]
    assert not frame._component_update_pending


def test_automatic_recent_check_stays_quiet() -> None:
    announcements: list[str] = []

    class Client:
        alive = True

        @staticmethod
        def update_media_components(*, automatic: bool = False) -> dict:
            assert automatic
            return {
                "success": True,
                "performed": False,
                "changed": False,
                "complete": True,
                "message": "Składniki były sprawdzane niedawno.",
            }

    class Runner:
        @staticmethod
        def submit(_stream, work, done, _failed):
            done(work())

    frame = type("Frame", (), {})()
    frame.client = Client()
    frame.runner = Runner()
    frame.store = None
    frame._component_update_pending = False
    frame.announcer = type("Announcer", (), {"say": staticmethod(announcements.append)})()

    gui.LiteFrame._update_media_components(frame, automatic=True)

    assert announcements == []
    assert not frame._component_update_pending
