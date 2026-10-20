from __future__ import annotations

from pathlib import Path

from test_gui_logic import install_wx_stub

install_wx_stub()

from amc_wx_lite.gui import LiteFrame


SOURCE = Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"


def test_sonos_account_message_uses_only_explicit_labels() -> None:
    payload = {
        "message": "Konto Sonos zostało połączone.",
        "label": "Stan zapasowy",
        "token": "sekret",
        "technicalObject": {"state": "Connected"},
    }
    assert LiteFrame._sonos_account_message(payload) == (
        "Konto Sonos zostało połączone."
    )
    assert LiteFrame._sonos_account_message({"label": "Brak konta."}) == (
        "Brak konta."
    )


def test_sonos_dialog_has_explicit_labels_and_never_opens_browser_on_start() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    dialog = source[source.index("class SonosAccountDialog") :]
    dialog = dialog[:dialog.index("class LibraryFoldersDialog")]
    assert 'SetName("Konto Sonos")' in dialog
    assert 'SetName("Adres logowania Sonos")' in dialog
    assert 'label="Rozpocznij logowanie"' in dialog
    assert 'label="Sprawdź logowanie"' in dialog
    assert 'label="Odśwież dostęp"' in dialog
    assert 'label="Głośniki i grupy Sonos"' in dialog
    assert "wx.LaunchDefaultBrowser" in dialog
    start_handler = dialog[dialog.index("    def _on_action") :]
    start_handler = start_handler[:start_handler.index("    def _on_open")]
    assert "LaunchDefaultBrowser" not in start_handler
    assert "str(payload)" not in dialog


def test_configure_sonos_opens_account_surface_not_a_spoken_dead_end() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    section = source[source.index("    def _configure_session") :]
    section = section[:section.index("    def _show_library_folders")]
    assert "if session_id is SessionId.SONOS:" in section
    assert "self._show_sonos_account()" in section
    assert 'SessionId.SONOS: "Wybierz dom i grupę Sonos"' not in section
