from __future__ import annotations

from amc_wx_lite.list_model import ListModel, Row
from amc_wx_lite.search_catalog import SearchEntry
from amc_wx_lite.spotify_source import (
    SpotifyContainerPayloadError,
    account_summary_from_payload,
    artist_overview_rows,
    container_result_from_payload,
    history_rows,
    information_text,
    normalize_history_payload,
    record_history_row,
    root_result_from_payload,
)
from amc_wx_lite.navigation import SessionId


def _payload() -> dict:
    return {
        "heading": "Biblioteka Spotify",
        "debug": "SpotifyItem { internal = secret }",
        "items": [
            {
                "id": f"private-row-{kind}",
                "externalId": f"spotify:{kind}:secret-{kind}",
                "title": title,
                "artist": "Wykonawca",
                "kind": kind,
                "durationTicks": 120 * 10_000_000 if kind in {"track", "episode"} else 0,
                "publicUri": f"https://open.spotify.invalid/{kind}/secret",
                "relatedAlbumExternalId": "spotify:album:private",
                "relatedAlbumTitle": "Album użytkowy",
                "relatedArtistExternalId": "spotify:artist:private",
                "relatedArtistName": "Wykonawca",
                "relatedPodcastExternalId": "spotify:show:private",
                "relatedPodcastTitle": "Podcast użytkowy",
                "unknownEnum": "InternalKind.Value",
            }
            for kind, title in (
                ("artist", "Wykonawca"),
                ("album", "Album"),
                ("playlist", "Playlista"),
                ("podcast", "Podcast"),
                ("track", "Utwór"),
                ("episode", "Odcinek"),
            )
        ],
    }


def test_explicit_payload_accepts_all_user_facing_spotify_kinds() -> None:
    result = container_result_from_payload(_payload())

    assert result.heading == "Biblioteka Spotify"
    assert [row.kind for row in result.rows] == [
        "artist", "album", "playlist", "podcast", "track", "episode"
    ]
    assert all(row.service_id for row in result.rows)
    assert result.rows[-1].related_podcast_title == "Podcast użytkowy"


def test_list_search_and_left_information_never_speak_ids_uri_enum_or_repr() -> None:
    result = container_result_from_payload(_payload())
    model = ListModel(list(result.rows))
    spoken = [
        model.text_for(index, column)
        for index in range(len(model.rows))
        for column in range(3)
    ]
    spoken.extend(
        SearchEntry(SessionId.SPOTIFY, row).accessible_label
        for row in result.rows
    )
    spoken.extend(information_text(row) for row in result.rows)
    all_spoken = " ".join(spoken)

    assert "secret" not in all_spoken
    assert "spotify:" not in all_spoken
    assert "https://" not in all_spoken
    assert "InternalKind" not in all_spoken
    assert "Row(" not in all_spoken
    assert "SessionId" not in all_spoken
    assert "Podcast użytkowy" in information_text(result.rows[-1])


def test_malformed_payload_has_one_short_user_facing_error() -> None:
    for payload, message in (
        ([], "Katalog Spotify zwrócił nieprawidłową odpowiedź"),
        ({"heading": "Biblioteka"}, "Katalog Spotify zwrócił niepełną odpowiedź"),
    ):
        try:
            container_result_from_payload(payload)
        except SpotifyContainerPayloadError as error:
            assert str(error) == message
        else:  # pragma: no cover - czytelna porażka także bez pytest
            raise AssertionError("Brak oczekiwanego błędu payloadu Spotify")


def test_malformed_and_duplicate_items_are_dropped_without_dumping_objects() -> None:
    payload = _payload()
    payload["items"].extend([
        object(),
        {"id": "missing-title", "externalId": "spotify:track:hidden", "kind": "track"},
        dict(payload["items"][0]),
    ])

    result = container_result_from_payload(payload)

    assert len(result.rows) == 6


def test_unplayable_item_has_an_intentional_message_not_a_model_value() -> None:
    payload = {
        "heading": "Album",
        "items": [{
            "id": "private-row",
            "externalId": "spotify:track:secret",
            "title": "Utwór niedostępny",
            "kind": "track",
            "isPlayable": False,
        }],
    }

    row = container_result_from_payload(payload).rows[0]

    assert row.activation_message == "Ten materiał nie jest obecnie dostępny do odtworzenia"
    assert "secret" not in row.activation_message


def test_real_litehost_fields_map_availability_and_episode_parent() -> None:
    payload = {
        "heading": "Odcinki podcastu",
        "items": [{
            "id": "spotify:episode:private-row",
            "externalId": "privateepisode",
            "title": "Odcinek",
            "artist": "Podcast użytkowy",
            "kind": "episode",
            "isAvailable": False,
            # Wspólny MediaItem zapisuje rodzica odcinka w RelatedAlbum*.
            "relatedAlbumExternalId": "privatepodcast",
            "relatedAlbumTitle": "Podcast użytkowy",
        }],
    }

    row = container_result_from_payload(payload).rows[0]

    assert row.activation_message == (
        "Ten materiał nie jest obecnie dostępny do odtworzenia"
    )
    assert row.related_podcast_service_id == "privatepodcast"
    assert row.related_podcast_title == "Podcast użytkowy"
    assert row.related_album_service_id is None
    assert "private" not in information_text(row)


def test_artist_overview_uses_only_two_explicit_labels() -> None:
    artist = Row(
        "private-row", "Wykonawca", "artist",
        service_id="spotify:artist:secret", service_kind="artist",
    )

    rows = artist_overview_rows(artist)

    assert [row.title for row in rows] == ["Albumy", "Utwory"]
    assert all("secret" not in row.title for row in rows)


def test_collection_root_uses_labels_and_keeps_view_keys_private() -> None:
    result = root_result_from_payload({
        "heading": "Biblioteka Spotify",
        "views": [
            {"view": "liked", "label": "Polubione utwory"},
            {"view": "artists", "label": "Wykonawcy"},
            {"view": "private-enum", "label": "Nie pokazuj"},
        ],
    })

    assert result.heading == "Biblioteka Spotify"
    assert [row.title for row in result.rows] == ["Polubione utwory", "Wykonawcy"]
    assert [row.service_id for row in result.rows] == ["liked", "artists"]
    spoken = " ".join(
        ListModel(list(result.rows)).text_for(index, column)
        for index in range(len(result.rows))
        for column in range(3)
    )
    assert "liked" not in spoken
    assert "artists" not in spoken
    assert "private-enum" not in spoken


def test_account_summary_returns_only_intentional_catalogue_label() -> None:
    summary = account_summary_from_payload({
        "catalog": {
            "state": "notConfigured",
            "connected": False,
            "label": "Katalog Spotify nie jest skonfigurowany.",
            "technical": "SpotifyCredential { Secret = hidden }",
        },
    })

    assert summary.label == "Katalog Spotify nie jest skonfigurowany."
    assert summary.connected is False
    assert "hidden" not in summary.label


def test_private_playback_history_is_newest_first_unique_and_accessible() -> None:
    first = Row(
        "private-first", "Pierwszy", "track",
        service_id="spotify-track-first", service_kind="track",
        artist_name="Wykonawca",
    )
    second = Row(
        "private-second", "Drugi", "episode",
        service_id="spotify-episode-second", service_kind="episode",
        artist_name="Podcast",
        related_podcast_service_id="spotify-show-parent",
        related_podcast_title="Podcast użytkowy",
    )

    stored = record_history_row([], first)
    stored = record_history_row(stored, second)
    stored = record_history_row(stored, first)
    rows = history_rows(stored)

    assert [row.title for row in rows] == ["Pierwszy", "Drugi"]
    assert rows[1].related_podcast_title == "Podcast użytkowy"
    spoken = " ".join(
        ListModel(list(rows)).text_for(index, column)
        for index in range(len(rows))
        for column in range(3)
    )
    assert "spotify-track-first" not in spoken
    assert "spotify-episode-second" not in spoken


def test_private_spotify_history_drops_unknown_fields_and_keeps_500_items() -> None:
    raw = [
        {
            "itemId": f"private-{index}",
            "externalId": f"external-{index}",
            "title": f"Utwór {index}",
            "kind": "track",
            "token": "nie zapisuj",
        }
        for index in range(510)
    ]
    raw.insert(1, dict(raw[0]))
    raw.insert(2, {"itemId": "bad", "kind": "InternalKind.Track"})

    stored = normalize_history_payload(raw)

    assert len(stored) == 500
    assert stored[0]["title"] == "Utwór 0"
    assert stored[1]["title"] == "Utwór 1"
    assert all("token" not in item for item in stored)
