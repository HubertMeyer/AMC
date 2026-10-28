"""Bezpieczna konfiguracja i teksty interfejsu konta YouTube.

AMC Test korzysta z lokalnego pliku sekretu, a AMC Public z publicznego
identyfikatora klienta i serwera wymiany tokenów HTTPS. Wartość sekretu nie
jest przekazywana w wierszu poleceń ani umieszczana w publicznym pakiecie.

Funkcje parsujące przyjmują ``object`` celowo.  Granica protokołu nigdy nie
przepuszcza ``repr`` słownika, nazwy klasy, identyfikatora kanału ani surowego
błędu do kontrolki dostępnościowej.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from .release_profile import ReleaseProfile, current_profile


CLIENT_ID_ENVIRONMENT = "AMC_YOUTUBE_CLIENT_ID"
CLIENT_ID_RESOURCE = "youtube-oauth-client-id.txt"
PUBLIC_CLIENT_ID_ENVIRONMENT = "AMC_YOUTUBE_PUBLIC_CLIENT_ID"
PUBLIC_CLIENT_ID_RESOURCE = "youtube-oauth-public-client-id.txt"
CLIENT_SECRET_FILE_ENVIRONMENT = "AMC_YOUTUBE_CLIENT_SECRET_FILE"
CLIENT_SECRET_RESOURCE = "youtube-oauth-client-secret.txt"
TOKEN_BROKER_ENVIRONMENT = "AMC_YOUTUBE_TOKEN_BROKER"
TOKEN_BROKER_RESOURCE = "youtube-oauth-public-token-broker.txt"
YOUTUBE_ACCOUNT_CAPABILITY = "youtube.account.readonly"


def _payload_field(payload: Mapping[str, object], name: str) -> object:
    """Odczytaj pole JSON niezależnie od zapisu camelCase/PascalCase.

    Host .NET mógł dotąd zwracać publiczne rekordy protokołu z nazwami
    ``Available`` i ``Connected``, natomiast lekkie atrapy Pythona używały
    ``available`` i ``connected``.  Pierwszy wariant ma pierwszeństwo tylko
    wtedy, gdy wariantu protokołowego Pythona w ogóle nie ma; sprzeczna para
    nie może po cichu nadpisać jawnej wartości camelCase.
    """

    if name in payload:
        return payload[name]
    pascal_name = name[:1].upper() + name[1:]
    return payload.get(pascal_name)


def _valid_client_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not 20 <= len(candidate) <= 512:
        return None
    if not candidate.endswith(".apps.googleusercontent.com"):
        return None
    if any(character.isspace() or ord(character) < 32 for character in candidate):
        return None
    return candidate


def resolve_youtube_client_id(
    environment: Mapping[str, str] | None = None,
    *,
    profile: ReleaseProfile | None = None,
    resource_path: Path | None = None,
) -> str | None:
    """Zwróć konfigurację tylko dla profilu, który jawnie ją dopuszcza."""

    selected_profile = profile or current_profile()
    if YOUTUBE_ACCOUNT_CAPABILITY not in selected_profile.capabilities:
        return None
    variables = os.environ if environment is None else environment
    environment_name = (
        PUBLIC_CLIENT_ID_ENVIRONMENT
        if selected_profile.profile_id == "public"
        else CLIENT_ID_ENVIRONMENT
    )
    configured = _valid_client_id(variables.get(environment_name))
    if configured is not None:
        return configured
    default_resource = (
        PUBLIC_CLIENT_ID_RESOURCE
        if selected_profile.profile_id == "public"
        else CLIENT_ID_RESOURCE
    )
    source = resource_path or Path(__file__).with_name(default_resource)
    try:
        if not source.is_file() or source.stat().st_size > 2048:
            return None
        return _valid_client_id(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None


def resolve_youtube_client_secret_file(
    environment: Mapping[str, str] | None = None,
    *,
    profile: ReleaseProfile | None = None,
    resource_path: Path | None = None,
) -> Path | None:
    """Zwróć wyłącznie ścieżkę do poprawnego pliku sekretu AMC Test.

    Host C# odczytuje samą wartość. Dzięki temu sekret nie trafia do wiersza
    poleceń procesu, modelu GUI, logu ani etykiet dostępnościowych.
    """

    selected_profile = profile or current_profile()
    if (
        selected_profile.profile_id != "test"
        or YOUTUBE_ACCOUNT_CAPABILITY not in selected_profile.capabilities
    ):
        return None
    variables = os.environ if environment is None else environment
    configured_path = variables.get(CLIENT_SECRET_FILE_ENVIRONMENT, "").strip()
    source = Path(configured_path) if configured_path else (
        resource_path or Path(__file__).with_name(CLIENT_SECRET_RESOURCE)
    )
    try:
        if not source.is_file() or not 8 <= source.stat().st_size <= 2048:
            return None
        value = source.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None
    if (
        not 8 <= len(value) <= 512
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        return None
    return source.resolve()


def _valid_token_broker(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate or len(candidate) > 2048 or "\n" in candidate or "\r" in candidate:
        return None
    try:
        parsed = urlsplit(candidate)
        _ = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path != "/v1/google/token"
    ):
        return None
    return candidate


def resolve_youtube_token_broker(
    environment: Mapping[str, str] | None = None,
    *,
    profile: ReleaseProfile | None = None,
    resource_path: Path | None = None,
) -> str | None:
    """Zwróć zweryfikowany endpoint tylko dla AMC Public."""

    selected_profile = profile or current_profile()
    if (
        selected_profile.profile_id != "public"
        or YOUTUBE_ACCOUNT_CAPABILITY not in selected_profile.capabilities
    ):
        return None
    variables = os.environ if environment is None else environment
    configured = _valid_token_broker(variables.get(TOKEN_BROKER_ENVIRONMENT))
    if configured is not None:
        return configured
    source = resource_path or Path(__file__).with_name(TOKEN_BROKER_RESOURCE)
    try:
        if not source.is_file() or source.stat().st_size > 2048:
            return None
        return _valid_token_broker(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None


def safe_message(payload: object, fallback: str) -> str:
    """Odczytaj wyłącznie jawny komunikat użytkowy z odpowiedzi hosta."""

    if isinstance(payload, Mapping):
        value = _payload_field(payload, "message")
        if isinstance(value, str):
            normalized = " ".join(value.split()).strip()
            if normalized:
                return normalized[:1000]
    return fallback


def account_connected(payload: object) -> bool:
    return (
        isinstance(payload, Mapping)
        and _payload_field(payload, "connected") is True
    )


def capability_available(payload: object) -> bool:
    """Czy rzeczywisty host potwierdził możliwość obsługi konta YouTube."""

    return (
        isinstance(payload, Mapping)
        and _payload_field(payload, "available") is True
    )


@dataclass(frozen=True, slots=True)
class YouTubeSyncPreview:
    additions: int
    restores: int
    already_present: int
    suppressed: int
    labels: tuple[str, ...]
    message: str


@dataclass(frozen=True, slots=True)
class YouTubePlaylistSyncPreview:
    additions: int
    restores: int
    updates: int
    suppressed: int
    truncated: int
    labels: tuple[str, ...]
    message: str


def _safe_count(payload: Mapping[str, object], name: str) -> int:
    value = _payload_field(payload, name)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def sync_preview(payload: object) -> YouTubeSyncPreview | None:
    """Zbuduj model listy wyłącznie z etykiet i liczników publicznego DTO."""

    if not isinstance(payload, Mapping):
        return None
    raw_labels = _payload_field(payload, "channelLabels")
    labels: list[str] = []
    if isinstance(raw_labels, list):
        for value in raw_labels[:200]:
            if not isinstance(value, str):
                continue
            label = " ".join(value.split()).strip()
            if label:
                labels.append(label[:500])
    return YouTubeSyncPreview(
        additions=_safe_count(payload, "additions"),
        restores=_safe_count(payload, "restores"),
        already_present=_safe_count(payload, "alreadyPresent"),
        suppressed=_safe_count(payload, "suppressed"),
        labels=tuple(labels),
        message=safe_message(
            payload,
            "Sprawdzono subskrypcje YouTube. Przejrzyj listę przed zapisem.",
        ),
    )


def playlist_sync_preview(payload: object) -> YouTubePlaylistSyncPreview | None:
    """Zbuduj bezpieczny model playlist bez technicznych identyfikatorów."""

    if not isinstance(payload, Mapping):
        return None
    raw_labels = _payload_field(payload, "playlistLabels")
    labels: list[str] = []
    if isinstance(raw_labels, list):
        for value in raw_labels[:200]:
            if not isinstance(value, str):
                continue
            label = " ".join(value.split()).strip()
            if label:
                labels.append(label[:500])
    return YouTubePlaylistSyncPreview(
        additions=_safe_count(payload, "additions"),
        restores=_safe_count(payload, "restores"),
        updates=_safe_count(payload, "updates"),
        suppressed=_safe_count(payload, "suppressed"),
        truncated=_safe_count(payload, "truncated"),
        labels=tuple(labels),
        message=safe_message(
            payload,
            "Sprawdzono playlisty YouTube. Przejrzyj listę przed zapisem.",
        ),
    )
