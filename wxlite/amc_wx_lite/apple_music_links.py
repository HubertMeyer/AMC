"""Anonymous Apple Music public-link lookup used by recognized tracks.

The iTunes Search endpoint requires no Apple ID, developer token or Music User
Token.  Only public track and album URLs are retained; failures simply leave
the always-available browser search action in place.
"""

from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .recognition_actions import APPLE_MUSIC, select_catalog_match, sanitize_match


SEARCH_ENDPOINT = "https://itunes.apple.com/search"


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _candidate(raw: object) -> dict | None:
    if not isinstance(raw, dict):
        return None
    title = _text(raw.get("trackName"))
    artist = _text(raw.get("artistName"))
    track_url = _text(raw.get("trackViewUrl"))
    if not title or not artist or not track_url:
        return None
    return {
        "title": title,
        "artist": artist,
        "album": _text(raw.get("collectionName")),
        "trackId": str(raw.get("trackId") or "").strip(),
        "collectionId": str(raw.get("collectionId") or "").strip(),
        "trackUrl": track_url,
        "albumUrl": _text(raw.get("collectionViewUrl")),
    }


def resolve_public_links(entry: dict, *, opener=urlopen, timeout: float = 12.0) -> dict | None:
    query = " ".join(
        value
        for value in (_text(entry.get("artist")), _text(entry.get("title")))
        if value
    )
    if not query:
        return None
    address = SEARCH_ENDPOINT + "?" + urlencode({
        "term": query,
        "entity": "song",
        "limit": "25",
        "country": "PL",
    })
    request = Request(address, headers={"Accept": "application/json", "User-Agent": "AMC-Test"})
    with opener(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raw_results = payload.get("results") if isinstance(payload, dict) else None
    candidates = [
        candidate
        for raw in (raw_results if isinstance(raw_results, list) else [])
        if (candidate := _candidate(raw)) is not None
    ]
    selected = select_catalog_match(entry, candidates)
    if selected is None:
        return None
    return sanitize_match({
        "service": APPLE_MUSIC,
        "itemId": "apple-track:" + selected["trackId"],
        "serviceId": selected["trackId"],
        "title": selected["title"],
        "artist": selected["artist"],
        "albumServiceId": selected["collectionId"],
        "albumTitle": selected["album"],
        "artistServiceId": "",
        "artistName": selected["artist"],
        "publicUrl": selected["trackUrl"],
        "albumUrl": selected["albumUrl"],
        "artistUrl": "",
        "appUri": "",
    }, expected_service=APPLE_MUSIC)
