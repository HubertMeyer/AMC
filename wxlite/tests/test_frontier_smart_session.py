from __future__ import annotations

from pathlib import Path

from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.frontier_smart_source import (
    device_rows,
    mode_choices,
    now_playing_label,
    preset_choices,
    should_auto_discover_devices,
    snapshot,
)
from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.menu_model import menus_for_session
from amc_wx_lite.navigation import (
    ActivateFrontierSmartDevice,
    Navigator,
    SessionId,
    View,
)
from amc_wx_lite.release_profile import PUBLIC_PROFILE, TEST_PROFILE
from amc_wx_lite.shortcuts import (
    Action,
    Chord,
    FRONTIER_SMART_SUPPORTED_ACTIONS,
    describe,
    resolve,
)


def test_frontier_smart_exists_only_in_amc_test_profile() -> None:
    assert "frontierSmart" in TEST_PROFILE.session_ids
    assert "session.frontier-smart" in TEST_PROFILE.capabilities
    assert "frontierSmart" not in PUBLIC_PROFILE.session_ids
    assert "session.frontier-smart" not in PUBLIC_PROFILE.capabilities


def test_frontier_smart_device_activation_keeps_ids_out_of_spoken_rows() -> None:
    rows = device_rows({
        "items": [{
            "itemId": "frontier-smart:internal-device-id",
            "deviceId": "internal-device-id",
            "title": "Radio w salonie",
            "detail": "Firmware ir-mmi-FS2026-0500-088",
            "address": "192.168.1.55",
        }]
    })
    nav = Navigator()
    nav.apply_frontier_smart_devices(list(rows))
    nav.switch_session(SessionId.FRONTIER_SMART)

    intents = nav.activate_selected()

    assert len(intents) == 1
    assert isinstance(intents[0], ActivateFrontierSmartDevice)
    assert intents[0].title == "Radio w salonie"
    assert intents[0].device_id == "internal-device-id"
    assert nav.view is View.PLAYER
    spoken_cells = (rows[0].title, rows[0].kind_label, rows[0].detail)
    assert spoken_cells == (
        "Radio w salonie",
        "urządzenie",
        "Firmware ir-mmi-FS2026-0500-088",
    )
    assert "192.168.1.55" not in " ".join(spoken_cells)
    assert "internal-device-id" not in " ".join(spoken_cells)


def test_frontier_smart_payloads_are_allowlisted_for_accessible_text() -> None:
    state = snapshot({
        "deviceId": "internal-device-id",
        "deviceTitle": "Radio w salonie",
        "title": "Trójka",
        "subtitle": "Audycja wieczorna",
        "artist": "Polskie Radio",
        "playbackState": "odtwarzanie",
        "volume": 42,
        "muted": False,
        "positionSeconds": 15,
        "durationSeconds": 3600,
        "address": "192.168.1.55",
        "runtimeObject": "FrontierSmartDeviceSettings { Address = 192.168.1.55 }",
    })
    assert now_playing_label(state) == (
        "Trójka, Audycja wieczorna, Polskie Radio"
    )
    assert "address" not in state
    assert "runtimeObject" not in state
    assert "192.168.1.55" not in repr(state)

    title, presets = preset_choices({
        "deviceTitle": "Radio w salonie",
        "items": [{"presetKey": 0, "name": "Trójka", "label": "Trójka, preset 1"}],
    })
    assert title == "Radio w salonie"
    assert presets[0].label == "Trójka, preset 1"

    title, modes, selected = mode_choices({
        "deviceTitle": "Radio w salonie",
        "items": [
            {"key": 0, "label": "Radio internetowe", "selected": True, "enabled": True},
            {"key": 1, "label": "DAB, niedostępny do bezpośredniego wyboru", "selected": False, "enabled": False},
        ],
    })
    assert title == "Radio w salonie"
    assert selected == 0
    assert [choice.label for choice in modes] == [
        "Radio internetowe",
        "DAB, niedostępny do bezpośredniego wyboru",
    ]


def test_frontier_smart_host_client_uses_narrow_named_operations() -> None:
    calls: list[tuple[str, dict | None, float]] = []
    client = LiteHostClient(Path("host.exe"))
    client.call = lambda op, args=None, *, timeout=20.0: (
        calls.append((op, args, timeout)) or {}
    )

    client.frontier_smart_devices()
    client.frontier_smart_discover()
    client.frontier_smart_add("192.168.1.55", "1234")
    client.frontier_smart_select("device-1")
    client.frontier_smart_snapshot("device-1")
    client.frontier_smart_transport("device-1", "setVolume", volume=37)
    client.frontier_smart_modes("device-1")
    client.frontier_smart_set_mode("device-1", 2)
    client.frontier_smart_presets("device-1")
    client.frontier_smart_activate_preset("device-1", 4)
    client.frontier_smart_remove("device-1")

    assert calls == [
        ("frontierSmart.devices", None, 15.0),
        ("frontierSmart.discover", None, 15.0),
        ("frontierSmart.add", {"address": "192.168.1.55", "pin": "1234"}, 30.0),
        ("frontierSmart.select", {"deviceId": "device-1"}, 15.0),
        ("frontierSmart.snapshot", {"deviceId": "device-1"}, 30.0),
        (
            "frontierSmart.transport",
            {"deviceId": "device-1", "command": "setVolume", "volume": 37},
            30.0,
        ),
        ("frontierSmart.modes", {"deviceId": "device-1"}, 30.0),
        ("frontierSmart.modeSet", {"deviceId": "device-1", "modeKey": 2}, 30.0),
        ("frontierSmart.presets", {"deviceId": "device-1"}, 30.0),
        (
            "frontierSmart.presetActivate",
            {"deviceId": "device-1", "presetKey": 4},
            30.0,
        ),
        ("frontierSmart.remove", {"deviceId": "device-1"}, 15.0),
    ]


def test_frontier_smart_commands_have_menu_help_palette_and_execution_route() -> None:
    assert resolve(
        Chord("F5", ctrl=True),
        player_view=False,
        radio_session=False,
        frontier_smart_session=True,
    ) is Action.SESSION_CONFIGURE_CURRENT

    actions = {
        item.action
        for menu in menus_for_session(SessionId.FRONTIER_SMART)
        for item in menu.items
        if item.action is not None
    }
    assert {
        Action.SESSION_CONFIGURE_CURRENT,
        Action.FRONTIER_SMART_SELECT_MODE,
        Action.VIEW_PRESETS,
        Action.PLAY_PAUSE,
        Action.TOGGLE_MUTE,
    } <= actions
    assert Action.RECORD_TOGGLE not in actions
    assert Action.SELECT_AUDIO_OUTPUT not in actions

    help_entries = describe(
        "Frontier Smart",
        available_actions=set(FRONTIER_SMART_SUPPORTED_ACTIONS),
    )
    assert dict(help_entries)["Ctrl+F5"] == (
        "Pokaż zapisane urządzenia Frontier Smart i opcjonalnie wyszukaj nowe"
    )
    assert any(
        "tryb urządzenia Frontier Smart" in label
        for _shortcut, label in help_entries
    )

    palette_actions = {
        entry.action
        for entry in entries_for_session(
            SessionId.FRONTIER_SMART,
            [session.value for session in SessionId],
        )
    }
    assert Action.SESSION_CONFIGURE_CURRENT in palette_actions
    assert Action.FRONTIER_SMART_SELECT_MODE in palette_actions


def test_frontier_smart_device_dialog_has_explicit_names_and_keyboard_contract() -> None:
    source = (
        Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"
    ).read_text(encoding="utf-8")
    dialog = source[source.index("class FrontierSmartDevicesDialog") :]
    dialog = dialog[:dialog.index("class SessionSelectionDialog")]

    assert 'self.devices.SetName("Zapisane urządzenia Frontier Smart")' in dialog
    assert 'self.address.SetName("Lokalny adres IP urządzenia")' in dialog
    assert 'self.pin.SetName("PIN urządzenia, pole chronione")' in dialog
    assert 'self.manual_button.SetName("Wpisz lokalny adres IP ręcznie")' in dialog
    assert (
        'self.discover_button.SetName("Szukaj nowych urządzeń w sieci lokalnej")'
        in dialog
    )
    assert "self.Bind(wx.EVT_CHAR_HOOK, self._on_key)" in dialog
    assert "self.devices.Bind(wx.EVT_LISTBOX_DCLICK, self._on_select)" in dialog
    assert "self.devices.HasFocus()" in dialog
    assert "event.HasAnyModifiers()" in dialog
    assert "self.save_button.SetDefault()" not in dialog
    assert "wx.CallAfter(self._start_discovery)" in dialog
    assert "self.address_label.Hide()" in dialog
    assert "self.address.Hide()" in dialog
    assert "self.manual_button.SetFocus()" in dialog
    assert "self.pin.SetFocus()" in dialog
    assert "close_after=True" not in dialog


def test_frontier_smart_auto_discovers_only_without_saved_devices() -> None:
    assert should_auto_discover_devices({"items": []}) is True
    assert should_auto_discover_devices({
        "items": [
            {
                "itemId": "frontier:radio-1",
                "deviceId": "radio-1",
                "title": "Radio w salonie",
                "detail": "Frontier Smart",
            }
        ]
    }) is False

    source = (
        Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"
    ).read_text(encoding="utf-8")
    flow = source[source.index("    def _show_frontier_smart_devices") :]
    flow = flow[:flow.index("    def _activate_frontier_smart_device")]
    assert (
        "auto_discover=frontier_smart_should_auto_discover("
        in flow
    )
    assert 'label="&Szukaj nowych urządzeń"' in source


def test_frontier_smart_success_closes_configuration_and_returns_to_device_list() -> None:
    source = (
        Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"
    ).read_text(encoding="utf-8")
    flow = source[source.index("    def _show_frontier_smart_devices") :]
    flow = flow[:flow.index("    def _activate_frontier_smart_device")]

    assert "announce=self.announcer.say" in flow
    assert "lambda payload: finish(payload, dialog, close_after=True)" in flow
    assert "close_after=True" in flow
    assert "dialog.fail(str(error), focus_pin=focus_pin)" in flow
