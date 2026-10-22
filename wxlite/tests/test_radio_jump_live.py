from __future__ import annotations

from types import SimpleNamespace

from amc_wx_lite import menu_model
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.shortcuts import Action, Chord, describe, resolve
from amc_wx_lite.transport_parity import PLAYBACK_RATES


def test_end_is_live_for_radio_player_and_track_end_elsewhere() -> None:
    end = Chord("End")
    assert resolve(end, player_view=True, radio_session=True) is Action.RADIO_JUMP_LIVE
    assert resolve(end, player_view=True, radio_session=False) is Action.TRACK_END
    assert resolve(end, player_view=False, radio_session=True) is None


def test_radio_live_is_in_help_and_contextual_menu_only() -> None:
    assert ("End (Radio)", "Wróć do transmisji na żywo") in describe()

    item = next(
        item
        for menu in menu_model.build_menus()
        for item in menu.items
        if item.action is Action.RADIO_JUMP_LIVE
    )
    assert item.shortcut == "End"
    assert item.visible_sessions == (SessionId.RADIO,)
    assert item.needs_player_view is True
    assert "żywo" in item.label


def test_host_client_uses_dedicated_radio_operation() -> None:
    calls: list[tuple[str, dict]] = []
    client = object.__new__(LiteHostClient)
    client.call = lambda operation, args=None, **_kwargs: calls.append(
        (operation, args or {})
    ) or {"rate": 1.0}

    assert client.radio_jump_live() == {"rate": 1.0}
    assert calls == [("radio.jumpLive", {"sessionId": "radio"})]


def test_host_client_uses_dedicated_timeshift_percentage_operation() -> None:
    calls: list[tuple[str, dict]] = []
    client = object.__new__(LiteHostClient)
    client.call = lambda operation, args=None, **_kwargs: calls.append(
        (operation, args or {})
    ) or {"bufferPositionSeconds": 90.0, "bufferedSeconds": 180.0}

    assert client.radio_seek_percent(50) == {
        "bufferPositionSeconds": 90.0,
        "bufferedSeconds": 180.0,
    }
    assert calls == [
        ("radio.seekPercent", {"sessionId": "radio", "percentage": 50})
    ]


class _Runner:
    def __init__(self) -> None:
        self.name = ""

    def submit(self, name, work, done, _failed) -> None:
        self.name = name
        assert work() == {"behindLiveSeconds": 0.0, "rate": 1.0, "paused": False}
        done({"behindLiveSeconds": 0.0, "rate": 1.0, "paused": False})


class _Choice:
    def __init__(self) -> None:
        self.selection = -1

    def SetSelection(self, selection: int) -> None:
        self.selection = selection


def test_gui_completion_resets_visible_rate_and_announces_live() -> None:
    spoken: list[str] = []
    statuses: list[dict] = []
    runner = _Runner()
    choice = _Choice()
    frame = SimpleNamespace(
        client=SimpleNamespace(radio_jump_live=lambda: {
            "behindLiveSeconds": 0.0,
            "rate": 1.0,
            "paused": False,
        }),
        runner=runner,
        navigator=SimpleNamespace(active=SessionId.RADIO),
        _transport_status_by_session={SessionId.RADIO: {"rate": 1.5}},
        _last_status={"rate": 1.5},
        options=SimpleNamespace(rate=1.5),
        rate_choice=choice,
        announcer=SimpleNamespace(say=spoken.append),
        _update_native_playback_status=statuses.append,
    )

    LiteFrame._jump_radio_live(frame)

    assert runner.name == "radio-jump-live"
    assert frame.options.rate == 1.5, "Radio nie zmienia domyslu innych sesji"
    assert frame._runtime_rate_by_session[SessionId.RADIO] == 1.0
    assert choice.selection == PLAYBACK_RATES.index(1.0)
    assert frame._last_status["rate"] == 1.0
    assert statuses[-1]["behindLiveSeconds"] == 0.0
    assert spoken == ["Na żywo"]
