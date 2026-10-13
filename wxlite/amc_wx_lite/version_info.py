"""Czytelna tozsamosc uruchomionej paczki AMC Python.

Numer kompilacji pochodzi z podpisanego sumami manifestu paczki.  Nie
pokazujemy sciezek, obiektow ani surowych bledow parsera w tytule okna.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import __version__


_BUILD_LABEL = re.compile(
    r"^\d{4}\.\d{2}\.\d{2}(?:-[0-9a-f]{7,12})?(?:-robocza)?$",
    re.IGNORECASE,
)


def package_root(module_file: str | Path | None = None) -> Path:
    """Folder paczki zawierajacy ``AMC.exe`` i manifest."""

    source = Path(module_file) if module_file is not None else Path(__file__)
    return source.resolve().parents[2]


def read_build_label(root: str | Path | None = None) -> str:
    """Zwroc bezpieczna etykiete kompilacji albo pusty tekst."""

    base = Path(root) if root is not None else package_root()
    manifest = base / "bundle-manifest.json"
    try:
        if manifest.stat().st_size > 8 * 1024 * 1024:
            return ""
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ""
    label = payload.get("buildLabel") if isinstance(payload, dict) else None
    if not isinstance(label, str):
        return ""
    label = label.strip()
    return label if _BUILD_LABEL.fullmatch(label) else ""


def window_title(root: str | Path | None = None) -> str:
    """Tytul widoczny i czytany przez NVDA."""

    build = read_build_label(root)
    title = f"AMC Python — wersja {__version__}"
    return f"{title}, kompilacja {build}" if build else title


def is_main_window_title(title: str) -> bool:
    """Odróżnij główne okno od alertu „Diagnostyka AMC Python”."""

    return title == "AMC Python" or title.startswith("AMC Python — wersja ")
