#!/usr/bin/env python3
"""Inventory and optionally translate hard-coded AMC wxPython UI text.

Only source literals that are passed to known user-facing wxPython surfaces
are collected.  Runtime values (account names, paths, stations, devices,
titles, URLs, and profile data) are never read or sent to a translation
service.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import string
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parent
PACKAGE = ROOT / "amc_wx_lite"
DEFAULT_OUTPUT = PACKAGE / "locales" / "en_legacy.json"
DEFAULT_CACHE = REPOSITORY / ".test-output" / "google-translation-cache.json"
sys.path.insert(0, str(ROOT))


# Methods and small helpers whose arguments are intentional user-facing text.
# The tuple gives zero-based positional arguments.  ``None`` means every
# positional argument except the wx parent/control in position zero.
_POSITIONAL_ARGUMENTS: dict[str, tuple[int, ...] | None] = {
    "AddPage": (1,),
    "AppendCheckItem": (1, 2),
    "AppendRadioItem": (1, 2),
    "MessageBox": (0, 1),
    "SetHelpText": (0,),
    "SetLabel": (0,),
    "SetName": (0,),
    "SetStatusText": (0,),
    "SetTitle": (0,),
    "SetToolTip": (0,),
    "SetToolTipText": (0,),
    "_announce_after_list_update": (0,),
    "_announce_after_native_list_update": (0,),
    "_announce_routine_text": (0,),
    "_announce_transient_preview": (0,),
    "_set_status": (0,),
    "announce_status": (1,),
    "say": (0,),
    "show": (0,),
    "ui_text": (0,),
}

_WIDGET_CALLS = {
    "Button",
    "CheckBox",
    "Choice",
    "ComboBox",
    "Dialog",
    "Frame",
    "ListBox",
    "MenuItem",
    "RadioBox",
    "RadioButton",
    "StaticBox",
    "StaticText",
    "TextCtrl",
    "TextEntryDialog",
    "ToggleButton",
}

_TEXT_KEYWORDS = {
    "caption",
    "choices",
    "description",
    "help",
    "helpString",
    "label",
    "message",
    "title",
    "value",
}

_TEXT_NAME_SUFFIXES = (
    "_CAPTION",
    "_DESCRIPTION",
    "_GUIDANCE",
    "_HELP",
    "_LABEL",
    "_LABELS",
    "_MESSAGE",
    "_STATUS",
    "_TEXT",
    "_TITLE",
)

_INTERNAL_TOKEN = re.compile(r"^[a-z][a-z0-9_.:-]+$")
_URL_OR_PATH = re.compile(
    r"^(?:[a-z][a-z0-9+.-]*://|[a-z]:[\\/]|\\\\|\.\.?[\\/])",
    re.IGNORECASE,
)
_PERCENT_PLACEHOLDER = re.compile(
    r"%(?:\([^)]+\))?[#0 +\-]?(?:\d+|\*)?(?:\.\d+|\.\*)?[hlL]?[diouxXeEfFgGcrs%]"
)
_PLACEHOLDER = re.compile(r"\{(arg\d+)\}")

# Machine translation is only a draft.  These reviewed overrides protect the
# accessibility vocabulary where Polish words have several unrelated English
# meanings (for example ``zakładka`` = bookmark here, never a notebook tab).
_MANUAL_TRANSLATION_OVERRIDES = {
    "zaplanowane ": "scheduled ",
    "stacja": "station",
    "&Sposób zapisu:": "&Saving method:",
    "Bieżący stan konta i krótka instrukcja. Pole tylko do odczytu; użyj strzałek do czytania, a Tab przechodzi do czynności.": (
        "Current account status and brief instructions. This field is read-only; "
        "use the arrow keys to read it, and Tab moves to the actions."
    ),
    "Dla jednego działania wybierz wyniki z tej samej usługi": (
        "For one action, select results from the same service"
    ),
    "Dołącz ostatnie wpisy dziennika po automatycznej redakcji": (
        "Include recent log entries after automatic redaction"
    ),
    "Góra i dół wybierają plan. Lewo powtarza stan i termin, prawo czyta ustawienia pliku. Enter edytuje, Spacja włącza lub wyłącza.": (
        "Up and Down select a schedule. Left repeats its status and time, and "
        "Right reads the file settings. Enter edits; Space enables or disables."
    ),
    "Historia nie zawiera elementu, który można ponownie odtworzyć": (
        "Playback history does not contain an item that can be played again"
    ),
    "Nagranie jest już zatrzymywane": "The recording is already being stopped",
    "Nagranie jeszcze się uruchamia": "The recording is still starting",
    "Nawigacja po historii działa w odtwarzaczu": (
        "History navigation is available in the player"
    ),
    "Nawigacja po zakładkach jest dostępna dla plików lokalnych, podcastów i Spotify": (
        "Bookmark navigation is available for local files, podcasts, and Spotify"
    ),
    "Nazwa zakładki nie może być pusta": "The bookmark name cannot be empty",
    "Nie można dodać zakładki do bieżącego materiału": (
        "Cannot add a bookmark to the current item"
    ),
    "Nie można teraz odczytać stanu konta Sonos.": (
        "The Sonos account status cannot be read right now."
    ),
    "Nie można teraz odczytać stanu konta YouTube.": (
        "The YouTube account status cannot be read right now."
    ),
    "Nie udało się bezpiecznie zaktualizować składników. Szczegóły zapisano w dzienniku AMC": (
        "The components could not be updated safely. Details were saved in the AMC log"
    ),
    "Odtwarzanie działa, ale nie udało się zapisać pozycji w Historii odtwarzania": (
        "Playback is working, but the item could not be saved in Playback history"
    ),
    "Rozdziały bieżącego materiału": "Chapters in the current item",
    "Silnik nie działa, nawigacja po zakładkach jest niedostępna": (
        "The engine is not running; bookmark navigation is unavailable"
    ),
    "Ten materiał nie ma rozdziałów": "This item has no chapters",
    "Wynik zmiany harmonogramu": "Recording schedule change result",
    "Wyłączono oznajmianie rozpoznanych utworów. Obserwowanie nadal działa, a wyniki trafiają do historii": (
        "Recognized-track announcements are off. Monitoring is still active, and "
        "the results are added to history"
    ),
    "Zakładki bez zmian": "Bookmarks unchanged",
    "Zamknij historię": "Close history",
    "Zapis wideo jako jest dostępny tylko dla jednego materiału YouTube": (
        "Save video as is available for one YouTube video at a time"
    ),
    "Zapisz jako działa dla jednego materiału": (
        "Save as is available for one item at a time"
    ),
    "Dodano zakładkę {arg0}: {arg1}": "Added bookmark {arg0}: {arg1}",
    "Dodano zakładkę: {arg0}": "Added bookmark: {arg0}",
    "Materiał jest już w Bibliotece, Media internetowe: {arg0}": (
        "This item is already in the Library under Online media: {arg0}"
    ),
    "Nadano nazwę zakładce {arg0}: {arg1}": (
        "Named bookmark {arg0}: {arg1}"
    ),
    "Nie można przejść do zakładki: {arg0}": (
        "Cannot go to the bookmark: {arg0}"
    ),
    "Nie można teraz odczytać stanu konta {arg0}.": (
        "The {arg0} account status cannot be read right now."
    ),
    "Nie udało się zmienić losowania urządzenia {arg0}: {arg1}": (
        "Failed to change shuffle on device {arg0}: {arg1}"
    ),
    "Preset {arg0} istnieje, ale ten rodzaj materiału nie jest jeszcze przeniesiony.": (
        "Preset {arg0} exists, but this type of content has not been migrated yet."
    ),
    "Preset {arg0} ma nieobsługiwany rodzaj materiału Sonos": (
        "Preset {arg0} contains an unsupported type of Sonos content"
    ),
    "Preset {arg0} zapisano dla innego domu Sonos. Przypisz go ponownie w tym domu. Nic nie uruchomiłem": (
        "Preset {arg0} was saved for another Sonos household. Assign it again "
        "in this household. Nothing was started"
    ),
    "Rozpoczęto zapisywanie fragmentu: {arg0}": (
        "Saving the clip started: {arg0}"
    ),
    "Stan konta YouTube: {arg0}": "YouTube account status: {arg0}",
    "Stan konta {arg0}: {arg1}": "{arg0} account status: {arg1}",
    "Zakładka {arg0} już istnieje: {arg1}": (
        "Bookmark {arg0} already exists: {arg1}"
    ),
    "Zaloguj się zwykłym kontem na oficjalnej stronie {arg0}. Hasło wpisujesz wyłącznie w przeglądarce. AMC nie wymaga przepisywania kodu.": (
        "Sign in with a regular account on the official {arg0} website. Enter "
        "your password only in the browser. AMC does not ask you to type a code."
    ),
    "Wybrano kanałów: {arg0} z {arg1}": (
        "Selected channels: {arg0} of {arg1}"
    ),
    "Zakończono {arg0}nagrywanie {arg1}. Zapisano plików: {arg2}": (
        "Finished {arg0}recording of {arg1}. Files saved: {arg2}"
    ),
    "Zakończono {arg0}nagrywanie {arg1}: {arg2}": (
        "Finished {arg0}recording of {arg1}: {arg2}"
    ),
    "Zakończono {arg0}nagrywanie: {arg1}": (
        "Finished {arg0}recording: {arg1}"
    ),
    "Przygotowano nową playlistę {arg0}, {arg1}, zaznaczoną. Naciśnij Enter, aby ją utworzyć i dodać wybrane elementy": (
        "New playlist {arg0}, {arg1}, selected. Press Enter to create it and add "
        "the selected items"
    ),
    "Wpisz adres kanału RSS lub Atom, publicznego profilu SoundCloud, kanału albo playlisty YouTube lub pojedynczego publicznego materiału YouTube. Profil SoundCloud zostanie zapisany jako podcast z odtwarzalnymi i możliwymi do pobrania plikami audio. Adres profilu może mieć postać https://soundcloud.com/NazwaProfilu, a kanału YouTube https://www.youtube.com/@NazwaKanału.": (
        "Enter an RSS or Atom feed, public SoundCloud profile, YouTube channel "
        "or playlist, or one public YouTube video. A SoundCloud profile is saved "
        "as a podcast with playable and downloadable audio files. A profile URL "
        "can look like https://soundcloud.com/ProfileName, and a YouTube channel "
        "URL like https://www.youtube.com/@ChannelName."
    ),
}


@dataclass(frozen=True)
class Inventory:
    exact: frozenset[str]
    templates: frozenset[str]
    occurrences: tuple[dict[str, object], ...]


def default_source_paths() -> tuple[Path, ...]:
    """Return every wxPython UI module without treating non-UI code as text."""

    sources: list[Path] = []
    for path in sorted(PACKAGE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "import wx" in source or "from wx" in source:
            sources.append(path)
    return tuple(sources)


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _render_text(node: ast.AST, counter: list[int]) -> tuple[str, bool] | None:
    """Render a source literal as exact text or a stable ``{argN}`` template."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, False
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        dynamic = False
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                parts.append(f"{{arg{counter[0]}}}")
                counter[0] += 1
                dynamic = True
            else:
                return None
        return "".join(parts), dynamic
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _render_text(node.left, counter)
        right = _render_text(node.right, counter)
        if left is None or right is None:
            return None
        return left[0] + right[0], left[1] or right[1]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        left = _render_text(node.left, counter)
        if left is None:
            return None

        def replacement(match: re.Match[str]) -> str:
            if match.group(0) == "%%":
                return "%"
            marker = f"{{arg{counter[0]}}}"
            counter[0] += 1
            return marker

        rendered = _PERCENT_PLACEHOLDER.sub(replacement, left[0])
        return rendered, rendered != left[0] or left[1]
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
    ):
        base = _render_text(node.func.value, counter)
        if base is None:
            return None
        parts: list[str] = []
        dynamic = base[1]
        try:
            parsed = string.Formatter().parse(base[0])
            for literal, field, _format_spec, _conversion in parsed:
                parts.append(literal)
                if field is not None:
                    parts.append(f"{{arg{counter[0]}}}")
                    counter[0] += 1
                    dynamic = True
        except ValueError:
            return None
        return "".join(parts), dynamic
    return None


def _is_catalog_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) <= 1:
        return False
    if _URL_OR_PATH.match(stripped):
        return False
    if _INTERNAL_TOKEN.fullmatch(stripped) and not any(
        character in stripped for character in "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"
    ):
        return False
    if not any(character.isalpha() for character in stripped):
        return False
    return True


def _values_from_node(
    node: ast.AST,
    resolve_name,
    seen: frozenset[int] = frozenset(),
) -> Iterable[ast.AST]:
    if id(node) in seen:
        return
    seen = seen | {id(node)}
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for item in node.elts:
            yield from _values_from_node(item, resolve_name, seen)
        return
    if isinstance(node, ast.Dict):
        for value in node.values:
            yield from _values_from_node(value, resolve_name, seen)
        return
    if isinstance(node, ast.Name):
        resolved = tuple(resolve_name(node.id, int(getattr(node, "lineno", 0))))
        if resolved:
            for value in resolved:
                yield from _values_from_node(value, resolve_name, seen)
            return
    if isinstance(node, ast.Attribute):
        resolved = tuple(resolve_name(node.attr, int(getattr(node, "lineno", 0))))
        if resolved:
            for value in resolved:
                yield from _values_from_node(value, resolve_name, seen)
            return
    yield node


def _scope_tables(tree: ast.AST) -> tuple[
    dict[int, ast.AST],
    dict[int, dict[str, list[tuple[int, ast.AST]]]],
    dict[int, ast.AST | None],
]:
    scope_for_node: dict[int, ast.AST] = {}
    assignments: dict[int, dict[str, list[tuple[int, ast.AST]]]] = {id(tree): {}}
    parent_scope: dict[int, ast.AST | None] = {id(tree): None}

    def walk(node: ast.AST, scope: ast.AST) -> None:
        scope_for_node[id(node)] = scope
        child_scope = scope
        if isinstance(
            node,
            (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
        ):
            child_scope = node
            parent_scope[id(child_scope)] = scope
            assignments.setdefault(id(child_scope), {})
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            table = assignments.setdefault(id(scope), {})
            for target in targets:
                if isinstance(target, ast.Name):
                    table.setdefault(target.id, []).append(
                        (int(getattr(node, "lineno", 0)), value)
                    )
        for child in ast.iter_child_nodes(node):
            walk(child, child_scope)

    walk(tree, tree)
    return scope_for_node, assignments, parent_scope


def inventory_file(path: Path) -> Inventory:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    scope_for_node, assignments, parent_scope = _scope_tables(tree)

    exact: set[str] = set()
    templates: set[str] = set()
    occurrences: list[dict[str, object]] = []

    def add(node: ast.AST, call: str, scope: ast.AST) -> None:
        def resolve_name(name: str, line: int) -> Iterable[ast.AST]:
            current: ast.AST | None = scope
            while current is not None:
                candidates = [
                    value
                    for assigned_line, value in assignments.get(id(current), {}).get(name, ())
                    if assigned_line <= line
                ]
                if candidates:
                    yield from candidates
                    return
                current = parent_scope.get(id(current))

        for value in _values_from_node(node, resolve_name):
            rendered = _render_text(value, [0])
            if rendered is None:
                continue
            text, is_template = rendered
            if not _is_catalog_text(text):
                continue
            target = templates if is_template else exact
            target.add(text)
            occurrences.append(
                {
                    "call": call,
                    "line": int(getattr(value, "lineno", getattr(node, "lineno", 0))),
                    "template": is_template,
                    "text": text,
                }
            )
            # A formatted expression can itself contain a fixed user-facing
            # choice, for example ``'zaplanowane ' if scheduled else ''``.
            # Catalog that fixed part as well; runtime profile values are not
            # inspected and remain untouched.
            def embedded_literals(
                expression: ast.AST,
                seen: frozenset[int] = frozenset(),
            ) -> Iterable[ast.Constant]:
                if id(expression) in seen:
                    return
                seen = seen | {id(expression)}
                if isinstance(expression, ast.Constant):
                    if isinstance(expression.value, str):
                        yield expression
                    return
                if isinstance(expression, ast.IfExp):
                    yield from embedded_literals(expression.body, seen)
                    yield from embedded_literals(expression.orelse, seen)
                    return
                if isinstance(expression, ast.BoolOp):
                    for choice in expression.values:
                        yield from embedded_literals(choice, seen)
                    return
                if isinstance(expression, ast.Name):
                    for resolved in resolve_name(
                        expression.id,
                        int(getattr(expression, "lineno", 0)),
                    ):
                        yield from embedded_literals(resolved, seen)
                    return

            for formatted in ast.walk(value):
                if not isinstance(formatted, ast.FormattedValue):
                    continue
                for embedded in embedded_literals(formatted.value):
                    embedded_text = embedded.value
                    if not (
                        isinstance(embedded_text, str)
                        and len(embedded_text.strip()) > 1
                        and any(character.isalpha() for character in embedded_text)
                        and not _URL_OR_PATH.match(embedded_text.strip())
                    ):
                        continue
                    exact.add(embedded_text)
                    occurrences.append(
                        {
                            "call": call + ".embedded",
                            "line": int(getattr(embedded, "lineno", 0)),
                            "template": False,
                            "text": embedded_text,
                        }
                    )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        scope = scope_for_node[id(node)]
        positions = _POSITIONAL_ARGUMENTS.get(name)
        if positions is None and name not in _POSITIONAL_ARGUMENTS:
            if name in _WIDGET_CALLS or name.endswith("Dialog"):
                positions = tuple(range(1, len(node.args)))
            else:
                positions = ()
        elif positions is None:
            positions = tuple(range(1, len(node.args)))
        for position in positions:
            if 0 <= position < len(node.args):
                add(node.args[position], name, scope)
        if name in _WIDGET_CALLS or name.endswith("Dialog") or name in _POSITIONAL_ARGUMENTS:
            for keyword in node.keywords:
                if keyword.arg in _TEXT_KEYWORDS:
                    add(keyword.value, name, scope)

    # Constants such as login guidance are often assigned once and later
    # combined with a runtime status.  Their semantic name makes them an
    # intentional UI source even when the call receives only a variable.
    for table in assignments.values():
        for name, values in table.items():
            if name.isupper() and name.endswith(_TEXT_NAME_SUFFIXES):
                for _line, value in values:
                    scope = scope_for_node.get(id(value), tree)
                    add(value, name, scope)

    return Inventory(
        exact=frozenset(exact),
        templates=frozenset(templates),
        occurrences=tuple(
            sorted(
                occurrences,
                key=lambda item: (int(item["line"]), str(item["call"]), str(item["text"])),
            )
        ),
    )


def inventory_files(paths: Iterable[Path]) -> Inventory:
    exact: set[str] = set()
    templates: set[str] = set()
    occurrences: list[dict[str, object]] = []
    for path in paths:
        current = inventory_file(path)
        exact.update(current.exact)
        templates.update(current.templates)
        relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
        for item in current.occurrences:
            occurrences.append({"file": relative, **item})
    return Inventory(
        exact=frozenset(exact),
        templates=frozenset(templates),
        occurrences=tuple(
            sorted(
                occurrences,
                key=lambda item: (
                    str(item["file"]),
                    int(item["line"]),
                    str(item["call"]),
                    str(item["text"]),
                ),
            )
        ),
    )


def _google_translate(text: str, *, timeout: float = 45.0) -> str:
    # Imported only in the isolated translation-tools environment.  It is not
    # a runtime dependency of AMC or its packaged application.
    import requests  # type: ignore[import-not-found]

    response = None
    for attempt in range(5):
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "pl",
                "tl": "en",
                "dt": "t",
                "q": text,
            },
            timeout=timeout,
        )
        if response.status_code != 429 and response.status_code < 500:
            break
        time.sleep(2 ** attempt)
    assert response is not None
    response.raise_for_status()
    payload = response.json()
    return "".join(part[0] for part in payload[0] if part and part[0])


def _protect_placeholders(text: str) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        placeholder = "{" + match.group(1) + "}"
        marker = f"[[ZXQAMCARG{len(replacements):03d}QXZ]]"
        replacements[marker] = placeholder
        return marker

    return _PLACEHOLDER.sub(replace, text), replacements


def _restore_placeholders(text: str, replacements: dict[str, str]) -> str:
    result = text
    for marker, placeholder in replacements.items():
        if result.count(marker) != 1:
            raise ValueError(f"Translation did not preserve placeholder marker {marker}")
        result = result.replace(marker, placeholder)
    return result


def _normalize_product_names(text: str) -> str:
    replacements = {
        "Ffmpeg": "FFmpeg",
        "Tidal": "TIDAL",
        "Wiim": "WiiM",
        "Youtube": "YouTube",
        "Yt-Dlp": "yt-dlp",
        "Yt-dlp": "yt-dlp",
    }
    result = text
    for source, target in replacements.items():
        result = result.replace(source, target)
    return result


def translate_many(
    texts: Iterable[str],
    *,
    chunk_limit: int = 2800,
    cache_path: Path = DEFAULT_CACHE,
) -> dict[str, str]:
    """Translate source literals in auditable chunks with stable separators."""

    ordered = sorted(set(texts))
    translated: dict[str, str] = {}
    if cache_path.is_file():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(cached, dict):
            translated.update(
                {
                    str(source): str(target)
                    for source, target in cached.items()
                    if source in ordered and isinstance(target, str) and target
                }
            )
    ordered = [source for source in ordered if source not in translated]
    index = 0
    request_number = 0
    while index < len(ordered):
        items: list[tuple[str, str, dict[str, str]]] = []
        size = 0
        while index < len(ordered):
            source = ordered[index]
            protected, placeholders = _protect_placeholders(source)
            separator_size = 32 if items else 0
            if items and size + separator_size + len(protected) > chunk_limit:
                break
            items.append((source, protected, placeholders))
            size += separator_size + len(protected)
            index += 1

        separators = [
            f"ZXQAMCSEP{request_number:03d}{item_index:04d}QXZ"
            for item_index in range(max(0, len(items) - 1))
        ]
        parts: list[str] = []
        for item_index, (_source, protected, _placeholders) in enumerate(items):
            if item_index:
                parts.append("\n" + separators[item_index - 1] + "\n")
            parts.append(protected)
        response = _google_translate("".join(parts))
        for separator in separators:
            if response.count(separator) != 1:
                raise ValueError(f"Translation did not preserve separator {separator}")
        outputs = re.split(
            "(?:\\r?\\n)?(?:" + "|".join(map(re.escape, separators)) + ")(?:\\r?\\n)?",
            response,
        ) if separators else [response]
        if len(outputs) != len(items):
            raise ValueError("Translation response item count does not match request")
        for (source, protected, placeholders), output in zip(items, outputs, strict=True):
            try:
                restored = _restore_placeholders(output.strip(), placeholders)
            except ValueError:
                individual = _google_translate(protected)
                try:
                    restored = _restore_placeholders(individual.strip(), placeholders)
                except ValueError as error:
                    raise ValueError(
                        f"Translation did not preserve placeholders for {source!r}; "
                        f"received {individual!r}"
                    ) from error
            translated[source] = _normalize_product_names(restored)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(translated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        request_number += 1
        if index < len(ordered):
            time.sleep(0.8)
    return translated


def _placeholder_names(text: str) -> set[str]:
    return set(_PLACEHOLDER.findall(text))


def build_catalog(
    inventory: Inventory,
    *,
    translate: bool,
    source_paths: Iterable[Path],
) -> dict[str, object]:
    from amc_wx_lite import i18n

    curated = set(i18n._UI_TEXT_EN)  # noqa: SLF001 - intentional tooling API
    exact_sources = sorted(inventory.exact - curated)
    template_sources = sorted(inventory.templates)
    if translate:
        result = translate_many([*exact_sources, *template_sources])
    else:
        result = {source: "" for source in [*exact_sources, *template_sources]}
    for source, target in _MANUAL_TRANSLATION_OVERRIDES.items():
        if source in result:
            result[source] = target
    static = {source: result[source] for source in exact_sources}
    templates = {source: result[source] for source in template_sources}
    for source, target in templates.items():
        if target and _placeholder_names(source) != _placeholder_names(target):
            raise ValueError(f"Placeholder mismatch for {source!r}: {target!r}")
    fingerprint = hashlib.sha256(
        "\0".join([*sorted(inventory.exact), *sorted(inventory.templates)]).encode("utf-8")
    ).hexdigest()
    return {
        "_meta": {
            "language": "en",
            "sourceLanguage": "pl",
            "source": [
                path.resolve().relative_to(ROOT.resolve()).as_posix()
                for path in source_paths
            ],
            "sourceFingerprintSha256": fingerprint,
            "generatedAtUtc": datetime.now(UTC).isoformat(timespec="seconds"),
            "machineTranslationProvider": (
                "Google Translate public web endpoint; manually review before release"
                if translate
                else None
            ),
            "privacy": "No runtime, profile, account, path, title, station, or device data",
        },
        "static": static,
        "templates": templates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, action="append")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--translate-google",
        action="store_true",
        help="Send only collected source literals to Google Translate.",
    )
    parser.add_argument("--inventory-json", type=Path)
    args = parser.parse_args()

    source_paths = tuple(
        path.resolve() for path in (args.source or default_source_paths())
    )
    inventory = inventory_files(source_paths)
    catalog = build_catalog(
        inventory,
        translate=args.translate_google,
        source_paths=source_paths,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.inventory_json:
        args.inventory_json.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_json.write_text(
            json.dumps(
                {
                    "exact": sorted(inventory.exact),
                    "templates": sorted(inventory.templates),
                    "occurrences": inventory.occurrences,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(
        f"exact={len(inventory.exact)} templates={len(inventory.templates)} "
        f"catalog_static={len(catalog['static'])} "
        f"catalog_templates={len(catalog['templates'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
