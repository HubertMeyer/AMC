from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.menu_model import build_menus
from amc_wx_lite.navigation import (
    ActivateWiiMDevice,
    LibraryView,
    Navigator,
    PlayWiiMNetworkStream,
    SessionId,
    View,
)
from amc_wx_lite.shortcuts import (
    Action,
    Chord,
    WIIM_SUPPORTED_ACTIONS,
    resolve,
)
from amc_wx_lite.wiim_source import (
    device_rows,
    network_stream_edit_info,
    network_stream_rows,
    now_playing_label,
    preset_choices,
    snapshot,
)


def test_ctrl_5_and_menu_open_the_wiim_session() -> None:
    for player in (False, True):
        assert resolve(
            Chord("5", ctrl=True),
            player_view=player,
            radio_session=False,
        ) is Action.SESSION_WIIM
    view = next(menu for menu in build_menus() if menu.title == "&Widok")
    item = next(entry for entry in view.items if entry.action is Action.SESSION_WIIM)
    assert item.label == "Sesja: &WiiM"
    assert item.shortcut == "Ctrl+5"


def test_wiim_device_activation_separates_user_label_from_internal_id() -> None:
    nav = Navigator()
    rows = device_rows({
        "items": [{
            "itemId": "wiim:device-1",
            "deviceId": "device-1",
            "title": "Salon",
            "detail": "WiiM Pro",
            "selected": True,
            "address": "192.168.1.40",
        }]
    })
    nav.apply_wiim_devices(list(rows))
    nav.switch_session(SessionId.WIIM)

    intents = nav.activate_selected()

    assert len(intents) == 1
    intent = intents[0]
    assert isinstance(intent, ActivateWiiMDevice)
    assert intent.title == "Salon"
    assert intent.device_id == "device-1"
    assert "192.168.1.40" not in repr(nav.sessions[SessionId.WIIM].model.rows)
    assert nav.view is View.PLAYER


def test_wiim_payload_is_allowlisted_for_accessible_text() -> None:
    state = snapshot({
        "deviceId": "device-1",
        "deviceTitle": "Salon",
        "title": "Audycja",
        "artist": "Radio Poznań",
        "playbackState": "odtwarzanie",
        "volume": 35,
        "muted": False,
        "positionSeconds": 61,
        "durationSeconds": 600,
        "message": "Audycja, odtwarzanie, głośność 35%",
        "address": "192.168.1.40",
        "runtimeObject": "WiiMDeviceSettings { Address = 192.168.1.40 }",
    })

    assert now_playing_label(state) == "Audycja, Radio Poznań"
    assert "address" not in state
    assert "runtimeObject" not in state
    assert "192.168.1.40" not in repr(state)


def test_wiim_command_gate_blocks_local_audio_features() -> None:
    assert {
        Action.PLAY_PAUSE,
        Action.QUEUE_PREVIOUS,
        Action.QUEUE_NEXT,
        Action.VOLUME_UP_5,
        Action.VOLUME_DOWN_1,
        Action.TIME_ELAPSED,
        Action.VIEW_PRESETS,
        Action.ASSIGN_PRESET,
        Action.PRESET_1,
        Action.PRESET_12,
        Action.COPY_NAME,
        Action.FOCUS_FILTER,
        Action.VIEW_ACTIVE_RECORDINGS,
        Action.MANAGE_RADIO_SCHEDULES,
    } <= WIIM_SUPPORTED_ACTIONS
    assert {
        Action.ADD_BOOKMARK,
        Action.RATE_UP,
        Action.SEEK_FORWARD_10,
        Action.RECORD_TOGGLE,
        Action.ADD_TO_QUEUE,
        Action.SELECT_AUDIO_OUTPUT,
        Action.PREVIOUS_AUDIO_OUTPUT,
        Action.NEXT_AUDIO_OUTPUT,
    }.isdisjoint(WIIM_SUPPORTED_ACTIONS)


def test_wiim_host_client_sends_only_device_id_command_and_volume() -> None:
    calls: list[tuple[str, dict | None, float]] = []
    client = LiteHostClient(Path("host.exe"))
    client.call = lambda op, args=None, *, timeout=20.0: (
        calls.append((op, args, timeout)) or {}
    )

    client.wiim_devices()
    client.wiim_snapshot("device-1")
    client.wiim_transport("device-1", "setVolume", volume=37)
    client.wiim_presets("device-1")
    client.wiim_activate_preset("device-1", 5)
    client.wiim_network_streams()
    client.wiim_play_network_stream("device-1", "stream-7")
    client.wiim_network_stream_edit_info("stream-7")
    client.wiim_add_network_stream("Radio Poznań", "https://radio.example/live")
    client.wiim_edit_network_stream(
        "stream-7", "Radio Poznań 2", "https://radio.example/live2"
    )
    client.wiim_remove_network_streams(["stream-7", "stream-8"])
    client.wiim_import_network_streams("C:/listy/wiim.m3u")
    client.wiim_export_network_streams("C:/listy/eksport.m3u")
    client.wiim_sort_network_streams("Alphabetical")

    assert calls == [
        ("wiim.devices", None, 15.0),
        ("wiim.snapshot", {"deviceId": "device-1"}, 30.0),
        (
            "wiim.transport",
            {"deviceId": "device-1", "command": "setVolume", "volume": 37},
            30.0,
        ),
        ("wiim.presets", {"deviceId": "device-1"}, 30.0),
        (
            "wiim.presetActivate",
            {"deviceId": "device-1", "presetNumber": 5},
            30.0,
        ),
        ("wiim.networkStreams", None, 15.0),
        (
            "wiim.networkStreamPlay",
            {"deviceId": "device-1", "streamId": "stream-7"},
            30.0,
        ),
        (
            "wiim.networkStreamEditInfo",
            {"streamId": "stream-7"},
            15.0,
        ),
        (
            "wiim.networkStreamAdd",
            {"name": "Radio Poznań", "url": "https://radio.example/live"},
            30.0,
        ),
        (
            "wiim.networkStreamEdit",
            {
                "streamId": "stream-7",
                "name": "Radio Poznań 2",
                "url": "https://radio.example/live2",
            },
            30.0,
        ),
        (
            "wiim.networkStreamRemove",
            {"itemIds": ["stream-7", "stream-8"]},
            30.0,
        ),
        (
            "wiim.networkStreamImport",
            {"path": "C:/listy/wiim.m3u"},
            60.0,
        ),
        (
            "wiim.networkStreamExport",
            {"path": "C:/listy/eksport.m3u"},
            60.0,
        ),
        (
            "wiim.networkStreamSort",
            {"mode": "Alphabetical"},
            30.0,
        ),
    ]
    assert "address" not in repr(calls).casefold()


def test_wiim_dispatch_reaches_remote_volume_and_blocks_local_rate() -> None:
    spoken: list[str] = []
    volume_steps: list[int] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.WIIM),
        announcer=SimpleNamespace(say=spoken.append),
        messages=SimpleNamespace(custom_seek_seconds=300),
        _adjust_volume=volume_steps.append,
    )

    LiteFrame._dispatch(frame, Action.VOLUME_UP_5)
    assert volume_steps == [5]
    assert spoken == []

    LiteFrame._dispatch(frame, Action.RATE_UP)
    assert volume_steps == [5]
    assert spoken == ["To polecenie nie jest dostępne w sesji WiiM"]


def test_wiim_preset_list_has_only_twelve_intentional_labels() -> None:
    items = [
        {
            "itemId": f"wiim-preset:{number}",
            "presetNumber": number,
            "name": "Radio Test" if number == 2 else "",
            "source": "radio internetowe" if number == 2 else "",
            "label": (
                "Preset 2, Radio Test, radio internetowe"
                if number == 2
                else f"Preset {number}, pusty"
            ),
            "occupied": number == 2,
            "current": number == 2,
            "activationError": "",
            "uri": "https://secret.example/stream",
            "runtimeObject": "WiiMPresetInformation { Number = 2 }",
        }
        for number in range(1, 13)
    ]

    title, choices = preset_choices({
        "deviceId": "device-1",
        "deviceTitle": "Salon",
        "items": items,
    })

    assert title == "Salon"
    assert len(choices) == 12
    assert choices[1].label == "Preset 2, Radio Test, radio internetowe"
    assert choices[1].title == "Radio Test"
    assert choices[1].source == "radio internetowe"
    assert choices[1].occupied is True
    assert choices[1].current is True
    assert "secret" not in repr(choices)
    assert "WiiMPresetInformation" not in repr(choices)


def test_wiim_preset_connect_reason_stays_user_facing() -> None:
    items = [
        {
            "presetNumber": number,
            "label": "Preset 5, TIDAL, TIDAL Connect"
            if number == 5 else f"Preset {number}, pusty",
            "occupied": number == 5,
            "current": False,
            "activationError": (
                "Preset 5 to TIDAL Connect. Urządzenie samo tego nie uruchomi, "
                "bo odbiera dźwięk z aplikacji."
                if number == 5 else ""
            ),
        }
        for number in range(1, 13)
    ]

    _title, choices = preset_choices({"deviceTitle": "Salon", "items": items})

    assert choices[4].activation_error.startswith("Preset 5 to TIDAL Connect")


def test_ctrl_alt_p_routes_to_native_wiim_presets() -> None:
    calls: list[str] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.WIIM),
        _show_wiim_presets=lambda: calls.append("wiim"),
    )

    LiteFrame._show_presets(frame)

    assert calls == ["wiim"]


def test_wiim_assignment_and_digit_activation_use_device_specific_paths() -> None:
    calls: list[object] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.WIIM),
        _show_wiim_presets=lambda **kwargs: calls.append(("assign", kwargs)),
        _activate_wiim_shortcut_preset=lambda slot: calls.append(("play", slot)),
    )

    LiteFrame._assign_preset(frame)
    LiteFrame._activate_preset(frame, 12)

    assert calls == [
        ("assign", {"select_for_shortcut": True}),
        ("play", 12),
    ]


def test_ctrl_o_is_wiim_streams_only_in_wiim_context() -> None:
    chord = Chord("O", ctrl=True)
    assert resolve(
        chord,
        player_view=False,
        radio_session=False,
        wiim_session=True,
    ) is Action.VIEW_WIIM_NETWORK_STREAMS
    assert resolve(
        chord,
        player_view=True,
        radio_session=False,
        wiim_session=True,
    ) is Action.VIEW_WIIM_NETWORK_STREAMS
    assert resolve(
        chord,
        player_view=False,
        radio_session=False,
    ) is Action.OPEN_FILE_DIALOG


def test_wiim_stream_edit_shortcuts_are_active_only_inside_stream_list() -> None:
    for key, action in (
        ("N", Action.ADD_WIIM_NETWORK_STREAM),
        ("O", Action.VIEW_WIIM_NETWORK_STREAMS),
    ):
        assert resolve(
            Chord(key, ctrl=True),
            player_view=False,
            radio_session=False,
            wiim_session=True,
        ) is action

    assert resolve(
        Chord("F2"),
        player_view=False,
        radio_session=False,
        wiim_session=True,
    ) is None
    assert resolve(
        Chord("Delete"),
        player_view=False,
        radio_session=False,
        wiim_session=True,
    ) is None
    assert resolve(
        Chord("F2"),
        player_view=False,
        radio_session=False,
        wiim_session=True,
        wiim_streams=True,
    ) is Action.EDIT_WIIM_NETWORK_STREAM
    assert resolve(
        Chord("Delete"),
        player_view=False,
        radio_session=False,
        wiim_session=True,
        wiim_streams=True,
    ) is Action.REMOVE_WIIM_NETWORK_STREAMS

    assert resolve(
        Chord("O", ctrl=True, shift=True),
        player_view=False,
        radio_session=False,
        wiim_session=True,
    ) is Action.IMPORT_WIIM_NETWORK_STREAMS
    assert resolve(
        Chord("E", ctrl=True),
        player_view=False,
        radio_session=False,
        wiim_session=True,
    ) is Action.EXPORT_WIIM_NETWORK_STREAMS
    for key, action in (
        ("1", Action.SORT_WIIM_NETWORK_STREAMS_ADDED),
        ("2", Action.SORT_WIIM_NETWORK_STREAMS_ALPHABETICAL),
        ("3", Action.SORT_WIIM_NETWORK_STREAMS_CUSTOM),
    ):
        assert resolve(
            Chord(key, alt=True),
            player_view=False,
            radio_session=False,
            wiim_session=True,
        ) is None
        assert resolve(
            Chord(key, alt=True),
            player_view=False,
            radio_session=False,
            wiim_session=True,
            wiim_streams=True,
        ) is action


def test_wiim_stream_edit_info_is_explicit_and_user_facing() -> None:
    assert network_stream_edit_info({
        "streamId": "stream-7",
        "name": "Radio Poznań",
        "url": "https://radio.example/live",
        "runtimeObject": "NetworkStreamSettings { Id = stream-7 }",
    }) == (
        "stream-7",
        "Radio Poznań",
        "https://radio.example/live",
    )


def test_wiim_network_stream_view_uses_only_user_labels_and_returns_to_device() -> None:
    nav = Navigator()
    devices = list(device_rows({
        "items": [{
            "itemId": "wiim:device-1",
            "deviceId": "device-1",
            "title": "Salon",
            "detail": "WiiM Pro",
        }]
    }))
    nav.apply_wiim_devices(devices)
    nav.switch_session(SessionId.WIIM)
    streams = list(network_stream_rows({
        "items": [{
            "itemId": "wiim-stream:stream-7",
            "streamId": "stream-7",
            "title": "Radio Poznań",
            "detail": "Strumień sieciowy",
            "url": "https://secret.example/live.m3u8",
            "runtimeObject": "NetworkStream { Id = stream-7 }",
        }]
    }, device_id="device-1"))

    nav.apply_wiim_network_streams(
        streams,
        device_id="device-1",
        return_id="wiim:device-1",
    )
    assert nav.session.library_view is LibraryView.WIIM_NETWORK_STREAMS
    assert nav.session.model.selected_row.title == "Radio Poznań"
    assert "secret.example" not in repr(nav.session.model.rows)
    assert "Id = stream-7" not in repr(nav.session.model.rows)

    intents = nav.activate_selected()
    assert len(intents) == 1
    assert isinstance(intents[0], PlayWiiMNetworkStream)
    assert intents[0].device_id == "device-1"
    assert intents[0].stream_id == "stream-7"

    nav.session.view = View.LIST
    nav.go_to_parent()
    assert nav.session.library_view is None
    assert nav.session.model.selected_id == "wiim:device-1"
