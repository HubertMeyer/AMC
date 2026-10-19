"""Lokalny, prywatnościowy fundament Sygnalisty AMC.

Moduł nie zna wx ani sieci. Ta sama zredagowana treść jest pokazywana w
podglądzie, kopiowana, zapisywana i — w przyszłości — przekazywana do
transportu. Dzięki temu przycisk nie może wysłać innej treści niż widział
użytkownik.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Protocol


MAX_TITLE_CHARACTERS = 200
MAX_DESCRIPTION_CHARACTERS = 20_000
MAX_STEPS_CHARACTERS = 10_000
MAX_LOG_LINES = 200
MAX_LOG_SOURCE_BYTES = 512 * 1024
MAX_LOG_CHARACTERS = 64 * 1024
MAX_REPORT_BYTES = 256 * 1024


class ReportKind(str, Enum):
    BUG = "bug"
    SUGGESTION = "suggestion"


REPORT_KIND_LABELS = {
    ReportKind.BUG: "Błąd",
    ReportKind.SUGGESTION: "Sugestia",
}


@dataclass(frozen=True, slots=True)
class ReportDraft:
    kind: ReportKind
    title: str
    description: str
    reproduction_steps: str = ""
    include_log: bool = False


@dataclass(frozen=True, slots=True)
class ReportEnvironment:
    application_name: str
    version: str
    build: str
    channel: str
    operating_system: str
    active_session: str
    components: str


@dataclass(frozen=True, slots=True)
class PreparedReport:
    title: str
    body: str
    included_log: bool

    @property
    def utf8_size(self) -> int:
        return len(self.body.encode("utf-8", errors="strict"))


class DeliveryStatus(str, Enum):
    SUCCESS = "success"
    NOT_CONFIGURED = "not-configured"
    OFFLINE = "offline"
    RATE_LIMITED = "rate-limited"
    TOO_LARGE = "too-large"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    status: DeliveryStatus
    issue_number: int | None = None
    issue_url: str | None = None

    @property
    def user_message(self) -> str:
        if self.status is DeliveryStatus.SUCCESS:
            suffix = (
                f" Numer zgłoszenia: {self.issue_number}."
                if self.issue_number is not None
                else ""
            )
            return "Zgłoszenie zostało wysłane." + suffix
        if self.status is DeliveryStatus.NOT_CONFIGURED:
            return (
                "Wysyłanie zgłoszeń nie jest jeszcze skonfigurowane. "
                "Skopiuj raport albo zapisz go do pliku."
            )
        if self.status is DeliveryStatus.OFFLINE:
            return "Brak połączenia z serwerem zgłoszeń. Raport nie został wysłany."
        if self.status is DeliveryStatus.RATE_LIMITED:
            return "Serwer ograniczył liczbę zgłoszeń. Spróbuj później."
        if self.status is DeliveryStatus.TOO_LARGE:
            return "Raport jest zbyt duży, aby go wysłać. Usuń log i spróbuj ponownie."
        return "Nie udało się wysłać zgłoszenia. Raport nie został utracony."


class ReportTransport(Protocol):
    def send(self, report: PreparedReport) -> DeliveryResult:
        """Wyślij dokładnie zredagowany raport widoczny w podglądzie."""


class LocalOnlyTransport:
    """Uczciwy transport przed wdrożeniem Workera: nigdy nie używa sieci."""

    def send(self, report: PreparedReport) -> DeliveryResult:
        del report
        return DeliveryResult(DeliveryStatus.NOT_CONFIGURED)


_WINDOWS_PATH = re.compile(
    r"(?i)(?<![\w])(?:[a-z]:[\\/]|\\\\)[^\r\n\t\"<>|]+"
)
_FILE_URI = re.compile(r"(?i)\bfile:///[^\s\"<>]+")
_WEB_ADDRESS = re.compile(r"(?i)\b(?:https?|rtsp|mms)://[^\s\"<>]+")
_EMAIL = re.compile(r"(?i)\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
_IPV4 = re.compile(
    r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)"
)
_MAC = re.compile(r"(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b")
_GUID = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
)
_AUTHORIZATION_HEADER = re.compile(
    r"(?im)\b(authorization|proxy-authorization|cookie|set-cookie)\s*:\s*[^\r\n]*"
)
_BEARER_VALUE = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?P<quote>[\"']?)(?P<key>access[_ -]?token|refresh[_ -]?token|"
    r"client[_ -]?secret|api[_ -]?key|password|passwd|account(?:[_ -]?name)?|"
    r"user(?:[_ -]?name)?|display[_ -]?name)(?P=quote)"
    r"\s*[:=]\s*(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\r\n]*)"
)
_JWT = re.compile(r"\beyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{10,}(?:\.[a-zA-Z0-9_-]{10,})?\b")
_LONG_OPAQUE = re.compile(r"(?<![a-zA-Z0-9_-])[a-zA-Z0-9_-]{64,}(?![a-zA-Z0-9_-])")
_PRIVATE_FILENAME = re.compile(
    r"(?i)(?<![\w.-])[^\s\\/:*?\"<>|]{1,180}\."
    r"(?:mp3|m4a|aac|flac|wav|ogg|opus|wma|mp4|mkv|avi|mov|webm|"
    r"m3u8?|pls|asx|xspf|json|db|sqlite|log|txt)(?![\w.-])"
)


def redact_private_data(value: str) -> str:
    """Usuń prywatne dane, zachowując czytelną strukturę diagnostyczną."""

    text = str(value or "").replace("\x00", "")
    text = _FILE_URI.sub("[ścieżka prywatna]", text)
    text = _WINDOWS_PATH.sub("[ścieżka prywatna]", text)
    text = _WEB_ADDRESS.sub("[adres usunięty]", text)
    text = _EMAIL.sub("[adres e-mail usunięty]", text)
    text = _MAC.sub("[adres urządzenia usunięty]", text)
    text = _IPV4.sub("[adres sieciowy usunięty]", text)
    text = _GUID.sub("[identyfikator usunięty]", text)
    text = _AUTHORIZATION_HEADER.sub(
        lambda match: f"{match.group(1)}: [wartość usunięta]",
        text,
    )
    text = _BEARER_VALUE.sub("Bearer [wartość usunięta]", text)
    text = _SECRET_ASSIGNMENT.sub(
        lambda match: f"{match.group('key')}: [wartość usunięta]",
        text,
    )
    text = _JWT.sub("[token usunięty]", text)
    text = _LONG_OPAQUE.sub("[wartość poufna usunięta]", text)
    text = _PRIVATE_FILENAME.sub("[nazwa pliku usunięta]", text)
    return text


def _limited(value: str, maximum: int) -> str:
    text = str(value or "").strip()
    if len(text) <= maximum:
        return text
    return text[:maximum].rstrip() + "\n[treść skrócona przed przygotowaniem raportu]"


def read_log_tail(path: str | Path | None) -> tuple[str, ...]:
    """Czytaj ograniczony ogon logu; nigdy cały wielomegabajtowy plik."""

    if path is None:
        return ()
    source = Path(path)
    try:
        size = source.stat().st_size
        with source.open("rb") as stream:
            offset = max(0, size - MAX_LOG_SOURCE_BYTES)
            stream.seek(offset)
            raw = stream.read(MAX_LOG_SOURCE_BYTES)
    except OSError:
        return ()

    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if offset > 0 and lines:
        lines = lines[1:]
    tail: deque[str] = deque(maxlen=MAX_LOG_LINES)
    characters = 0
    for line in reversed(lines):
        safe = redact_private_data(line)
        cost = len(safe) + 1
        if characters + cost > MAX_LOG_CHARACTERS:
            break
        tail.appendleft(safe)
        characters += cost
        if len(tail) >= MAX_LOG_LINES:
            break
    return tuple(tail)


def prepare_report(
    draft: ReportDraft,
    environment: ReportEnvironment,
    *,
    log_lines: tuple[str, ...] | list[str] = (),
) -> PreparedReport:
    """Zbuduj dokładnie tę treść, którą można potem skopiować lub zapisać."""

    kind = REPORT_KIND_LABELS.get(draft.kind, REPORT_KIND_LABELS[ReportKind.BUG])
    title_text = redact_private_data(_limited(draft.title, MAX_TITLE_CHARACTERS))
    title_text = title_text or "Bez tytułu"
    description = redact_private_data(
        _limited(draft.description, MAX_DESCRIPTION_CHARACTERS)
    ) or "Nie wpisano opisu."
    steps = redact_private_data(
        _limited(draft.reproduction_steps, MAX_STEPS_CHARACTERS)
    )

    sections = [
        "Raport AMC",
        "",
        f"Rodzaj: {kind}",
        f"Tytuł: {title_text}",
        "",
        "Opis:",
        description,
    ]
    if steps:
        sections.extend(("", "Kroki odtworzenia:", steps))

    included_log = bool(draft.include_log and log_lines)
    if included_log:
        safe_lines = [redact_private_data(line) for line in log_lines[-MAX_LOG_LINES:]]
        log_text = "\n".join(safe_lines)
        if len(log_text) > MAX_LOG_CHARACTERS:
            log_text = log_text[-MAX_LOG_CHARACTERS:]
            log_text = "[początek logu pominięty]\n" + log_text
        sections.extend(("", "Dziennik diagnostyczny po redakcji:", log_text))

    sections.extend((
        "",
        "Dane techniczne:",
        f"Program: {redact_private_data(environment.application_name)}",
        f"Wersja: {redact_private_data(environment.version)}",
        f"Kompilacja: {redact_private_data(environment.build) or 'brak etykiety'}",
        f"Kanał: {redact_private_data(environment.channel)}",
        f"System: {redact_private_data(environment.operating_system)}",
        f"Sesja: {redact_private_data(environment.active_session)}",
        f"Składniki: {redact_private_data(environment.components)}",
        "Log dołączony: " + ("tak, po redakcji" if included_log else "nie"),
    ))

    body = "\n".join(sections).rstrip() + "\n"
    body = redact_private_data(body)
    return PreparedReport(f"[{kind}] {title_text}", body, included_log)


def deliver_report(
    transport: ReportTransport,
    report: PreparedReport,
) -> DeliveryResult:
    """Jedna brama przyszłej wysyłki, z uczciwymi wynikami bez wyjątków UI."""

    if report.utf8_size > MAX_REPORT_BYTES:
        return DeliveryResult(DeliveryStatus.TOO_LARGE)
    try:
        result = transport.send(report)
    except (ConnectionError, TimeoutError, OSError):
        return DeliveryResult(DeliveryStatus.OFFLINE)
    except Exception:
        return DeliveryResult(DeliveryStatus.FAILED)
    return result if isinstance(result, DeliveryResult) else DeliveryResult(
        DeliveryStatus.FAILED
    )


def report_file_name(moment: datetime | None = None) -> str:
    stamp = moment or datetime.now().astimezone()
    return stamp.strftime("zgloszenie-%Y%m%d-%H%M%S.txt")


def save_report_atomic(
    report: PreparedReport,
    directory: str | Path,
    *,
    moment: datetime | None = None,
) -> Path:
    """Zapisz zredagowany podgląd atomowo w magazynie bieżącego profilu."""

    target_directory = Path(directory)
    target_directory.mkdir(parents=True, exist_ok=True)
    target = target_directory / report_file_name(moment)
    handle, temporary = tempfile.mkstemp(
        dir=str(target_directory), prefix=".zgloszenie-", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(report.body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return target
