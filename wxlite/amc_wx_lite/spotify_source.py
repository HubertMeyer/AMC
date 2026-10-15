"""Pure, read-only Spotify DTO and accessibility presenter.

This module deliberately has no network, credentials, wx or playback code.
It accepts only a small explicit payload shaped like the existing TIDAL host
DTO, converts it into :class:`Row` objects, and keeps opaque Spotify IDs/URIs
outside every ordinary accessible label.
"""

from __future__ import annotations

from dataclasses import dataclass

from .list_model import Row
from .radio_recording import format_duration


_CONTAINER_KINDS = {"artist", "album", "playlist", "podcast"}
_PLAYABLE_KINDS = {"track", "episode"}
_KNOWN_KINDS = _CONTAINER_KINDS | _PLAYABLE_KINDS


class SpotifyContainerPayloadError(RuntimeError):
    """A short user-facing error for an invalid controller payload."""


@dataclass(frozen=True, slots=True)
class SpotifyContainerResult:
    heading: str
    rows: tuple[Row, ...]


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _ticks(value: object) -> int:
    return max(0, value) if type(value) is int else 0


def _kind(value: object) -> str | None:
    candidate = _text(value).casefold()
    return candidate if candidate in _KNOWN_KINDS else None


def _row(entry: object) -> Row | None:
    if not isinstance(entry, dict):
        return None
    item_id = _text(entry.get("id"))
    service_id = _text(entry.get("externalId"))
    title = _text(entry.get("title"))
    kind = _kind(entry.get("kind"))
    if not item_id or not service_id or not title or kind is None:
        return None

    artist = _text(entry.get("artist"))
    duration = _ticks(entry.get("durationTicks"))
    details: list[str] = []
    if artist and artist.casefold() != title.casefold():
        details.append(artist)
    if duration:
        details.append(format_duration(duration / 10_000_000))

    # LiteHost nazywa pole zgodnie ze wspólnym modelem ``isAvailable``.
    # ``isPlayable`` przyjmujemy także, aby czysty model mógł obsłużyć
    # późniejszy adapter odtwarzacza bez zmiany kontraktu wiersza.
    playable = (
        entry.get("isAvailable") is not False
        and entry.get("isPlayable") is not False
    )
    activation_message = None
    if kind in _PLAYABLE_KINDS and not playable:
        activation_message = "Ten materiał nie jest obecnie dostępny do odtworzenia"

    related_album_service_id = _text(entry.get("relatedAlbumExternalId")) or None
    related_album_title = _text(entry.get("relatedAlbumTitle"))
    related_podcast_service_id = (
        _text(entry.get("relatedPodcastExternalId")) or None
    )
    related_podcast_title = _text(entry.get("relatedPodcastTitle"))
    # Istniejący wspólny ``MediaItem`` przechowuje rodzica odcinka w polach
    # RelatedAlbum*. LiteHost celowo nie wystawia typu technicznego, więc na
    # granicy wx zamieniamy te pola na użytkową relację „podcast”.
    if kind == "episode":
        related_podcast_service_id = (
            related_podcast_service_id or related_album_service_id
        )
        related_podcast_title = related_podcast_title or related_album_title
        related_album_service_id = None
        related_album_title = ""

    return Row(
        item_id=item_id,
        title=title,
        kind=kind,
        url=_text(entry.get("publicUri")) or None,
        detail=", ".join(details),
        activation_message=activation_message,
        service_id=service_id,
        service_kind=kind,
        artist_name=artist,
        related_album_service_id=related_album_service_id,
        related_album_title=related_album_title,
        related_artist_service_id=(
            _text(entry.get("relatedArtistExternalId")) or None
        ),
        related_artist_name=_text(entry.get("relatedArtistName")),
        related_podcast_service_id=related_podcast_service_id,
        related_podcast_title=related_podcast_title,
        duration_ticks=duration,
    )


def container_result_from_payload(payload: object) -> SpotifyContainerResult:
    """Sanitize a controller answer before any value can reach wx or NVDA.

    The accepted payload is intentionally small::

        {"heading": str, "items": [{
            "id": str, "externalId": str, "title": str,
            "kind": "artist|album|playlist|podcast|track|episode",
            "artist": str?, "durationTicks": int?, "publicUri": str?,
            "isPlayable": bool?,
            "relatedAlbumExternalId": str?, "relatedAlbumTitle": str?,
            "relatedArtistExternalId": str?, "relatedArtistName": str?,
            "relatedPodcastExternalId": str?, "relatedPodcastTitle": str?
        }]}

    Unknown fields are ignored. IDs and ``publicUri`` stay private model data.
    """

    if not isinstance(payload, dict):
        raise SpotifyContainerPayloadError(
            "Katalog Spotify zwrócił nieprawidłową odpowiedź"
        )
    heading = _text(payload.get("heading"))
    raw_items = payload.get("items")
    if not heading or not isinstance(raw_items, list):
        raise SpotifyContainerPayloadError(
            "Katalog Spotify zwrócił niepełną odpowiedź"
        )

    rows: list[Row] = []
    seen: set[str] = set()
    for entry in raw_items:
        row = _row(entry)
        if row is None or row.item_id in seen:
            continue
        seen.add(row.item_id)
        rows.append(row)
    return SpotifyContainerResult(heading, tuple(rows))


def artist_overview_rows(artist: Row) -> tuple[Row, ...]:
    """Two explicit destinations below a Spotify artist."""

    if artist.kind != "artist" or not artist.service_id:
        return ()
    return tuple(
        Row(
            item_id=f"spotify-section:{artist.item_id}:{section}",
            title=label,
            kind="folder",
            service_id=artist.service_id,
            service_kind="artist",
            artist_name=artist.title,
            service_section=section,
        )
        for section, label in (("albums", "Albumy"), ("tracks", "Utwory"))
    )


def information_text(row: Row) -> str:
    """One deliberate Left-Arrow announcement without technical values."""

    values: list[str] = [row.title]
    if row.artist_name:
        values.append(f"Wykonawca: {row.artist_name}")
    values.append(f"Rodzaj: {row.kind_label or 'element'}")
    if row.kind == "track" and row.related_album_title:
        values.append(f"Album: {row.related_album_title}")
    if row.kind == "episode" and row.related_podcast_title:
        values.append(f"Podcast: {row.related_podcast_title}")
    if row.duration_ticks:
        values.append(
            f"Czas: {format_duration(row.duration_ticks / 10_000_000)}"
        )

    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return ", ".join(result)
