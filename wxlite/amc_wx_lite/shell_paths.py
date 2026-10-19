"""Bezpieczne, testowalne otwieranie lokalnych ścieżek w Eksploratorze.

Moduł nie zna wx ani modelu listy. Dzięki temu adres internetowy nigdy nie
zostanie potraktowany jak folder, a testy nie muszą naprawdę otwierać okna
Eksploratora.
"""

from __future__ import annotations

import ntpath
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Callable


NO_LOCAL_FILE_MESSAGE = "Ten element nie ma lokalnego pliku"
MISSING_LOCAL_FILE_MESSAGE = "Nie znaleziono lokalnego pliku"
OPEN_LOCAL_FILE_ERROR_MESSAGE = "Nie udało się otworzyć folderu pliku"

_DRIVE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


class ShellPathError(ValueError):
    """Błąd gotowy do przekazania użytkownikowi, bez technicznych szczegółów."""


@dataclass(frozen=True, slots=True)
class ExplorerTarget:
    path: str
    select_file: bool

    @property
    def arguments(self) -> tuple[str, ...]:
        if self.select_file:
            return ("explorer.exe", "/select,", self.path)
        return ("explorer.exe", self.path)


def looks_like_local_path(value: object) -> bool:
    """Rozpoznaj pełną ścieżkę dysku albo UNC, nigdy URL ani identyfikator."""

    text = str(value or "").strip()
    return bool(_DRIVE_PATH.match(text) or text.startswith((r"\\", "//")))


def explorer_target(
    value: object,
    *,
    exists: Callable[[str], bool] = os.path.exists,
    is_directory: Callable[[str], bool] = os.path.isdir,
) -> ExplorerTarget:
    """Zbuduj cel Eksploratora i sprawdź go dopiero przy wykonaniu polecenia."""

    text = str(value or "").strip()
    if not looks_like_local_path(text):
        raise ShellPathError(NO_LOCAL_FILE_MESSAGE)
    normalized = ntpath.normpath(text)
    if not exists(normalized):
        raise ShellPathError(MISSING_LOCAL_FILE_MESSAGE)
    return ExplorerTarget(normalized, select_file=not is_directory(normalized))


def open_in_explorer(
    value: object,
    *,
    start: Callable[..., object] = subprocess.Popen,
) -> ExplorerTarget:
    """Otwórz folder lub zaznacz plik bez powłoki i bez składania komendy."""

    target = explorer_target(value)
    try:
        start(list(target.arguments), shell=False, close_fds=True)
    except OSError as error:
        raise ShellPathError(OPEN_LOCAL_FILE_ERROR_MESSAGE) from error
    return target
