"""Bezpieczna granica danych Frontier Smart między LiteHostem i wxPython."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .list_model import Row


class FrontierSmartPayloadError(ValueError):
    """Host zwrócił dane, których nie wolno pokazać jako kontrolki."""


@dataclass(frozen=True, slots=True)
class FrontierSmartPresetChoice:
    key: int
    title: str
    label: str


@dataclass(frozen=True, slots=True)
class FrontierSmartModeChoice:
    key: int
    label: str
    selected: bool
    enabled: bool


class FrontierSmartConfigurationPhase(str, Enum):
    """Jawny stan pierwszej konfiguracji i późniejszego zarządzania."""

    EMPTY = "empty"
    SAVED_DEVICES = "saved_devices"
    DISCOVERING = "discovering"
    DISCOVERY_RESULTS = "discovery_results"
    EMPTY_RESULT = "empty_result"
    ERROR = "error"
    MANUAL_ADDRESS = "manual_address"
    IDENTIFYING = "identifying"
    WAITING_FOR_PIN = "waiting_for_pin"


@dataclass(frozen=True, slots=True)
class FrontierSmartConfigurationState:
    saved_devices: tuple[Row, ...]
    selected_device_id: str
    phase: FrontierSmartConfigurationPhase
    message: str = ""
    discovered_devices: tuple[tuple[str, str], ...] = ()
    target_address: str = ""
    target_label: str = ""

    @property
    def should_auto_discover(self) -> bool:
        return self.phase is FrontierSmartConfigurationPhase.EMPTY

    @property
    def pin_allowed(self) -> bool:
        return (
            self.phase is FrontierSmartConfigurationPhase.WAITING_FOR_PIN
            and bool(self.target_address)
            and bool(self.target_label)
        )


def configuration_state(payload: object) -> FrontierSmartConfigurationState:
    rows = device_rows(payload)
    selected_device_id, message = device_list_state(payload)
    return FrontierSmartConfigurationState(
        saved_devices=rows,
        selected_device_id=selected_device_id,
        phase=(
            FrontierSmartConfigurationPhase.SAVED_DEVICES
            if rows
            else FrontierSmartConfigurationPhase.EMPTY
        ),
        message=message,
    )


def discovery_started(
    state: FrontierSmartConfigurationState,
) -> FrontierSmartConfigurationState:
    return replace(
        state,
        phase=FrontierSmartConfigurationPhase.DISCOVERING,
        message="Wykrywanie urządzeń w sieci lokalnej",
        discovered_devices=(),
        target_address="",
        target_label="",
    )


def discovery_finished(
    state: FrontierSmartConfigurationState,
    payload: object,
) -> FrontierSmartConfigurationState:
    choices = discovered_devices(payload)
    message = payload_message(payload)
    return replace(
        state,
        phase=(
            FrontierSmartConfigurationPhase.DISCOVERY_RESULTS
            if choices
            else FrontierSmartConfigurationPhase.EMPTY_RESULT
        ),
        message=message,
        discovered_devices=choices,
        target_address="",
        target_label="",
    )


def manual_address_started(
    state: FrontierSmartConfigurationState,
) -> FrontierSmartConfigurationState:
    return replace(
        state,
        phase=FrontierSmartConfigurationPhase.MANUAL_ADDRESS,
        message=(
            "Wpisz lokalny adres IP radia, a następnie wybierz "
            "Sprawdź urządzenie."
        ),
        discovered_devices=(),
        target_address="",
        target_label="",
    )


def identifying_started(
    state: FrontierSmartConfigurationState,
) -> FrontierSmartConfigurationState:
    return replace(
        state,
        phase=FrontierSmartConfigurationPhase.IDENTIFYING,
        message="Sprawdzanie urządzenia pod podanym adresem",
        target_address="",
        target_label="",
    )


def waiting_for_pin(
    state: FrontierSmartConfigurationState,
    address: str,
    label: str,
) -> FrontierSmartConfigurationState:
    safe_address = _text(address)
    safe_label = _text(label)
    if (
        not safe_address
        or not safe_label
        or safe_address.casefold() in safe_label.casefold()
    ):
        raise FrontierSmartPayloadError(
            "Nie udało się potwierdzić użytkowej nazwy urządzenia Frontier Smart"
        )
    if "teufel" in safe_label.casefold() and "3sixty" in safe_label.casefold():
        pin_help = (
            "Wpisz czterocyfrowy PIN NetRemote, nie hasło Wi-Fi. "
            "W Teufel RADIO 3SIXTY ustawienie fabryczne to 1234; "
            "można je sprawdzić w menu radia: Ustawienia systemowe, Sieć, "
            "Ustawienia NetRemote PIN."
        )
    else:
        pin_help = (
            "Wpisz PIN NetRemote, nie hasło Wi-Fi. Sprawdź go w ustawieniach "
            "sieciowych urządzenia."
        )
    return replace(
        state,
        phase=FrontierSmartConfigurationPhase.WAITING_FOR_PIN,
        message=(
            f"Wykryto urządzenie {safe_label}. {pin_help} "
            "Następnie wybierz Połącz i zapisz."
        ),
        target_address=safe_address,
        target_label=safe_label,
    )


def configuration_failed(
    state: FrontierSmartConfigurationState,
    message: str,
) -> FrontierSmartConfigurationState:
    return replace(
        state,
        phase=FrontierSmartConfigurationPhase.ERROR,
        message=_text(message) or "Nie udało się wykonać operacji.",
        discovered_devices=(),
        target_address="",
        target_label="",
    )


def device_rows(payload: object) -> tuple[Row, ...]:
    if not isinstance(payload, dict):
        raise FrontierSmartPayloadError(
            "Host Frontier Smart zwrócił nieprawidłową odpowiedź"
        )
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise FrontierSmartPayloadError(
            "Host Frontier Smart nie zwrócił listy urządzeń"
        )
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
            kind="frontierSmartDevice",
            detail=_text(raw.get("detail")),
            service_id=device_id,
            service_kind="frontierSmartDevice",
        ))
    return tuple(rows)


def should_auto_discover_devices(payload: object) -> bool:
    """Szukaj samoczynnie wyłącznie przy pustej, nieskonfigurowanej sesji."""

    return configuration_state(payload).should_auto_discover


def device_list_state(payload: object) -> tuple[str, str]:
    if not isinstance(payload, dict):
        raise FrontierSmartPayloadError(
            "Host Frontier Smart zwrócił nieprawidłową odpowiedź"
        )
    return _text(payload.get("selectedDeviceId")), _text(payload.get("message"))


def discovered_devices(payload: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise FrontierSmartPayloadError(
            "Host Frontier Smart nie zwrócił wyniku wykrywania"
        )
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in payload["items"]:
        if not isinstance(raw, dict):
            continue
        address = _text(raw.get("address"))
        label = _text(raw.get("label"))
        if (
            not address
            or not label
            or address in seen
            or address.casefold() in label.casefold()
        ):
            continue
        seen.add(address)
        result.append((address, label))
    return tuple(result)


def payload_message(payload: object) -> str:
    return _text(payload.get("message")) if isinstance(payload, dict) else ""


def snapshot(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise FrontierSmartPayloadError(
            "Host Frontier Smart zwrócił nieprawidłowy stan"
        )
    result = {
        name: _text(payload.get(name))
        for name in (
            "itemId", "deviceId", "deviceTitle", "title", "subtitle",
            "artist", "album", "playbackState", "message",
        )
    }
    result["muted"] = payload.get("muted") is True
    result["poweredOn"] = payload.get("poweredOn")
    volume = payload.get("volume")
    result["volume"] = (
        max(0, min(100, volume))
        if type(volume) is int
        else None
    )
    mode_key = payload.get("modeKey")
    result["modeKey"] = mode_key if type(mode_key) is int and mode_key >= 0 else None
    for name in ("positionSeconds", "durationSeconds"):
        value = payload.get(name)
        result[name] = (
            max(0.0, float(value))
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        )
    if not result["deviceId"]:
        raise FrontierSmartPayloadError(
            "Host Frontier Smart nie wskazał urządzenia"
        )
    return result


def preset_choices(
    payload: object,
) -> tuple[str, tuple[FrontierSmartPresetChoice, ...]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise FrontierSmartPayloadError(
            "Host Frontier Smart nie zwrócił listy presetów"
        )
    device_title = _text(payload.get("deviceTitle")) or "Frontier Smart"
    result: list[FrontierSmartPresetChoice] = []
    seen: set[int] = set()
    for raw in payload["items"]:
        if not isinstance(raw, dict):
            continue
        key = raw.get("presetKey")
        label = _text(raw.get("label"))
        name = _text(raw.get("name"))
        if type(key) is not int or key < 0 or not label or key in seen:
            continue
        seen.add(key)
        result.append(FrontierSmartPresetChoice(
            key=key,
            title=name or f"Preset {key + 1}",
            label=label,
        ))
    return device_title, tuple(result)


def mode_choices(
    payload: object,
) -> tuple[str, tuple[FrontierSmartModeChoice, ...], int]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise FrontierSmartPayloadError(
            "Host Frontier Smart nie zwrócił listy trybów"
        )
    device_title = _text(payload.get("deviceTitle")) or "Frontier Smart"
    result: list[FrontierSmartModeChoice] = []
    seen: set[int] = set()
    for raw in payload["items"]:
        if not isinstance(raw, dict):
            continue
        key = raw.get("key")
        label = _text(raw.get("label"))
        if type(key) is not int or key < 0 or not label or key in seen:
            continue
        seen.add(key)
        result.append(FrontierSmartModeChoice(
            key=key,
            label=label,
            selected=raw.get("selected") is True,
            enabled=raw.get("enabled") is True,
        ))
    selected_index = next(
        (index for index, choice in enumerate(result) if choice.selected),
        0,
    )
    return device_title, tuple(result), selected_index


def now_playing_label(state: dict) -> str:
    parts: list[str] = []
    for name in ("title", "subtitle", "artist", "album"):
        value = _text(state.get(name))
        if value and value.casefold() not in {part.casefold() for part in parts}:
            parts.append(value)
    if not parts:
        parts.append(_text(state.get("deviceTitle")) or "Frontier Smart")
    if state.get("muted"):
        parts.append("wyciszone")
    return ", ".join(parts)


def _text(value: object) -> str:
    return value.strip()[:500] if isinstance(value, str) else ""
