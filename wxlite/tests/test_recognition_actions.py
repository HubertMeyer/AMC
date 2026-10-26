from __future__ import annotations

import io
import json

from amc_wx_lite import apple_music_links, radio_recognition
from amc_wx_lite.list_model import Row
from amc_wx_lite.recognition_actions import (
    APPLE_MUSIC,
    SPOTIFY,
    TIDAL,
    action_url,
    all_actions,
    cached_matches,
    match_from_row,
    quick_actions,
    select_catalog_match,
    store_match,
)
from amc_wx_lite.state_store import LiteState, Options, StateStore


def _entry() -> dict:
    return {
        "id": "recognized-1",
        "title": "Kto Dał Nam Deszcz (1980)",
        "artist": "Krystyna Prońko",
        "album": "Osobista Kolekcja 2",
        "stationName": "Poznań",
        "recognizedUtcTicks": 638000000000000000,
    }


def _spotify_row() -> Row:
    return Row(
        item_id="spotify-track-1",
        title="Kto Dał Nam Deszcz (1980)",
        kind="track",
        url="https://open.spotify.com/track/track-1",
        service_id="track-1",
        service_kind="track",
        artist_name="Krystyna Pronko",
        related_album_service_id="album-1",
        related_album_title="Osobista Kolekcja 2",
        related_artist_service_id="artist-1",
        related_artist_name="Krystyna Prońko",
    )


def test_shared_action_model_keeps_right_arrow_short_and_context_complete() -> None:
    entry = _entry()
    quick = quick_actions(entry, TIDAL)
    complete = all_actions(entry, TIDAL)
    assert quick
    assert set(quick).issubset(set(complete))
    assert quick[0].label == "Krystyna Prońko — wykonawca"
    assert quick[1].label == "Osobista Kolekcja 2 — album"
    labels = {action.label for action in complete}
    assert "Spotify — pokaż utwór w AMC" in labels
    assert "TIDAL — pokaż utwór w AMC" in labels
    assert "Apple Music — wyszukaj w przeglądarce" in labels


def test_catalogue_match_is_conservative_and_diacritic_tolerant() -> None:
    selected = select_catalog_match(_entry(), [
        {"title": "Inny utwór", "artist": "Krystyna Prońko", "album": "Album"},
        {
            "title": "Kto Dal Nam Deszcz 1980",
            "artist": "Krystyna Pronko",
            "album": "Osobista Kolekcja 2",
            "publicUrl": "https://example.test/right",
        },
    ])
    assert selected is not None
    assert selected["publicUrl"].endswith("/right")


def test_exact_service_match_round_trips_through_state(tmp_path) -> None:
    entry = _entry()
    match = match_from_row(SPOTIFY, _spotify_row())
    assert store_match(entry, match)
    assert action_url(
        next(action for action in all_actions(entry, SPOTIFY)
             if action.action_id == "spotify.amc.album"),
        match,
    ) == "https://open.spotify.com/album/album-1"
    store = StateStore(tmp_path)
    store.save(LiteState(
        options=Options(radio_recognition_default_service=TIDAL),
        recognized_tracks=[entry],
    ))
    loaded = store.load()
    assert loaded.options.radio_recognition_default_service == TIDAL
    assert cached_matches(loaded.recognized_tracks[0])[SPOTIFY]["serviceId"] == "track-1"


def test_apple_music_lookup_is_anonymous_and_returns_public_links() -> None:
    payload = json.dumps({"results": [{
        "trackName": "Kto Dal Nam Deszcz 1980",
        "artistName": "Krystyna Pronko",
        "collectionName": "Osobista Kolekcja 2",
        "trackId": 101,
        "collectionId": 202,
        "trackViewUrl": "https://music.apple.com/pl/song/example/101",
        "collectionViewUrl": "https://music.apple.com/pl/album/example/202",
    }]}).encode("utf-8")
    seen = {}

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    def opener(request, *, timeout):
        seen["url"] = request.full_url
        seen["authorization"] = request.get_header("Authorization")
        seen["timeout"] = timeout
        return Response(payload)

    match = apple_music_links.resolve_public_links(_entry(), opener=opener)
    assert match is not None
    assert match["service"] == APPLE_MUSIC
    assert match["albumUrl"].endswith("/202")
    assert "itunes.apple.com/search" in seen["url"]
    assert seen["authorization"] is None


def test_clipboard_description_remains_multiline_and_uses_cached_exact_link() -> None:
    entry = _entry()
    store_match(entry, match_from_row(SPOTIFY, _spotify_row()))
    description = radio_recognition.copy_text(entry)
    assert "\nWykonawca: Krystyna Prońko" in description
    assert radio_recognition.service_links(entry)["Spotify"].endswith("/track/track-1")
