from __future__ import annotations

from amc_wx_lite import menu_model
from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.list_model import Row
from amc_wx_lite.podcast_source import is_youtube_video_row
from amc_wx_lite.shortcuts import Action, Chord, resolve
from amc_wx_lite.state_store import Options


def test_youtube_video_shortcuts_are_semantic() -> None:
    assert resolve(
        Chord("D", ctrl=True, shift=True),
        player_view=False,
        radio_session=False,
        podcast_session=True,
        youtube_video_selection=True,
    ) is Action.DOWNLOAD_YOUTUBE_VIDEOS
    assert resolve(
        Chord("S", ctrl=True),
        player_view=False,
        radio_session=False,
        podcast_session=True,
        youtube_video_selection=True,
    ) is Action.SAVE_YOUTUBE_VIDEO_AS
    assert resolve(
        Chord("S", ctrl=True),
        player_view=False,
        radio_session=False,
        podcast_session=True,
        youtube_video_selection=False,
    ) is Action.SAVE_PODCAST_EPISODE_AS


def test_youtube_detection_uses_model_or_public_host_without_speaking_it() -> None:
    assert is_youtube_video_row(Row(
        "one", "Film", "episode", service_kind="youtubeVideo"
    ))
    assert is_youtube_video_row(Row(
        "two", "Film", "episode", url="https://youtu.be/abc"
    ))
    assert not is_youtube_video_row(Row(
        "three", "Podcast", "episode", url="https://example.test/audio.mp3"
    ))


def test_video_format_setting_has_safe_default() -> None:
    assert Options().podcast_youtube_video_format == "mp4"
    assert Options(podcast_youtube_video_format="technical-enum").clamp().podcast_youtube_video_format == "mp4"
    assert Options(podcast_youtube_video_format="original").clamp().podcast_youtube_video_format == "original"


def test_menu_exposes_both_video_commands_with_user_labels() -> None:
    entries = {
        item.action: item
        for menu in menu_model.build_menus()
        for item in menu.items
        if item.action is not None
    }
    assert entries[Action.DOWNLOAD_YOUTUBE_VIDEOS].shortcut == "Ctrl+Shift+D"
    assert entries[Action.SAVE_YOUTUBE_VIDEO_AS].shortcut == "Ctrl+S"
    assert entries[Action.SAVE_YOUTUBE_VIDEO_AS].needs_single_youtube_video_item


def test_host_client_video_operations_have_explicit_format() -> None:
    client = object.__new__(LiteHostClient)
    seen = []

    def call(op, args=None, *, timeout=20.0):
        seen.append((op, args, timeout))
        return {}

    client.call = call
    client.download_youtube_videos(["one", "one", "two"], "mp4")
    client.youtube_video_save_as_info("one")
    client.save_youtube_video_as("one", r"D:\Wideo\film.mp4", "original")
    assert seen[0][0:2] == (
        "podcast.videoDownload",
        {"episodeIds": ["one", "two"], "format": "mp4"},
    )
    assert seen[1][0] == "podcast.videoSaveAsInfo"
    assert seen[2][0:2] == (
        "podcast.videoSaveAs",
        {"episodeId": "one", "path": r"D:\Wideo\film.mp4", "format": "original"},
    )
