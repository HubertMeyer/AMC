from __future__ import annotations

import json
from types import SimpleNamespace

from amc_wx_lite import menu_model, radio_recognition
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.shortcuts import Action, Chord, resolve
from amc_wx_lite.state_store import LiteState, Options, StateStore


def _host_entry(*, ticks: int, title: str = "Piosenka") -> dict:
    return {
        "stationId": "radio-1",
        "stationName": "Radio Poznań",
        "title": title,
        "artist": "Wykonawca",
        "album": "Album",
        "releaseDate": "2026",
        "providerUri": "https://example.test/wynik",
        "recognizedUtcTicks": ticks,
    }


def test_scope_labels_are_explicit_user_text() -> None:
    assert radio_recognition.scope_label("CurrentStation") == (
        "Tylko aktualnie odtwarzana stacja"
    )
    assert radio_recognition.normalize_scope("Technical.Enum.Value") == (
        radio_recognition.CURRENT_STATION
    )
    assert "CurrentStation" not in radio_recognition.scope_label("CurrentStation")


def test_host_result_is_persistable_and_recent_duplicate_is_not_added() -> None:
    now = radio_recognition.DOTNET_UNIX_EPOCH_TICKS + 900_000_000
    history: list[dict] = []
    payload = {"requested": 1, "recognized": [_host_entry(ticks=now)]}
    first = radio_recognition.merge_host_result(
        history, payload, current_ticks=now
    )
    second = radio_recognition.merge_host_result(
        history, payload, current_ticks=now + 10_000_000
    )
    assert len(first.added) == 1
    assert not first.duplicates
    assert not second.added
    assert len(second.duplicates) == 1
    assert len(history) == 1
    assert radio_recognition.track_label(history[0]).startswith(
        "Piosenka — Wykonawca, Radio Poznań, "
    )


def test_provider_uri_and_malformed_records_do_not_leak() -> None:
    ticks = radio_recognition.DOTNET_UNIX_EPOCH_TICKS + 10_000_000
    unsafe = _host_entry(ticks=ticks)
    unsafe["providerUri"] = "javascript:alert(1)"
    history: list[dict] = []
    radio_recognition.merge_host_result(
        history,
        {"requested": 1, "recognized": [unsafe]},
        current_ticks=ticks,
    )
    assert history[0]["providerUri"] == ""
    assert radio_recognition.read_tracks([{"id": "x", "title": object()}]) == []


def test_history_is_imported_only_from_the_radio_profile_section() -> None:
    ticks = radio_recognition.DOTNET_UNIX_EPOCH_TICKS + 10_000_000
    entry = {"id": "wynik-1", **_host_entry(ticks=ticks)}
    imported = radio_recognition.tracks_from_amc_state({
        "radio": {"recognizedTracks": [entry]},
        "recognizedTracks": [{"id": "nie-ten", **_host_entry(ticks=ticks)}],
    })
    assert imported == (radio_recognition.read_tracks([entry])[0],)
    assert radio_recognition.tracks_from_amc_state({
        "radio": {"recognizedTracks": "techniczny tekst"}
    }) == ()


def test_state_round_trip_keeps_settings_and_history(tmp_path) -> None:
    ticks = radio_recognition.DOTNET_UNIX_EPOCH_TICKS + 10_000_000
    store = StateStore(tmp_path)
    state = LiteState(
        options=Options(
            radio_recognition_monitoring=True,
            radio_recognition_scope=radio_recognition.CURRENT_AND_RECORDING_STATIONS,
            radio_recognition_announcements=False,
        ),
        recognized_tracks=[{
            "id": "wynik-1",
            **_host_entry(ticks=ticks),
        }],
        recognized_tracks_imported_from_amc=True,
    )
    store.save(state)
    loaded = store.load()
    assert loaded.options.radio_recognition_monitoring is True
    assert loaded.options.radio_recognition_scope == (
        radio_recognition.CURRENT_AND_RECORDING_STATIONS
    )
    assert loaded.options.radio_recognition_announcements is False
    assert loaded.recognized_tracks[0]["title"] == "Piosenka"
    assert loaded.recognized_tracks_imported_from_amc is True
    raw = json.loads(store.path.read_text(encoding="utf-8"))
    assert "recognized_tracks" in raw


def test_radio_shortcuts_match_the_original_window() -> None:
    assert resolve(
        Chord("S"), player_view=True, radio_session=True
    ) is Action.RECOGNIZE_RADIO_TRACK
    assert resolve(
        Chord("S", shift=True), player_view=True, radio_session=True
    ) is Action.TOGGLE_RADIO_RECOGNITION_MONITORING
    assert resolve(
        Chord("S", ctrl=True, alt=True),
        player_view=False,
        radio_session=True,
    ) is Action.VIEW_RADIO_RECOGNITION_HISTORY
    assert resolve(
        Chord("S", ctrl=True, alt=True, shift=True),
        player_view=False,
        radio_session=True,
    ) is Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS
    assert resolve(
        Chord("S"), player_view=False, radio_session=True
    ) is None


def test_radio_menu_exposes_same_actions_and_stateful_toggles() -> None:
    entries = [
        item
        for menu in menu_model.build_menus()
        for item in menu.items
        if item.action is not None
    ]
    by_action = {item.action: item for item in entries}
    assert by_action[Action.RECOGNIZE_RADIO_TRACK].shortcut == "S"
    assert by_action[Action.VIEW_RADIO_RECOGNITION_HISTORY].shortcut == "Ctrl+Alt+S"
    assert by_action[Action.TOGGLE_RADIO_RECOGNITION_MONITORING].checkable
    assert by_action[Action.TOGGLE_RADIO_RECOGNITION_ANNOUNCEMENTS].checkable


def test_client_sends_only_scope_not_audio() -> None:
    client = object.__new__(LiteHostClient)
    seen: dict = {}

    def call(op, args=None, *, timeout=20.0):
        seen.update(op=op, args=args, timeout=timeout)
        return {"requested": 0}

    client.call = call
    client.recognize_radio_tracks(radio_recognition.RECORDING_STATIONS)
    assert seen == {
        "op": "radio.recognition.run",
        "args": {"scope": "RecordingStations"},
        "timeout": 45.0,
    }


def test_paused_sources_do_not_keep_automatic_recognition_awake() -> None:
    frame = SimpleNamespace(
        options=Options(
            radio_recognition_scope=(
                radio_recognition.CURRENT_AND_RECORDING_STATIONS
            )
        ),
        _playing_sessions={SessionId.RADIO},
        _transport_status_by_session={SessionId.RADIO: {"paused": True}},
        _last_recording_status={
            "count": 1,
            "recordings": [{"state": "paused", "paused": True}],
        },
    )
    assert LiteFrame._recognition_source_available(frame) is False

    frame._last_recording_status["recordings"][0] = {
        "state": "recording",
        "paused": False,
    }
    assert LiteFrame._recognition_source_available(frame) is True
