"""Regresje trasowania I/O do wlasciwego lokalnego odtwarzacza."""

from __future__ import annotations

from types import SimpleNamespace

from test_gui_logic import install_wx_stub

install_wx_stub()

from amc_wx_lite import gui  # noqa: E402 - najpierw zastepnik wx
from amc_wx_lite.navigation import SessionId, View  # noqa: E402


class ImmediateRunner:
    def submit(self, _slot, work, done, _failed):  # noqa: ANN001
        done(work())


class StatusClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requested_sessions: list[str | None] = []

    def status(self, session_id: str | None = None) -> dict:
        self.requested_sessions.append(session_id)
        return self.payload


def _frame(session: SessionId, source: str) -> tuple[object, StatusClient, list[str]]:
    payload = {
        "engine": "files",
        "sessionId": session.value,
        "id": f"file:{source}",
        "source": source,
        "title": "Nagrana Dwójka",
        "positionSeconds": 4_520.0,
        "durationSeconds": 4_530.0,
    }
    client = StatusClient(payload)
    spoken: list[str] = []
    frame = gui.LiteFrame.__new__(gui.LiteFrame)
    frame.client = client
    frame.navigator = SimpleNamespace(active=session, view=View.PLAYER)
    frame.runner = ImmediateRunner()
    frame.announcer = SimpleNamespace(say=spoken.append)
    frame._last_status = {}
    frame.state = SimpleNamespace(clip_selections=[])
    return frame, client, spoken


def test_recording_opened_from_history_queries_files_not_last_host_engine(
    tmp_path,
) -> None:
    recording = tmp_path / "2 - 2026-10-12 22-02-19.mp3"
    recording.write_bytes(b"ID3")
    frame, client, spoken = _frame(SessionId.FILES, str(recording))
    received: list[object] = []

    gui.LiteFrame._request_audio_clip_context(
        frame,
        lambda context, selection: received.append((context, selection)),
    )

    assert client.requested_sessions == ["files"]
    assert len(received) == 1
    assert received[0][0].source_path == str(recording)
    assert spoken == []


def test_downloaded_podcast_queries_podcast_session_explicitly(tmp_path) -> None:
    episode = tmp_path / "odcinek.mp3"
    episode.write_bytes(b"ID3")
    frame, client, spoken = _frame(SessionId.PODCASTS, str(episode))
    received: list[object] = []

    gui.LiteFrame._request_audio_clip_context(
        frame,
        lambda context, selection: received.append((context, selection)),
    )

    assert client.requested_sessions == ["podcasts"]
    assert len(received) == 1
    assert received[0][0].source_path == str(episode)
    assert spoken == []


def test_radio_player_does_not_fall_back_to_last_local_engine(tmp_path) -> None:
    recording = tmp_path / "radio.mp3"
    recording.write_bytes(b"ID3")
    frame, client, spoken = _frame(SessionId.RADIO, str(recording))
    received: list[object] = []

    gui.LiteFrame._request_audio_clip_context(
        frame,
        lambda context, selection: received.append((context, selection)),
    )

    assert client.requested_sessions == []
    assert received == []
    assert spoken == [
        "Wycinanie fragmentu jest dostępne dla plików lokalnych "
        "i pobranych odcinków podcastów"
    ]
