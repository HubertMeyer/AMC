from __future__ import annotations

from types import SimpleNamespace

from amc_wx_lite.radio_recording import (
    recording_output_description,
    scheduled_recording_output_description,
)
from amc_wx_lite.shortcuts import Action, Chord, resolve


def test_active_recording_right_arrow_text_uses_effective_file_and_folder() -> None:
    assert recording_output_description({
        "format": "Mp3",
        "bitrateKbps": 192,
        "path": r"D:\Nagrania\audycja.mp3",
        "outputFolder": r"D:\Nagrania",
        "defaultFolder": "D:\\Nagrania\\",
    }) == "192 kb/s, plik audycja.mp3, folder domyślny"
    assert recording_output_description({
        "format": "Flac",
        "path": "",
        "outputFolder": r"E:\Radio",
        "defaultFolder": r"D:\Nagrania",
    }) == r"FLAC, plik przygotowywany, E:\Radio"


def test_schedule_right_arrow_has_no_source_or_url() -> None:
    message = scheduled_recording_output_description(
        {
            "stationName": "Radio Poznań",
            "url": "https://radio.example/stream",
            "recordingFormat": "Aac",
            "recordingBitrateKbps": 256,
            "outputFolder": "",
        },
        SimpleNamespace(format="Mp3", bitrate_kbps=192, default_folder=r"D:\Nagrania"),
    )
    assert message == "256 kb/s, plik przygotowywany, folder domyślny"
    assert "Poznań" not in message
    assert "http" not in message


def test_right_arrow_only_changes_meaning_in_active_recordings() -> None:
    assert resolve(
        Chord("Right"),
        player_view=False,
        radio_session=True,
        radio_recording_context=True,
    ) is Action.RECORDING_OUTPUT_INFORMATION
    assert resolve(
        Chord("Right"),
        player_view=False,
        radio_session=True,
        radio_recording_context=False,
    ) is None
