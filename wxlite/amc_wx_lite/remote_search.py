"""Bezpieczne wyniki publicznych katalogów podcastów, Mixcloud i YouTube.

Host C# wykonuje sieć i zwraca mały kontrakt. Ten moduł oddziela modelowe
identyfikatory od etykiet przeznaczonych dla użytkownika, odrzuca niepubliczne
adresy i scala wynik z lokalną biblioteką tak, by zapisany element zawsze
wygrywał z jego zdalnym odpowiednikiem.
"""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from .list_model import Row
from .navigation import LibraryView, SessionId
from .search_catalog import SearchEntry


REMOTE_KINDS = frozenset((
    "rss",
    "youtubeChannel",
    "youtubeVideo",
    "mixcloudChannel",
    "mixcloudShow",
))
ROW_KINDS = frozenset(("podcast", "episode"))


def _text(value: object, *, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    normalized = " ".join(value.split())
    return normalized[:limit].strip()


def public_address(value: object) -> str | None:
    """Zwróć publiczny adres HTTP(S) bez danych logowania."""

    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate or len(candidate) > 4096:
        return None
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except (ValueError, UnicodeError):
        return None
    if parsed.scheme.casefold() not in ("http", "https"):
        return None
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        return None
    if port is not None and not 1 <= port <= 65535:
        return None
    return candidate


def normalize_public_address(value: object) -> str | None:
    address = public_address(value)
    if address is None:
        return None
    parsed = urlsplit(address)
    host = (parsed.hostname or "").casefold()
    try:
        port = parsed.port
    except ValueError:
        return None
    default_port = (
        parsed.scheme.casefold() == "http" and port == 80
    ) or (
        parsed.scheme.casefold() == "https" and port == 443
    )
    authority = host if port is None or default_port else f"{host}:{port}"
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.casefold(), authority, path, parsed.query, ""))


def entries_from_payload(
    payload: object,
) -> tuple[list[SearchEntry], tuple[str, ...]]:
    """Zamień ograniczony kontrakt hosta na wiersze wxPython."""

    if not isinstance(payload, dict):
        raise ValueError("Nieprawidłowa odpowiedź katalogów podcastów")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("Nieprawidłowa odpowiedź katalogów podcastów")

    warnings = tuple(
        text
        for value in payload.get("warnings", [])
        if (text := _text(value, limit=180))
    ) if isinstance(payload.get("warnings", []), list) else ()
    entries: list[SearchEntry] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_items[:160]):
        if not isinstance(raw, dict):
            continue
        remote_kind = _text(raw.get("remoteKind"), limit=32)
        row_kind = _text(raw.get("kind"), limit=16)
        address = public_address(raw.get("address"))
        normalized = normalize_public_address(address)
        title = _text(raw.get("title"), limit=500)
        if (
            remote_kind not in REMOTE_KINDS
            or row_kind not in ROW_KINDS
            or not title
            or address is None
            or normalized is None
            or normalized in seen
        ):
            continue
        seen.add(normalized)
        internal_id = _text(raw.get("id"), limit=500) or f"remote:{index}"
        artist = _text(raw.get("artist"), limit=300)
        detail = _text(raw.get("detail"), limit=180)
        try:
            duration_ticks = max(0, int(raw.get("durationTicks") or 0))
        except (TypeError, ValueError, OverflowError):
            duration_ticks = 0
        entries.append(SearchEntry(
            SessionId.PODCASTS,
            Row(
                item_id=internal_id,
                title=title,
                kind=row_kind,
                url=address,
                detail=detail,
                artist_name=artist,
                duration_ticks=duration_ticks,
                service_kind=remote_kind,
            ),
            LibraryView.PODCAST_LIBRARY
            if row_kind == "podcast"
            else LibraryView.PODCAST_EPISODES,
            parent_id=(
                None if row_kind == "podcast" else "remote:internet-media"
            ),
            remote_kind=remote_kind,
        ))
    return entries, warnings


def radio_entries_from_payload(
    payload: object,
) -> tuple[list[SearchEntry], tuple[str, ...]]:
    """Zamień ograniczony kontrakt Radio Browser na bezpieczne wiersze."""

    if not isinstance(payload, dict):
        raise ValueError("Nieprawidłowa odpowiedź katalogu stacji radiowych")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("Nieprawidłowa odpowiedź katalogu stacji radiowych")

    warnings = tuple(
        text
        for value in payload.get("warnings", [])
        if (text := _text(value, limit=180))
    ) if isinstance(payload.get("warnings", []), list) else ()
    entries: list[SearchEntry] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_items[:120]):
        if not isinstance(raw, dict):
            continue
        address = public_address(raw.get("address"))
        normalized = normalize_public_address(address)
        title = _text(raw.get("title"), limit=500)
        if (
            _text(raw.get("remoteKind"), limit=32) != "radioStation"
            or _text(raw.get("kind"), limit=16) != "station"
            or not title
            or address is None
            or normalized is None
            or normalized in seen
        ):
            continue
        seen.add(normalized)
        internal_id = _text(raw.get("id"), limit=500) or f"remote-radio:{index}"
        entries.append(SearchEntry(
            SessionId.RADIO,
            Row(
                item_id=internal_id,
                title=title,
                kind="station",
                url=address,
                detail=_text(raw.get("detail"), limit=300),
            ),
            remote_kind="radioStation",
        ))
    return entries, warnings


def merge_saved_and_remote(
    saved: list[SearchEntry],
    remote: list[SearchEntry],
    *,
    saved_catalog: list[SearchEntry] | None = None,
) -> list[SearchEntry]:
    """Scal wyniki, zachowując lokalny element przy tym samym adresie."""

    result = list(saved)
    known_addresses = {
        normalized
        for entry in (saved_catalog if saved_catalog is not None else saved)
        if (normalized := normalize_public_address(entry.row.url)) is not None
    }
    known_ids = {
        (entry.session_id, entry.row.item_id)
        for entry in (saved_catalog if saved_catalog is not None else saved)
    }
    for entry in remote:
        normalized = normalize_public_address(entry.row.url)
        identity = (entry.session_id, entry.row.item_id)
        if normalized is None or normalized in known_addresses or identity in known_ids:
            continue
        known_addresses.add(normalized)
        known_ids.add(identity)
        result.append(entry)
    return result
