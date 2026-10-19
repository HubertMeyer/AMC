"""Wspólny stan dostępnych list celów należących do usług.

Moduł nie zna Spotify, TIDAL-a ani wxPython. Rozdziela dane modelu od tekstu
czytanego przez NVDA, izoluje pamięć według usługi i konta oraz pozwala
adapterom ponownie sprawdzać uprawnienia przy właściwym zapisie.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_SCOPE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_MAX_SCOPES = 32
_MAX_DESTINATIONS = 50


def normalize_scope(value: object) -> str:
    """Return a stable internal scope or an empty value for invalid input."""

    scope = value.strip().lower() if isinstance(value, str) else ""
    return scope if _SCOPE_PATTERN.fullmatch(scope) else ""


def normalize_destination_ids(raw: object) -> list[str]:
    """Keep only bounded, unique, stable identifiers from persisted state."""

    if not isinstance(raw, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for value in raw:
        destination_id = value.strip() if isinstance(value, str) else ""
        if not destination_id or destination_id in seen:
            continue
        seen.add(destination_id)
        result.append(destination_id)
        if len(result) >= _MAX_DESTINATIONS:
            break
    return result


def normalize_remembered_destinations(raw: object) -> dict[str, list[str]]:
    """Sanitize selections partitioned by service picker scope."""

    if not isinstance(raw, dict):
        return {}
    result: dict[str, list[str]] = {}
    for raw_scope, raw_ids in raw.items():
        scope = normalize_scope(raw_scope)
        ids = normalize_destination_ids(raw_ids)
        if not scope or not ids:
            continue
        result[scope] = ids
        if len(result) >= _MAX_SCOPES:
            break
    return result


def remembered_destination_ids(state: object, scope: str) -> list[str]:
    """Read one selection without exposing or returning the stored list."""

    normalized_scope = normalize_scope(scope)
    mapping = normalize_remembered_destinations(
        getattr(state, "service_picker_destination_ids", {})
    )
    if normalized_scope in mapping:
        return list(mapping[normalized_scope])
    # Jednorazowa zgodność z polem wdrożonym przed uogólnieniem mechanizmu.
    if normalized_scope == "spotify:playlists":
        return normalize_destination_ids(
            getattr(state, "spotify_playlist_destination_ids", [])
        )
    return []


def remember_destination_ids(state: object, scope: str, values: object) -> list[str]:
    """Persist a sanitized selection in the generic in-memory state object."""

    normalized_scope = normalize_scope(scope)
    ids = normalize_destination_ids(values)
    if not normalized_scope:
        return []
    mapping = normalize_remembered_destinations(
        getattr(state, "service_picker_destination_ids", {})
    )
    if ids:
        mapping[normalized_scope] = ids
    else:
        mapping.pop(normalized_scope, None)
    setattr(state, "service_picker_destination_ids", mapping)
    # Zachowaj zgodność wsteczną podczas przejścia jednej wersji ustawień.
    if normalized_scope == "spotify:playlists" and hasattr(
        state, "spotify_playlist_destination_ids"
    ):
        setattr(state, "spotify_playlist_destination_ids", list(ids))
    return list(ids)


@dataclass(frozen=True, slots=True)
class ServiceDestination:
    """Provider-owned target with deliberate presentation text."""

    destination_id: str
    name: str
    accessible_label: str

    def __post_init__(self) -> None:
        if not self.destination_id.strip():
            raise ValueError("Cel usługi wymaga stabilnego identyfikatora")
        if not self.name.strip() or not self.accessible_label.strip():
            raise ValueError("Cel usługi wymaga nazwy i dostępnej etykiety")


class ServiceDestinationCache:
    """Process-local snapshots isolated by provider scope and account."""

    def __init__(self) -> None:
        self._partitions: dict[
            tuple[str, str], tuple[ServiceDestination, ...]
        ] = {}

    @staticmethod
    def _key(scope: str, account_id: str = "") -> tuple[str, str]:
        normalized_scope = normalize_scope(scope)
        if not normalized_scope:
            raise ValueError("Nieprawidłowy zakres listy usługi")
        normalized_account = (
            account_id.strip() if isinstance(account_id, str) else ""
        )
        return normalized_scope, normalized_account

    def has_snapshot(self, scope: str, account_id: str = "") -> bool:
        return self._key(scope, account_id) in self._partitions

    def snapshot(
        self,
        scope: str,
        account_id: str = "",
    ) -> tuple[ServiceDestination, ...]:
        return self._partitions.get(self._key(scope, account_id), ())

    def replace(
        self,
        scope: str,
        destinations: list[ServiceDestination],
        account_id: str = "",
    ) -> tuple[ServiceDestination, ...]:
        unique: dict[str, ServiceDestination] = {}
        for destination in destinations:
            unique[destination.destination_id] = destination
        snapshot = tuple(unique.values())
        self._partitions[self._key(scope, account_id)] = snapshot
        return snapshot

    def merge_confirmed(
        self,
        scope: str,
        destinations: list[ServiceDestination],
        account_id: str = "",
    ) -> tuple[ServiceDestination, ...]:
        key = self._key(scope, account_id)
        merged = {
            destination.destination_id: destination
            for destination in self._partitions.get(key, ())
        }
        for destination in destinations:
            merged[destination.destination_id] = destination
        snapshot = tuple(merged.values())
        self._partitions[key] = snapshot
        return snapshot

    def invalidate(self, scope: str, account_id: str | None = None) -> None:
        normalized_scope = normalize_scope(scope)
        if not normalized_scope:
            return
        if account_id is not None:
            self._partitions.pop(self._key(normalized_scope, account_id), None)
            return
        for key in tuple(self._partitions):
            if key[0] == normalized_scope:
                self._partitions.pop(key, None)
