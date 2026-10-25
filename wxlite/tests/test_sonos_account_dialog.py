from __future__ import annotations

from pathlib import Path

from test_gui_logic import install_wx_stub

install_wx_stub()

from amc_wx_lite.gui import LiteFrame, SonosAccountDialog


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
    assert 'SetName("Instrukcja logowania Sonos")' in dialog
    assert 'SetName("Stan konta Sonos")' in dialog
    assert "self.instructions = wx.TextCtrl" in dialog
    assert "self.status = wx.TextCtrl" in dialog
    assert "wx.TE_READONLY" in dialog
    assert "wx.TE_MULTILINE" in dialog
    assert 'SetName("Adres logowania Sonos")' in dialog
    assert 'label="Rozpocznij logowanie"' in dialog
    assert 'label="Sprawdź logowanie"' in dialog
    assert 'label="Odśwież dostęp"' in dialog
    assert 'label="Głośniki i grupy Sonos"' in dialog


def test_sonos_dialog_hides_login_when_public_service_is_unavailable() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    dialog = source[source.index("class SonosAccountDialog") :]
    dialog = dialog[:dialog.index("class LibraryFoldersDialog")]
    assert 'payload.get("canLogin") is not False' in dialog
    assert (
        "self.login_button.Show(can_login and not awaiting and not connected)"
        in dialog
    )
    assert "self.disconnect_button.Show(connected and can_disconnect)" in dialog
    assert 'return "status"' in dialog
    assert "wx.LaunchDefaultBrowser" in dialog
    start_handler = dialog[dialog.index("    def _on_action") :]
    start_handler = start_handler[:start_handler.index("    def _on_open")]
    assert "LaunchDefaultBrowser" not in start_handler
    assert "str(payload)" not in dialog


def test_sonos_dialog_focuses_a_meaningful_control_for_every_account_state() -> None:
    focus = SonosAccountDialog._initial_focus_key

    assert focus(
        awaiting=True, connected=False, can_login=True, has_address=True
    ) == "open"
    assert focus(
        awaiting=True, connected=False, can_login=True, has_address=False
    ) == "check"
    assert focus(
        awaiting=False, connected=True, can_login=True, has_address=False
    ) == "targets"
    assert focus(
        awaiting=False, connected=False, can_login=True, has_address=False
    ) == "login"
    assert focus(
        awaiting=False, connected=False, can_login=False, has_address=False
    ) == "status"


def test_configure_sonos_opens_account_surface_not_a_spoken_dead_end() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    section = source[source.index("    def _configure_session") :]
    section = section[:section.index("    def _show_library_folders")]
    assert "if session_id is SessionId.SONOS:" in section
    assert "self._show_sonos_account()" in section
    assert 'SessionId.SONOS: "Wybierz dom i grupę Sonos"' not in section
    assert "elif isinstance(intent, OpenSonosAccount):" in source
