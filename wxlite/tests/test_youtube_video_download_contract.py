from __future__ import annotations

from amc_wx_lite import menu_model
from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite.list_model import Row
from amc_wx_lite.podcast_source import (
    PodcastSubscription,
    is_supported_video_row,
    is_youtube_video_row,
)
from amc_wx_lite.shortcuts import Action, Chord, _help_entries, resolve
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


def test_facebook_and_instagram_video_links_are_detected_but_profiles_are_not() -> None:
    for address in (
        "https://www.facebook.com/buremisie/videos/123456789/",
        "https://www.facebook.com/reel/123456789",
        "https://www.instagram.com/p/ABC123/",
        "https://www.instagram.com/reel/ABC123/",
        "https://www.instagram.com/example/reel/ABC123/",
    ):
        assert is_supported_video_row(Row("social", "Film", "episode", url=address))
    for address in (
        "https://www.facebook.com/buremisie/videos/",
        "https://www.facebook.com/buremisie",
        "https://www.instagram.com/someprofile/",
        "https://www.facebook.com.evil.example/videos/123",
    ):
        assert not is_supported_video_row(Row("profile", "Profil", "episode", url=address))


def test_video_command_discovery_mentions_supported_services() -> None:
    labels = {action: description for _, description, action in _help_entries()}
    assert "Facebooka" in labels[Action.DOWNLOAD_YOUTUBE_VIDEOS]
    assert "Instagrama" in labels[Action.DOWNLOAD_YOUTUBE_VIDEOS]
    assert "internetowy" in labels[Action.SAVE_YOUTUBE_VIDEO_AS]


def test_facebook_page_is_named_source_with_manual_refresh_and_audio_download() -> None:
    page = PodcastSubscription(
        "facebook-page:123456789", "Wspólnota Burego Misia", 5,
        "https://www.facebook.com/buremisie/",
    )
    row = page.as_row()
    assert row.detail == "strona Facebooka"
    assert row.service_kind == "facebookPage"
    assert row.url == "https://www.facebook.com/buremisie/"
    assert resolve(
        Chord("F5"), player_view=False, radio_session=False,
        podcast_session=True,
    ) is Action.REFRESH_PODCAST
    assert resolve(
        Chord("D", ctrl=True), player_view=False, radio_session=False,
        podcast_session=True,
    ) is Action.DOWNLOAD_PODCAST_EPISODES
    labels = {action: description for _, description, action in _help_entries()}
    assert "Facebooka" in labels[Action.ADD_PODCAST_SOURCE]
    assert "Facebooka" in labels[Action.REFRESH_PODCAST]
    assert "MP3" in labels[Action.DOWNLOAD_PODCAST_EPISODES]
    entries = {
        item.action: item
        for menu in menu_model.build_menus()
        for item in menu.items
        if item.action is not None
    }
    assert "Facebooka" in entries[Action.REFRESH_PODCAST].label
    assert "MP3" in entries[Action.DOWNLOAD_PODCAST_EPISODES].label


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
