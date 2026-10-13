from __future__ import annotations

from pathlib import Path
from types import MethodType, SimpleNamespace

from amc_wx_lite import gui as gui_module
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.host_client import HostError, LiteHostClient
from amc_wx_lite.menu_model import build_menus
from amc_wx_lite.navigation import (
    ActivateSonosGroup,
    LibraryView,
    Navigator,
    OpenSonosView,
    PlaySonosMaterial,
    SessionId,
    View,
)
from amc_wx_lite.shortcuts import Action, Chord, SONOS_SUPPORTED_ACTIONS, resolve
from amc_wx_lite.sonos_source import (
    library_rows,
    material_rows,
    now_playing_label,
    own_stream_edit_info,
    snapshot,
    target_rows,
)


def test_ctrl_6_and_menu_open_the_sonos_session() -> None:
    for player in (False, True):
        assert resolve(
            Chord("6", ctrl=True),
            player_view=player,
            radio_session=False,
        ) is Action.SESSION_SONOS
    view = next(menu for menu in build_menus() if menu.title == "&Widok")
    item = next(entry for entry in view.items if entry.action is Action.SESSION_SONOS)
    assert item.label == "Sesja: &Sonos"
    assert item.shortcut == "Ctrl+6"


def test_sonos_content_and_target_shortcuts_work_in_list_and_player() -> None:
    expected = {
        "Ctrl+L": Action.VIEW_LIBRARY,
        "Ctrl+U": Action.VIEW_FAVORITES,
        "Ctrl+P": Action.VIEW_PLAYLISTS,
        "Ctrl+F5": Action.SELECT_SONOS_TARGET,
    }
    for player in (False, True):
        for chord, action in expected.items():
            parts = chord.split("+")
            assert resolve(
                Chord(
                    parts[-1],
                    ctrl="Ctrl" in parts,
                    shift="Shift" in parts,
                    alt="Alt" in parts,
                ),
                player_view=player,
                radio_session=False,
                sonos_session=True,
            ) is action


def test_sonos_own_stream_edit_shortcuts_are_strictly_contextual() -> None:
    expected = {
        "Ctrl+N": Action.ADD_SONOS_OWN_STREAM,
        "F2": Action.EDIT_SONOS_OWN_STREAM,
        "Delete": Action.REMOVE_SONOS_OWN_STREAMS,
        "Ctrl+O": Action.IMPORT_SONOS_OWN_STREAMS,
        "Alt+1": Action.SORT_SONOS_OWN_STREAMS_ADDED,
        "Alt+2": Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL,
        "Alt+3": Action.SORT_SONOS_OWN_STREAMS_CUSTOM,
    }
    for chord, action in expected.items():
        parts = chord.split("+")
        parsed = Chord(
            parts[-1],
            ctrl="Ctrl" in parts,
            shift="Shift" in parts,
            alt="Alt" in parts,
        )
        assert resolve(
            parsed,
            player_view=False,
            radio_session=False,
            sonos_session=True,
            sonos_own_streams=True,
        ) is action
        assert resolve(
            parsed,
            player_view=False,
            radio_session=False,
            sonos_session=True,
            sonos_own_streams=False,
        ) is None


def test_sonos_library_categories_materials_and_back_are_typed() -> None:
    nav = Navigator()
    nav.switch_session(SessionId.SONOS)
    categories = list(library_rows({
        "items": [
            {
                "itemId": "sonos.library.favorites",
                "title": "Ulubione Sonos",
                "detail": "Enter otwiera listę",
                "kind": "favorites",
            },
            {
                "itemId": "sonos.library.playlists",
                "title": "Playlisty Sonos",
                "detail": "Enter otwiera listę",
                "kind": "playlists",
            },
            {
                "itemId": "sonos.library.ownstreams",
                "title": "Moje stacje",
                "detail": "Enter otwiera listę",
                "kind": "ownStreams",
            },
        ]
    }, "house-1"))
    nav.apply_sonos_library(categories, household_id="house-1")
    opened = nav.activate_selected()
    assert opened == [OpenSonosView(
        LibraryView.SONOS_FAVORITES,
        household_id="house-1",
        preferred_id=None,
    )]

    nav.apply_sonos_library(categories, household_id="house-1")
    assert nav.session.model.select_id("sonos.library.ownstreams")
    assert nav.activate_selected() == [OpenSonosView(
        LibraryView.SONOS_OWN_STREAMS,
        household_id="house-1",
        preferred_id=None,
    )]

    favorites = list(material_rows({
        "items": [{
            "itemId": "sonos-favorite:item-1",
            "materialId": "favorite-1",
            "title": "Radio Poznań",
            "kind": "favorite",
        }]
    }, "house-1"))
    nav.apply_sonos_materials(
        LibraryView.SONOS_FAVORITES,
        favorites,
        household_id="house-1",
        return_id="sonos.library.favorites",
    )
    played = nav.activate_selected()
    assert played == [PlaySonosMaterial(
        item_id="sonos-favorite:item-1",
        title="Radio Poznań",
        household_id="house-1",
        kind="favorite",
        material_id="favorite-1",
    )]
    nav.back_to_list()
    assert nav.go_to_parent() == [OpenSonosView(
        LibraryView.SONOS_LIBRARY,
        household_id="house-1",
        preferred_id="sonos.library.favorites",
    )]


def test_sonos_own_stream_is_a_typed_material_without_spoken_url() -> None:
    nav = Navigator()
    nav.switch_session(SessionId.SONOS)
    rows = list(material_rows({
        "items": [{
            "itemId": "sonos-stream:technical-item",
            "materialId": "technical-material",
            "title": "Radio domowe",
            "detail": "Stacja zapisana w AMC",
            "kind": "ownStream",
            "streamUrl": "https://secret.example/live",
        }]
    }, "house-1"))
    nav.apply_sonos_materials(
        LibraryView.SONOS_OWN_STREAMS,
        rows,
        household_id="house-1",
        return_id="sonos.library.ownstreams",
    )

    assert rows[0].title == "Radio domowe"
    assert rows[0].detail == "Stacja zapisana w AMC"
    assert "secret.example" not in rows[0].title
    assert "secret.example" not in rows[0].detail
    assert nav.activate_selected() == [PlaySonosMaterial(
        item_id="sonos-stream:technical-item",
        title="Radio domowe",
        household_id="house-1",
        kind="ownStream",
        material_id="technical-material",
    )]


def test_sonos_own_stream_url_is_exposed_only_to_explicit_editor() -> None:
    assert own_stream_edit_info({
        "streamId": "stream-1",
        "name": "Radio domowe",
        "url": "https://radio.example/live",
        "runtimeObject": "SonosOwnStreamSettings { StreamUrl = secret }",
    }) == (
        "stream-1",
        "Radio domowe",
        "https://radio.example/live",
    )


def test_sonos_material_uses_active_group_and_stays_on_one_request_lane() -> None:
    submissions: list = []
    calls: list = []
    frame = SimpleNamespace(
        client=SimpleNamespace(
            sonos_load_material=lambda *args: calls.append(args) or {}
        ),
        announcer=SimpleNamespace(say=lambda _text: None),
        runner=SimpleNamespace(submit=lambda *args: submissions.append(args)),
        navigator=SimpleNamespace(active=SessionId.SONOS),
        _sonos_active_household_id="house-1",
        _sonos_active_group_id="group-1",
        _sonos_request_pending=False,
        _sonos_retry_pending=False,
        _sonos_pending_material=None,
    )
    intent = PlaySonosMaterial(
        "item-1", "Radio Poznań", "house-1", "favorite", "favorite-1"
    )

    LiteFrame._play_sonos_material(frame, intent)

    assert len(submissions) == 1
    stream, work, _done, _failed = submissions[0]
    assert stream == "sonos-material"
    assert frame._sonos_request_pending is True
    work()
    assert calls == [("house-1", "group-1", "favorite", "favorite-1")]


def test_sonos_activation_separates_labels_from_internal_ids() -> None:
    nav = Navigator()
    rows = target_rows({
        "items": [{
            "itemId": "sonos:group-1",
            "householdId": "house-technical",
            "groupId": "group-technical",
            "title": "Salon",
            "detail": "Dwa głośniki",
        }]
    })
    nav.apply_sonos_targets(list(rows))
    nav.switch_session(SessionId.SONOS)

    intents = nav.activate_selected()

    assert len(intents) == 1
    intent = intents[0]
    assert isinstance(intent, ActivateSonosGroup)
    assert intent.title == "Salon"
    assert intent.household_id == "house-technical"
    assert intent.group_id == "group-technical"
    row = nav.sessions[SessionId.SONOS].model.selected_row
    assert row is not None
    assert row.title == "Salon"
    assert row.detail == "Dwa głośniki"
    assert "technical" not in row.title
    assert "technical" not in row.detail
    assert nav.view is View.PLAYER


def test_sonos_snapshot_allowlists_accessible_text() -> None:
    state = snapshot({
        "itemId": "sonos:group-1",
        "householdId": "house-1",
        "groupId": "group-1",
        "groupTitle": "Salon",
        "title": "Audycja",
        "source": "Radio Poznań",
        "stateText": "odtwarzanie",
        "volumeText": "głośność 35%",
        "positionText": "1:01 z 10:00",
        "playbackState": "playing",
        "volume": 35,
        "muted": False,
        "fixedVolume": False,
        "positionSeconds": 61,
        "durationSeconds": 600,
        "message": "Audycja, odtwarzanie",
        "token": "secret",
        "runtimeObject": "SonosGroup { Id = group-1 }",
    })

    assert now_playing_label(state) == "Audycja, Radio Poznań"
    assert "token" not in state
    assert "runtimeObject" not in state
    assert "secret" not in repr(state)


def test_sonos_command_gate_blocks_local_only_features() -> None:
    assert {
        Action.PLAY_PAUSE,
        Action.QUEUE_PREVIOUS,
        Action.QUEUE_NEXT,
        Action.SEEK_FORWARD_10,
        Action.SEEK_PERCENT_50,
        Action.VOLUME_UP_5,
        Action.TIME_ELAPSED,
        Action.COPY_NAME,
        Action.ADD_SONOS_OWN_STREAM,
        Action.EDIT_SONOS_OWN_STREAM,
        Action.REMOVE_SONOS_OWN_STREAMS,
        Action.IMPORT_SONOS_OWN_STREAMS,
        Action.SORT_SONOS_OWN_STREAMS_ALPHABETICAL,
    } <= SONOS_SUPPORTED_ACTIONS
    assert {
        Action.ADD_BOOKMARK,
        Action.RATE_UP,
        Action.RECORD_TOGGLE,
        Action.ADD_TO_QUEUE,
        Action.SELECT_AUDIO_OUTPUT,
        Action.PREVIOUS_AUDIO_OUTPUT,
        Action.NEXT_AUDIO_OUTPUT,
    }.isdisjoint(SONOS_SUPPORTED_ACTIONS)


def test_sonos_host_client_uses_narrow_commands_and_arguments() -> None:
    calls: list[tuple[str, dict | None, float]] = []
    client = LiteHostClient(Path("host.exe"))
    client.call = lambda op, args=None, *, timeout=20.0: (
        calls.append((op, args, timeout)) or {}
    )

    client.sonos_targets()
    client.sonos_snapshot("house-1", "group-1")
    client.sonos_transport(
        "house-1", "group-1", "seekRelative", seconds=30
    )
    client.sonos_library()
    client.sonos_materials("house-1", "favorite")
    client.sonos_materials("house-1", "ownStream")
    client.sonos_load_material(
        "house-1", "group-1", "favorite", "favorite-1"
    )
    client.sonos_load_material(
        "house-1", "group-1", "ownStream", "stream-1"
    )
    client.sonos_own_stream_edit_info("stream-1")
    client.sonos_add_own_stream("Radio domowe", "https://radio.example/live")
    client.sonos_edit_own_stream(
        "stream-1", "Radio nowe", "https://radio.example/new"
    )
    client.sonos_remove_own_streams(["stream-1", "stream-2"])
    client.sonos_import_own_streams("C:/listy/sonos.m3u")
    client.sonos_sort_own_streams("Alphabetical")

    assert calls == [
        ("sonos.targets", None, 60.0),
        (
            "sonos.snapshot",
            {"householdId": "house-1", "groupId": "group-1"},
            45.0,
        ),
        (
            "sonos.transport",
            {
                "householdId": "house-1",
                "groupId": "group-1",
                "command": "seekRelative",
                "seconds": 30.0,
            },
            45.0,
        ),
        ("sonos.library", None, 10.0),
        (
            "sonos.materials",
            {"householdId": "house-1", "kind": "favorite"},
            60.0,
        ),
        (
            "sonos.materials",
            {"householdId": "house-1", "kind": "ownStream"},
            60.0,
        ),
        (
            "sonos.loadMaterial",
            {
                "householdId": "house-1",
                "groupId": "group-1",
                "kind": "favorite",
                "materialId": "favorite-1",
            },
            60.0,
        ),
        (
            "sonos.loadMaterial",
            {
                "householdId": "house-1",
                "groupId": "group-1",
                "kind": "ownStream",
                "materialId": "stream-1",
            },
            60.0,
        ),
        (
            "sonos.ownStreamEditInfo",
            {"streamId": "stream-1"},
            15.0,
        ),
        (
            "sonos.ownStreamAdd",
            {"name": "Radio domowe", "url": "https://radio.example/live"},
            30.0,
        ),
        (
            "sonos.ownStreamEdit",
            {
                "streamId": "stream-1",
                "name": "Radio nowe",
                "url": "https://radio.example/new",
            },
            30.0,
        ),
        (
            "sonos.ownStreamRemove",
            {"itemIds": ["stream-1", "stream-2"]},
            30.0,
        ),
        (
            "sonos.ownStreamImport",
            {"path": "C:/listy/sonos.m3u"},
            60.0,
        ),
        (
            "sonos.ownStreamSort",
            {"mode": "Alphabetical"},
            30.0,
        ),
    ]


def test_sonos_library_and_material_rows_keep_ids_out_of_spoken_text() -> None:
    categories = library_rows({
        "items": [{
            "itemId": "sonos.library.favorites",
            "title": "Ulubione Sonos",
            "detail": "Enter otwiera listę",
            "kind": "favorites",
        }]
    }, "house-technical")
    assert categories[0].title == "Ulubione Sonos"
    assert categories[0].detail == "Enter otwiera listę"
    assert categories[0].parent_id == "house-technical"
    assert "technical" not in categories[0].title
    assert "technical" not in categories[0].detail

    materials = material_rows({
        "items": [{
            "itemId": "sonos-favorite:technical-item",
            "materialId": "technical-material",
            "title": "Radio Poznań, TuneIn",
            "kind": "favorite",
            "runtimeObject": "Favorite { Id = technical-material }",
        }]
    }, "house-technical")
    assert materials[0].title == "Radio Poznań, TuneIn"
    assert materials[0].service_id == "technical-material"
    assert "technical" not in materials[0].title
    assert "runtimeObject" not in materials[0].detail


def test_sonos_dispatch_reaches_remote_volume_and_blocks_local_rate() -> None:
    spoken: list[str] = []
    volume_steps: list[int] = []
    frame = SimpleNamespace(
        navigator=SimpleNamespace(active=SessionId.SONOS),
        announcer=SimpleNamespace(say=spoken.append),
        messages=SimpleNamespace(custom_seek_seconds=300),
        _adjust_volume=volume_steps.append,
    )

    LiteFrame._dispatch(frame, Action.VOLUME_UP_5)
    assert volume_steps == [5]
    assert spoken == []

    LiteFrame._dispatch(frame, Action.RATE_UP)
    assert volume_steps == [5]
    assert spoken == ["To polecenie nie jest dostępne w sesji Sonos"]


def _queued_sonos_frame(submissions: list, spoken: list[str]) -> SimpleNamespace:
    calls: list[tuple] = []
    frame = SimpleNamespace(
        client=SimpleNamespace(
            sonos_transport=lambda *args, **kwargs: (
                calls.append((args, kwargs)) or {}
            )
        ),
        navigator=SimpleNamespace(active=SessionId.SONOS, view=View.PLAYER),
        announcer=SimpleNamespace(say=spoken.append),
        runner=SimpleNamespace(
            submit=lambda *args: submissions.append(args)
        ),
        _sonos_active_household_id="house-1",
        _sonos_active_group_id="group-1",
        _sonos_request_pending=False,
        _sonos_retry_pending=False,
        _sonos_pending_activation=None,
        _sonos_status_poll_pending=False,
        _sonos_command_queue=[],
        _sonos_transport_calls=calls,
    )
    frame._start_next_sonos_command = MethodType(
        LiteFrame._start_next_sonos_command, frame
    )
    frame._finish_sonos_request = MethodType(
        LiteFrame._finish_sonos_request, frame
    )
    return frame


def test_sonos_command_waits_while_snapshot_is_pending() -> None:
    submissions: list = []
    frame = _queued_sonos_frame(submissions, [])
    frame._sonos_request_pending = True

    LiteFrame._sonos_transport(frame, "toggle")

    assert submissions == []
    assert frame._sonos_command_queue == [
        ("house-1", "group-1", "toggle", None, None, 0)
    ]


def test_sonos_timer_does_not_overlap_a_read_or_waiting_command() -> None:
    submissions: list = []
    frame = _queued_sonos_frame(submissions, [])
    frame.client.sonos_snapshot = lambda *_args: {}
    frame._sonos_request_pending = True

    LiteFrame._refresh_sonos_status(frame)

    assert submissions == []
    assert frame._sonos_status_poll_pending is False

    frame._sonos_request_pending = False
    frame._sonos_command_queue.append(
        ("house-1", "group-1", "toggle", None, None, 0)
    )
    LiteFrame._refresh_sonos_status(frame)
    assert submissions == []


def test_finishing_sonos_read_starts_one_waiting_command() -> None:
    submissions: list = []
    frame = _queued_sonos_frame(submissions, [])
    frame._sonos_request_pending = True
    frame._sonos_command_queue.append(
        ("house-1", "group-1", "toggle", None, None, 0)
    )

    LiteFrame._finish_sonos_request(frame)

    assert len(submissions) == 1
    stream, work, _done, _failed = submissions[0]
    assert stream == "sonos-transport"
    assert frame._sonos_request_pending is True
    assert frame._sonos_command_queue == []
    work()
    assert frame._sonos_transport_calls == [
        (("house-1", "group-1", "toggle"), {
            "volume": None,
            "seconds": None,
        })
    ]


def test_busy_sonos_command_is_retried_without_speaking_error() -> None:
    submissions: list = []
    spoken: list[str] = []
    scheduled: list = []
    frame = _queued_sonos_frame(submissions, spoken)
    original_call_later = getattr(gui_module.wx, "CallLater", None)
    gui_module.wx.CallLater = (
        lambda _milliseconds, callback: scheduled.append(callback)
    )
    try:
        frame._sonos_command_queue.append(
            ("house-1", "group-1", "toggle", None, None, 0)
        )

        LiteFrame._start_next_sonos_command(frame)
        submissions[0][3](HostError("Trwa odczyt", code="operation_busy"))

        assert spoken == []
        assert frame._sonos_request_pending is False
        assert frame._sonos_retry_pending is True
        assert frame._sonos_command_queue == [
            ("house-1", "group-1", "toggle", None, None, 1)
        ]
        assert len(scheduled) == 1

        scheduled[0]()
        assert len(submissions) == 2
        assert frame._sonos_retry_pending is False
        assert frame._sonos_request_pending is True
    finally:
        if original_call_later is None:
            del gui_module.wx.CallLater
        else:
            gui_module.wx.CallLater = original_call_later


def test_busy_initial_sonos_read_is_retried_without_returning_to_list() -> None:
    submissions: list = []
    spoken: list[str] = []
    scheduled: list = []
    frame = _queued_sonos_frame(submissions, spoken)
    frame.client.sonos_snapshot = lambda *_args: {}
    frame.now_playing = SimpleNamespace(SetLabel=lambda _label: None)
    frame._set_transport_label = lambda **_kwargs: None
    frame._activate_sonos_group = MethodType(LiteFrame._activate_sonos_group, frame)
    original_call_later = getattr(gui_module.wx, "CallLater", None)
    gui_module.wx.CallLater = (
        lambda _milliseconds, callback: scheduled.append(callback)
    )
    intent = ActivateSonosGroup(
        "sonos:group-1", "Salon", "house-1", "group-1"
    )

    try:
        LiteFrame._activate_sonos_group(frame, intent)
        submissions[0][3](HostError("Trwa odczyt", code="operation_busy"))

        assert spoken == []
        assert frame.navigator.view is View.PLAYER
        assert frame._sonos_retry_pending is True
        scheduled[0]()
        assert len(submissions) == 2
        assert frame._sonos_request_pending is True
    finally:
        if original_call_later is None:
            del gui_module.wx.CallLater
        else:
            gui_module.wx.CallLater = original_call_later


def test_new_group_selection_wins_over_busy_command_retry() -> None:
    submissions: list = []
    scheduled: list = []
    frame = _queued_sonos_frame(submissions, [])
    frame.client.sonos_snapshot = lambda *_args: {}
    frame.now_playing = SimpleNamespace(SetLabel=lambda _label: None)
    frame._set_transport_label = lambda **_kwargs: None
    frame._activate_sonos_group = MethodType(LiteFrame._activate_sonos_group, frame)
    original_call_later = getattr(gui_module.wx, "CallLater", None)
    gui_module.wx.CallLater = (
        lambda _milliseconds, callback: scheduled.append(callback)
    )
    try:
        frame._sonos_command_queue.append(
            ("house-1", "group-1", "toggle", None, None, 0)
        )
        LiteFrame._start_next_sonos_command(frame)
        submissions[0][3](HostError("Trwa odczyt", code="operation_busy"))

        new_group = ActivateSonosGroup(
            "sonos:group-2", "Kuchnia", "house-1", "group-2"
        )
        LiteFrame._activate_sonos_group(frame, new_group)
        assert frame._sonos_pending_activation is new_group

        scheduled[0]()
        assert len(submissions) == 2
        assert submissions[1][0] == "sonos-snapshot"
        assert frame._sonos_active_group_id == "group-2"
        assert frame._sonos_pending_activation is None
    finally:
        if original_call_later is None:
            del gui_module.wx.CallLater
        else:
            gui_module.wx.CallLater = original_call_later
