"""Użytkowe informacje o jednym wierszu, bez technicznych identyfikatorów.

Ten moduł celowo nie zna wx. Alt+T może używać krótkiej informacji istniejącej
w GUI, a Alt+Enter dostaje tutaj pełny, testowalny tekst właściwości. Pola
``item_id`` i ``service_id`` nigdy nie są częścią wyniku.
"""

from __future__ import annotations

from .list_model import Row
from .radio_recording import format_duration


def _append_distinct(lines: list[str], label: str, value: str | None) -> None:
    text = (value or "").strip()
    if not text:
        return
    candidate = f"{label}: {text}"
    if candidate not in lines:
        lines.append(candidate)


def item_properties_text(
    row: Row,
    *,
    session_label: str,
    view_label: str = "",
) -> str:
    """Zbuduj czytelny tekst dialogu Alt+Enter.

    Model zachowuje osobno identyfikatory potrzebne hostowi. Tutaj korzystamy
    wyłącznie z pól przeznaczonych dla użytkownika: nazwy, etykiety rodzaju,
    metadanych, czasu oraz jawnego adresu lub ścieżki.
    """

    lines: list[str] = []
    _append_distinct(lines, "Nazwa", row.title)
    _append_distinct(lines, "Rodzaj", row.kind_label)
    _append_distinct(lines, "Sesja", session_label)
    _append_distinct(lines, "Widok", view_label)
    _append_distinct(lines, "Wykonawca", row.artist_name)
    _append_distinct(lines, "Album", row.related_album_title)
    _append_distinct(lines, "Podcast", row.related_podcast_title)
    _append_distinct(lines, "Szczegóły", row.detail)
    _append_distinct(lines, "Stan", row.state_detail or row.state_prefix)

    if row.duration_ticks > 0:
        _append_distinct(
            lines,
            "Czas trwania",
            format_duration(row.duration_ticks / 10_000_000),
        )
    if row.position_seconds > 0:
        _append_distinct(
            lines,
            "Pozycja",
            format_duration(row.position_seconds),
        )
    if row.path:
        _append_distinct(lines, "Ścieżka", row.path)
    elif row.url:
        _append_distinct(lines, "Adres", row.url)

    return "\r\n".join(lines)
