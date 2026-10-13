"""Dane dostępnej palety poleceń AMC Python, bez zależności od wx.

Paleta nie przechowuje identyfikatorów tekstowych ani nazw enumów w etykiecie.
Każdy wpis prowadzi do istniejącej :class:`Action`, tej samej co menu i skrót.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import menu_model
from .navigation import SessionId
from .search_catalog import normalize_search_text, query_words
from .shortcuts import Action


@dataclass(frozen=True, slots=True)
class CommandPaletteEntry:
    action: Action
    name: str
    shortcut: str | None = None

    @property
    def label(self) -> str:
        if self.shortcut and self.shortcut.casefold() not in self.name.casefold():
            return f"{self.name}, {self.shortcut}"
        return self.name


def _plain_label(value: str) -> str:
    return " ".join(value.replace("&", "").split()).strip()


def _shortcut_label(value: str | None) -> str | None:
    if not value:
        return None
    parts = value.split("+")
    key = parts[-1]
    parts[-1] = {
        "Prior": "Page Up",
        "Next": "Page Down",
        "Return": "Enter",
        "Back": "Backspace",
        "Space": "Spacja",
        "Left": "strzałka w lewo",
        "Right": "strzałka w prawo",
        "Up": "strzałka w górę",
        "Down": "strzałka w dół",
    }.get(key, key)
    return "+".join(parts)


def entries_for_session(
    session: SessionId,
    session_order: object = None,
) -> tuple[CommandPaletteEntry, ...]:
    """Zbuduj po jednym użytkowym wpisie na akcję widoczną w tej sesji."""

    result: list[CommandPaletteEntry] = []
    seen: set[Action] = set()
    for menu in menu_model.menus_for_session(session, session_order):
        for item in menu.items:
            if item.is_separator or item.action is None or item.action in seen:
                continue
            name = _plain_label(item.label)
            if not name:
                continue
            seen.add(item.action)
            result.append(CommandPaletteEntry(
                action=item.action,
                name=name,
                shortcut=_shortcut_label(item.shortcut),
            ))
    return tuple(sorted(
        result,
        key=lambda entry: (normalize_search_text(entry.name), entry.label.casefold()),
    ))


def filter_entries(
    entries: tuple[CommandPaletteEntry, ...], query: str
) -> tuple[CommandPaletteEntry, ...]:
    """Filtruj po wszystkich słowach, bez rozróżniania wielkości i akcentów."""

    words = query_words(query)
    if not words:
        return entries
    return tuple(
        entry
        for entry in entries
        if all(word in normalize_search_text(entry.label) for word in words)
    )


def count_label(count: int) -> str:
    if count == 0:
        return "Brak pasujących poleceń"
    if count == 1:
        return "1 polecenie"
    if 2 <= count <= 4:
        return f"{count} polecenia"
    return f"{count} poleceń"
