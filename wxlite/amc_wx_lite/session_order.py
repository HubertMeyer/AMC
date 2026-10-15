"""Prywatna kolejność sesji i wynikające z niej skróty ``Ctrl+1–9``.

Wartości modelu pozostają oddzielone od tekstów dostępnościowych.  Ten moduł
nie zna wx, dzięki czemu walidację zapisu, zawijanie kolejności i mapowanie
skrótów można sprawdzić bez otwierania okna.
"""

from __future__ import annotations

from collections.abc import Iterable

from .navigation import SessionId
from .shortcuts import Action


DEFAULT_SESSION_ORDER: tuple[SessionId, ...] = tuple(SessionId)

SESSION_ACTIONS: dict[SessionId, Action] = {
    SessionId.FILES: Action.SESSION_FILES,
    SessionId.RADIO: Action.SESSION_RADIO,
    SessionId.PODCASTS: Action.SESSION_PODCASTS,
    SessionId.TIDAL: Action.SESSION_TIDAL,
    SessionId.WIIM: Action.SESSION_WIIM,
    SessionId.SONOS: Action.SESSION_SONOS,
    SessionId.SPOTIFY: Action.SESSION_SPOTIFY,
}

SESSION_NAMES: dict[SessionId, str] = {
    SessionId.FILES: "Pliki lokalne",
    SessionId.RADIO: "Radio internetowe",
    SessionId.PODCASTS: "Podcasty i YouTube",
    SessionId.TIDAL: "TIDAL",
    SessionId.WIIM: "WiiM",
    SessionId.SONOS: "Sonos",
    SessionId.SPOTIFY: "Spotify",
}

SESSION_MENU_LABELS: dict[SessionId, str] = {
    SessionId.FILES: "Sesja: &Pliki lokalne",
    SessionId.RADIO: "Sesja: &Radio",
    SessionId.PODCASTS: "Sesja: Podcasty i &YouTube",
    SessionId.TIDAL: "Sesja: &TIDAL",
    SessionId.WIIM: "Sesja: &WiiM",
    SessionId.SONOS: "Sesja: &Sonos",
    SessionId.SPOTIFY: "Sesja: Spoti&fy",
}


def normalize(raw: object) -> tuple[SessionId, ...]:
    """Zachowaj znane, niepowtórzone sesje i dopisz brakujące na końcu."""

    values: Iterable[object]
    if isinstance(raw, (list, tuple)):
        values = raw
    else:
        values = ()

    result: list[SessionId] = []
    seen: set[SessionId] = set()
    for value in values:
        try:
            session = value if isinstance(value, SessionId) else SessionId(value)
        except (TypeError, ValueError):
            continue
        if session in seen:
            continue
        seen.add(session)
        result.append(session)

    result.extend(session for session in DEFAULT_SESSION_ORDER if session not in seen)
    return tuple(result)


def values(raw: object) -> list[str]:
    """Wartości do prywatnego JSON-u, nigdy etykiety wypowiadane przez NVDA."""

    return [session.value for session in normalize(raw)]


def slot_for_session(session: SessionId, raw: object) -> int:
    return normalize(raw).index(session) + 1


def session_for_slot(slot: int, raw: object) -> SessionId | None:
    ordered = normalize(raw)
    index = slot - 1
    return ordered[index] if 0 <= index < len(ordered) else None


def action_for_slot(slot: int, raw: object) -> Action | None:
    session = session_for_slot(slot, raw)
    return SESSION_ACTIONS.get(session) if session is not None else None


def adjacent(current: SessionId, direction: int, raw: object) -> SessionId:
    """Poprzednia/następna sesja z zawijaniem na obu końcach."""

    ordered = normalize(raw)
    try:
        index = ordered.index(current)
    except ValueError:
        index = 0
    step = -1 if direction < 0 else 1
    return ordered[(index + step) % len(ordered)]


def selection_labels(raw: object) -> tuple[str, ...]:
    return tuple(
        f"Ctrl+{slot}, {SESSION_NAMES[session]}"
        for slot, session in enumerate(normalize(raw), start=1)
    )
