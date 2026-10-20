from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from test_gui_logic import install_wx_stub

install_wx_stub()

import amc_wx_lite.gui as gui_module
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.navigation import SessionId


SOURCE = Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"


def test_account_status_uses_only_explicit_user_facing_labels() -> None:
    spotify = LiteFrame._service_account_status_message(
        SessionId.SPOTIFY,
        {
            "catalog": {"label": "Katalog Spotify jest połączony: Michał."},
            "playback": {"label": "Konto odtwarzania Spotify jest zapisane."},
            "technicalObject": {"id": "secret"},
        },
    )
    tidal = LiteFrame._service_account_status_message(
        SessionId.TIDAL,
        {"label": "Konto TIDAL jest połączone.", "token": "nie czytaj"},
    )

    assert spotify == (
        "Katalog Spotify jest połączony: Michał. "
        "Konto odtwarzania Spotify jest zapisane."
    )
    assert tidal == "Konto TIDAL jest połączone."
    assert "secret" not in spotify
    assert "token" not in tidal.casefold()


def test_dialog_explains_browser_login_without_code_and_has_explicit_names() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    dialog = source[source.index("class ServiceAccountDialog") :]
    dialog = dialog[:dialog.index("class SessionSelectionDialog")]
    assert 'label="Zaloguj w przeglądarce"' in dialog
    assert "AMC nie wymaga " in dialog
    assert '"przepisywania kodu."' in dialog
    assert 'SetName(f"Stan konta {service_name}: {status}")' in dialog
    assert 'SetName(f"Zaloguj konto {service_name} w przeglądarce")' in dialog
    assert "self.login_button.SetFocus" in dialog
    assert "self.close_button.Enable(not self._busy)" in dialog


def test_configure_routes_spotify_tidal_and_wiim_without_opening_browser_itself() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    section = source[source.index("    def _configure_session") :]
    section = section[:section.index("    def _show_session_list")]
    assert "self._show_service_account(session_id)" in section
    assert "client.spotify_login()" in section
    assert "client.tidal_login()" in section
    assert "self._load_wiim_devices" in section
    assert "LaunchDefaultBrowser" not in section
    assert "webbrowser" not in section.casefold()


def test_opening_spotify_account_announces_current_status_without_login() -> None:
    spoken: list[str] = []
    shown: list[tuple[str, str]] = []

    class FakeDialog:
        def __init__(self, _parent, service_name, status, _start_login) -> None:
            self.service_name = service_name
            self.status = status

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def ShowModal(self) -> int:  # noqa: N802 - API wx
            shown.append((self.service_name, self.status))
            return 0

    original_dialog = gui_module.ServiceAccountDialog
    gui_module.ServiceAccountDialog = FakeDialog
    try:
        frame = SimpleNamespace(
            client=SimpleNamespace(
                spotify_account_status=lambda: {
                    "catalog": {
                        "connected": True,
                        "label": "Katalog Spotify jest połączony: Michał.",
                    },
                    "playback": {
                        "connected": True,
                        "label": "Konto odtwarzania Spotify jest zapisane i gotowe.",
                    },
                }
            ),
            runner=SimpleNamespace(submit=lambda *_args: None),
            announcer=SimpleNamespace(say=spoken.append),
            _service_account_status_message=(
                LiteFrame._service_account_status_message
            ),
            _restore_focus_after_dialog=lambda: None,
        )

        LiteFrame._show_service_account(frame, SessionId.SPOTIFY)
    finally:
        gui_module.ServiceAccountDialog = original_dialog

    expected = (
        "Katalog Spotify jest połączony: Michał. "
        "Konto odtwarzania Spotify jest zapisane i gotowe."
    )
    assert shown == [("Spotify", expected)]
    assert spoken == [expected]
