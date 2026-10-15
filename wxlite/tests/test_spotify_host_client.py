"""Narrow Python-to-host contract for Spotify catalogue and playback."""

from pathlib import Path

import pytest

from amc_wx_lite.host_client import HostError, LiteHostClient


def recording_client() -> tuple[
    LiteHostClient,
    list[tuple[str, dict | None, float]],
]:
    calls: list[tuple[str, dict | None, float]] = []
    client = LiteHostClient(Path("host.exe"))
    client.call = lambda op, args=None, *, timeout=20.0: (
        calls.append((op, args, timeout)) or {"ok": True}
    )
    return client, calls


def test_spotify_static_reads_send_no_account_or_authentication_data() -> None:
    client, calls = recording_client()

    client.spotify_capabilities()
    client.spotify_account_status()
    client.spotify_collection_root()

    assert calls == [
        ("spotify.capabilities", None, 15.0),
        ("spotify.accountStatus", None, 15.0),
        ("spotify.collectionRoot", None, 15.0),
    ]


def test_spotify_collection_view_sends_view_and_cumulative_page_size() -> None:
    client, calls = recording_client()

    client.spotify_collection_view("albums", loaded_count=300)

    assert calls == [
        ("spotify.collectionView", {"view": "albums", "loadedCount": 300}, 180.0),
    ]


def test_spotify_container_matches_the_csharp_contract_exactly() -> None:
    client, calls = recording_client()

    client.spotify_container_items(
        external_id="artist123",
        title="Wykonawca",
        kind="artist",
        artist="Wykonawca",
        artist_section="tracks",
    )

    assert calls == [(
        "spotify.containerItems",
        {
            "externalId": "artist123",
            "title": "Wykonawca",
            "kind": "artist",
            "artist": "Wykonawca",
            "artistSection": "tracks",
        },
        120.0,
    )]
    serialized = repr(calls).casefold()
    assert "token" not in serialized
    assert "credential" not in serialized
    assert "publicuri" not in serialized
    assert "source" not in serialized
    assert "itemid" not in serialized


def test_spotify_container_omits_empty_optional_fields() -> None:
    client, calls = recording_client()

    client.spotify_container_items(
        external_id="album123",
        title="Album",
        kind="album",
    )

    assert calls[0][1] == {
        "externalId": "album123",
        "title": "Album",
        "kind": "album",
    }


def test_spotify_search_sends_only_the_user_query() -> None:
    client, calls = recording_client()

    client.spotify_search("Artysta")

    assert calls == [
        ("spotify.search", {"query": "Artysta"}, 120.0),
    ]
    serialized = repr(calls).casefold()
    assert "token" not in serialized
    assert "credential" not in serialized
    assert "source" not in serialized


def test_spotify_play_sends_only_safe_item_identity_and_playback_values() -> None:
    client, calls = recording_client()

    client.spotify_play(
        item_id="spotify:track:track123:occurrence:2",
        title="Utwór",
        external_id="track123",
        kind="track",
        artist="Wykonawca",
        volume=37,
        position_seconds=12.5,
    )

    assert calls == [(
        "spotify.play",
        {
            "itemId": "spotify:track:track123:occurrence:2",
            "title": "Utwór",
            "externalId": "track123",
            "kind": "track",
            "artist": "Wykonawca",
            "volume": 37,
            "positionSeconds": 12.5,
        },
        60.0,
    )]
    serialized = repr(calls).casefold()
    assert "token" not in serialized
    assert "credential" not in serialized
    assert "source" not in serialized


def test_spotify_methods_preserve_the_hosts_user_facing_error() -> None:
    client = LiteHostClient(Path("host.exe"))

    def fail(op, args=None, *, timeout=20.0):
        raise HostError(
            "Katalog Spotify nie jest połączony. Otwórz ustawienia konta Spotify.",
            code="spotify-not-connected",
        )

    client.call = fail  # type: ignore[method-assign]

    with pytest.raises(HostError) as captured:
        client.spotify_search("Artysta")

    assert str(captured.value) == (
        "Katalog Spotify nie jest połączony. "
        "Otwórz ustawienia konta Spotify."
    )
    assert captured.value.code == "spotify-not-connected"
