"""Jawny model listy i migawki WiiM dla natywnych kontrolek wx."""

from __future__ import annotations

from dataclasses import dataclass

from .list_model import Row


class WiiMPayloadError(ValueError):
    """Host zwrocil odpowiedz, ktorej nie wolno pokazac jako listy."""


@dataclass(frozen=True, slots=True)
class WiiMPresetChoice:
    """Jedno miejsce urządzenia; do kontrolki trafia wyłącznie ``label``."""

    number: int
    label: str
    occupied: bool
    current: bool
    activation_error: str


def device_rows(payload: object) -> tuple[Row, ...]:
    """Przyjmij tylko celowe etykiety; nigdy repr obiektu ani adres IP."""
    if not isinstance(payload, dict):
        raise WiiMPayloadError("Host WiiM zwrócił nieprawidłową odpowiedź")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise WiiMPayloadError("Host WiiM nie zwrócił listy urządzeń")

    rows: list[Row] = []
    seen: set[str] = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item_id = _text(raw.get("itemId"))
        device_id = _text(raw.get("deviceId"))
        title = _text(raw.get("title"))
        if not item_id or not device_id or not title or item_id in seen:
            continue
        seen.add(item_id)
        rows.append(Row(
            item_id=item_id,
            title=title,
            kind="device",
            detail=_text(raw.get("detail")),
            service_id=device_id,
            service_kind="device",
        ))
    return tuple(rows)


def network_stream_rows(payload: object, *, device_id: str) -> tuple[Row, ...]:
    """Zapisane strumienie WiiM bez adresów w tekście dostępnym.

    ``device_id`` pozostaje polem modelu potrzebnym do wykonania Entera.
    Nazwa, rodzaj i licznik wiersza są jedynymi wartościami przekazywanymi
    natywnej liście oraz NVDA.
    """
    if not isinstance(payload, dict):
        raise WiiMPayloadError("Host WiiM zwrócił nieprawidłową odpowiedź")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise WiiMPayloadError("Host WiiM nie zwrócił listy strumieni")
    if not isinstance(device_id, str) or not device_id.strip():
        raise WiiMPayloadError("Nie wybrano urządzenia WiiM")

    rows: list[Row] = []
    seen: set[str] = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item_id = _text(raw.get("itemId"))
        stream_id = _text(raw.get("streamId"))
        title = _text(raw.get("title"))
        if not item_id or not stream_id or not title or item_id in seen:
            continue
        seen.add(item_id)
        rows.append(Row(
            item_id=item_id,
            title=title,
            kind="wiimNetworkStream",
            detail=_text(raw.get("detail")) or "Strumień sieciowy",
            parent_id=device_id.strip(),
            service_id=stream_id,
            service_kind="wiimNetworkStream",
        ))
    return tuple(rows)


def snapshot(payload: object) -> dict:
    """Odetnij nieznane pola przed użyciem danych do nazw kontrolek."""
    if not isinstance(payload, dict):
        raise WiiMPayloadError("Host WiiM zwrócił nieprawidłowy stan")
    result = {
        name: _text(payload.get(name))
        for name in (
            "itemId", "deviceId", "deviceTitle", "title", "subtitle",
            "artist", "album", "source", "playbackState", "message",
        )
    }
    result["muted"] = payload.get("muted") is True
    volume = payload.get("volume")
    result["volume"] = (
        max(0, min(100, volume))
        if isinstance(volume, int) and not isinstance(volume, bool)
        else 0
    )
    for name in ("positionSeconds", "durationSeconds"):
        value = payload.get(name)
        result[name] = (
            max(0.0, float(value))
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        )
    return result


def preset_choices(payload: object) -> tuple[str, tuple[WiiMPresetChoice, ...]]:
    """Przyjmij dokładnie 12 celowo opisanych miejsc, bez adresów i repr."""
    if not isinstance(payload, dict):
        raise WiiMPayloadError("Host WiiM zwrócił nieprawidłową listę presetów")
    device_title = _text(payload.get("deviceTitle")) or "WiiM"
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise WiiMPayloadError("Host WiiM nie zwrócił listy presetów")

    choices: dict[int, WiiMPresetChoice] = {}
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        number = raw.get("presetNumber")
        label = _text(raw.get("label"))
        if (
            type(number) is not int
            or not 1 <= number <= 12
            or not label
            or number in choices
        ):
            continue
        choices[number] = WiiMPresetChoice(
            number=number,
            label=label,
            occupied=raw.get("occupied") is True,
            current=raw.get("current") is True,
            activation_error=_text(raw.get("activationError")),
        )
    if set(choices) != set(range(1, 13)):
        raise WiiMPayloadError("Host WiiM zwrócił niepełną listę presetów")
    return device_title, tuple(choices[number] for number in range(1, 13))


def now_playing_label(state: dict) -> str:
    """Nazwa kontrolki transportu: tylko treść dla użytkownika."""
    parts: list[str] = []
    for name in ("title", "subtitle", "artist", "album"):
        value = _text(state.get(name))
        if value and value.casefold() not in {part.casefold() for part in parts}:
            parts.append(value)
    if not parts:
        parts.append(_text(state.get("deviceTitle")) or "WiiM")
    if state.get("muted"):
        parts.append("wyciszone")
    return ", ".join(parts)


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
