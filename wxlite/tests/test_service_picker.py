"""Wspólny kontrakt zdalnych list wyboru dla obecnych i przyszłych usług."""

from __future__ import annotations

from types import SimpleNamespace

from amc_wx_lite.service_picker import (
    ServiceDestination,
    ServiceDestinationCache,
    normalize_remembered_destinations,
    remember_destination_ids,
    remembered_destination_ids,
)


def destination(destination_id: str, name: str) -> ServiceDestination:
    return ServiceDestination(destination_id, name, f"{name}, prywatna")


def test_cache_reuses_snapshot_and_isolates_service_and_account() -> None:
    cache = ServiceDestinationCache()
    cache.replace("spotify:playlists", [destination("same", "Spotify")], "anna")
    cache.replace("tidal:playlists", [destination("same", "TIDAL")], "anna")
    cache.replace("spotify:playlists", [destination("same", "Inne konto")], "ewa")

    assert cache.has_snapshot("spotify:playlists", "anna")
    assert [item.name for item in cache.snapshot("spotify:playlists", "anna")] == [
        "Spotify"
    ]
    assert [item.name for item in cache.snapshot("tidal:playlists", "anna")] == [
        "TIDAL"
    ]
    assert [item.name for item in cache.snapshot("spotify:playlists", "ewa")] == [
        "Inne konto"
    ]


def test_confirmed_creation_merges_only_the_selected_partition() -> None:
    cache = ServiceDestinationCache()
    cache.replace("spotify:playlists", [destination("old", "Stara")])
    cache.replace("tidal:playlists", [destination("tidal", "TIDAL")])

    cache.merge_confirmed(
        "spotify:playlists",
        [destination("new", "Nowa"), destination("old", "Zmieniona")],
    )

    assert [
        (item.destination_id, item.name)
        for item in cache.snapshot("spotify:playlists")
    ] == [("old", "Zmieniona"), ("new", "Nowa")]
    assert [item.destination_id for item in cache.snapshot("tidal:playlists")] == [
        "tidal"
    ]


def test_invalidation_can_target_one_account_or_a_whole_service() -> None:
    cache = ServiceDestinationCache()
    cache.replace("spotify:playlists", [], "anna")
    cache.replace("spotify:playlists", [destination("one", "Jedna")], "ewa")
    cache.replace("tidal:playlists", [destination("two", "Druga")], "anna")

    cache.invalidate("spotify:playlists", "anna")
    assert not cache.has_snapshot("spotify:playlists", "anna")
    assert cache.has_snapshot("spotify:playlists", "ewa")
    cache.invalidate("spotify:playlists")
    assert not cache.has_snapshot("spotify:playlists", "ewa")
    assert cache.has_snapshot("tidal:playlists", "anna")


def test_remembered_selections_are_sanitized_and_partitioned() -> None:
    state = SimpleNamespace(
        service_picker_destination_ids={
            "tidal:playlists": ["tidal-one"],
        },
        spotify_playlist_destination_ids=["legacy"],
    )

    assert remembered_destination_ids(state, "spotify:playlists") == ["legacy"]
    assert remember_destination_ids(
        state,
        "spotify:playlists",
        [" one ", "one", "two", ""],
    ) == ["one", "two"]
    assert remembered_destination_ids(state, "tidal:playlists") == ["tidal-one"]
    assert state.spotify_playlist_destination_ids == ["one", "two"]
    assert normalize_remembered_destinations(
        state.service_picker_destination_ids
    ) == {
        "tidal:playlists": ["tidal-one"],
        "spotify:playlists": ["one", "two"],
    }
