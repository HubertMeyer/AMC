from __future__ import annotations

from pathlib import Path

from amc_wx_lite import gui
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.menu_model import menus_for_session
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.shortcuts import Action, describe
from amc_wx_lite.state_store import Options
from amc_wx_lite.host_client import LiteHostClient


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


def test_automatic_update_passes_private_policy_overrides_to_host() -> None:
    calls: list[dict[str, object]] = []

    class Client:
        alive = True

        @staticmethod
        def update_media_components(**kwargs) -> dict:
            calls.append(kwargs)
            return {
                "success": True,
                "performed": False,
                "changed": False,
                "complete": True,
            }

    class Runner:
        @staticmethod
        def submit(_stream, work, done, _failed):
            done(work())

    frame = type("Frame", (), {})()
    frame.client = Client()
    frame.runner = Runner()
    frame.store = None
    frame.options = Options(
        component_check_automatically=False,
        component_download_automatically=True,
    )
    frame._component_update_pending = False
    frame.announcer = type("Announcer", (), {"say": staticmethod(lambda _value: None)})()

    gui.LiteFrame._update_media_components(frame, automatic=True)

    assert calls == [{
        "automatic": True,
        "check_automatically": False,
        "download_automatically": True,
    }]


def test_settings_completion_callback_receives_the_same_result() -> None:
    completed: list[dict[str, object]] = []

    class Client:
        alive = True

        @staticmethod
        def update_media_components(*, automatic: bool = False) -> dict:
            return {
                "success": True,
                "performed": True,
                "changed": False,
                "complete": True,
                "ffmpeg": "FFmpeg jest gotowy",
                "ytDlp": "yt-dlp jest gotowy",
                "message": "Składniki są aktualne.",
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
    frame.announcer = type("Announcer", (), {"say": staticmethod(lambda _value: None)})()

    started = gui.LiteFrame._update_media_components(
        frame, on_complete=completed.append
    )

    assert started is True
    assert completed == [{
        "success": True,
        "performed": True,
        "changed": False,
        "complete": True,
        "ffmpeg": "FFmpeg jest gotowy",
        "ytDlp": "yt-dlp jest gotowy",
        "message": "Składniki są aktualne.",
    }]


def test_host_client_uses_narrow_status_and_update_contract() -> None:
    calls: list[tuple[str, dict | None, float]] = []
    client = LiteHostClient(Path("host.exe"))
    client.call = lambda op, args=None, *, timeout=20.0: (
        calls.append((op, args, timeout)) or {"success": True}
    )

    client.component_update_status()
    client.update_media_components(
        automatic=True,
        check_automatically=False,
        download_automatically=True,
    )

    assert calls == [
        ("components.status", None, 20.0),
        (
            "components.updateAutomatic",
            {
                "checkAutomatically": False,
                "downloadAutomatically": True,
            },
            1_200.0,
        ),
    ]


def test_component_update_failure_does_not_speak_technical_exception(
    tmp_path: Path,
) -> None:
    announcements: list[str] = []

    class Client:
        alive = True

        @staticmethod
        def update_media_components(*, automatic: bool = False) -> dict:
            raise RuntimeError(r"C:\sekretna-sciezka\ffmpeg.exe: błąd 500")

    class Runner:
        @staticmethod
        def submit(_stream, work, _done, failed):
            try:
                work()
            except Exception as error:
                failed(error)

    frame = type("Frame", (), {})()
    frame.client = Client()
    frame.runner = Runner()
    frame.store = type("Store", (), {"directory": tmp_path})()
    frame._component_update_pending = False
    frame.announcer = type("Announcer", (), {"say": staticmethod(announcements.append)})()

    gui.LiteFrame._update_media_components(frame)

    assert announcements[-1] == (
        "Nie udało się bezpiecznie zaktualizować składników. "
        "Szczegóły zapisano w dzienniku AMC"
    )
    assert "sekretna-sciezka" not in announcements[-1]
