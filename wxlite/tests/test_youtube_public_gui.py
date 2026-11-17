"""Publiczne transmisje: rzeczywiste bramki poleceń, nie tylko wpis w menu."""
from types import SimpleNamespace
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_gui_logic import install_wx_stub
install_wx_stub()
from amc_wx_lite.gui import LiteFrame
from amc_wx_lite import menu_model
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.navigation import LibraryView, SessionId
from amc_wx_lite.shortcuts import Action, Chord, resolve


def test_public_capability_enables_ctrl_t_without_google_account():
    assert resolve(Chord("T", ctrl=True), player_view=False, radio_session=False,
                   podcast_session=True, youtube_channel=True,
                   youtube_account_available=False, youtube_broadcast_available=True) is Action.YOUTUBE_BROADCASTS


def test_public_broadcast_menu_and_palette_do_not_expose_google_account():
    required = {Action.YOUTUBE_BROADCASTS, Action.VIEW_YOUTUBE_LIVE_AGGREGATE,
                Action.CONFIGURE_YOUTUBE_LIVE_CHANNELS}
    menu_actions = {item.action for group in menu_model.menus_for_session(
        SessionId.PODCASTS, youtube_account_available=False, youtube_broadcast_available=True)
        for item in group.items}
    assert required <= menu_actions
    palette_actions = {item.action for item in entries_for_session(
        SessionId.PODCASTS, youtube_account_available=False, youtube_broadcast_available=True)}
    assert required <= palette_actions
    assert Action.YOUTUBE_ACCOUNT not in menu_actions | palette_actions


def test_public_aggregate_submits_scan_without_google_account():
    requests, messages = [], []
    state = SimpleNamespace(library_view=LibraryView.YOUTUBE_BROADCASTS_AGGREGATE,
                            model=SimpleNamespace(selected_id=None))
    frame = SimpleNamespace(
        _youtube_live_scan_pending=False, _youtube_live_scan_version=0,
        _youtube_account_available=False, _youtube_broadcast_available=True,
        _youtube_live_channels_by_id={}, client=object(),
        announcer=SimpleNamespace(say=messages.append),
        state=SimpleNamespace(youtube_live_channel_ids=["one"]),
        navigator=SimpleNamespace(active=SessionId.PODCASTS, session=state,
                                  sessions={SessionId.PODCASTS: state}),
        runner=SimpleNamespace(submit=lambda *args: requests.append(args)),
        _sync_views=lambda: None)
    LiteFrame._show_youtube_live_aggregate(frame)
    assert len(requests) == 1, messages
    assert frame._youtube_live_scan_pending


def test_radio_refresh_is_available_and_submits_without_google_account():
    for entries in (
        [item for group in menu_model.menus_for_session(
            SessionId.RADIO, youtube_account_available=False,
            youtube_broadcast_available=True) for item in group.items],
        entries_for_session(SessionId.RADIO, youtube_account_available=False,
                            youtube_broadcast_available=True),
    ):
        assert Action.REFRESH_YOUTUBE_RADIO_STATION in {item.action for item in entries}
    requests = []
    frame = SimpleNamespace(
        _selected_station=lambda: SimpleNamespace(url="https://www.youtube.com/@fixture/live"),
        _youtube_channel_subscriptions=lambda: [],
        client=object(), radio=SimpleNamespace(may_edit=True),
        _youtube_account_available=False, _youtube_broadcast_available=True,
        announcer=SimpleNamespace(say=lambda *_: None),
        runner=SimpleNamespace(submit=lambda *args: requests.append(args)))
    LiteFrame._refresh_selected_youtube_radio_station(frame)
    assert len(requests) == 1
    assert requests[0][0] == "radio-youtube-broadcast"


def test_unavailable_public_aggregate_reports_component_requirement_in_english():
    from amc_wx_lite import i18n
    messages = []
    frame = SimpleNamespace(_youtube_live_scan_pending=False,
                            _youtube_account_available=False,
                            _youtube_broadcast_available=False, client=object(),
                            announcer=SimpleNamespace(say=messages.append))
    previous = i18n.active_language()
    try:
        i18n.configure("en")
        LiteFrame._show_youtube_live_aggregate(frame)
        assert messages == ["Check the yt-dlp component or set up a YouTube account in the File menu"]
    finally:
        i18n.configure(previous)
