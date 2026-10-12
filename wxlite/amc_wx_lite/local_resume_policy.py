"""Polityka wznawiania lokalnych plików dziedziczona z głównego AMC."""

from __future__ import annotations

import json
from pathlib import Path


def load_remember_local_playback_positions(state_path: Path) -> bool:
    """Odczytaj globalny wybór z profilu bez zapisywania go.

    Brak lub uszkodzenie starego profilu wraca do domyślnego ``True`` z
    ``AppSettings.RememberLocalPlaybackPositions``.
    """
    try:
        raw = json.loads(Path(state_path).read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return True
    if not isinstance(raw, dict):
        return True
    settings = raw.get("settings")
    if not isinstance(settings, dict):
        return True
    value = settings.get("rememberLocalPlaybackPositions")
    return value if type(value) is bool else True


def resolve_remember_local_playback_positions(
    override: bool | None,
    inherited: bool,
) -> bool:
    """Jawny wybór wxPython albo migracyjne dziedziczenie z profilu AMC."""
    return override if type(override) is bool else inherited
