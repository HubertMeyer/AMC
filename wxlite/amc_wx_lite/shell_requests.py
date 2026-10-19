"""Jednoliniowe żądania launchera AMC14, bez zależności od wx."""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass
from typing import Callable, TextIO


INVALID_REQUEST_MESSAGE = "Nie udało się odczytać polecenia otwarcia pliku"


class ShellRequestError(ValueError):
    """Odmowa o stałej, użytkowej treści bez ujawniania danych wejściowych."""


@dataclass(frozen=True, slots=True)
class ShellRequest:
    files: tuple[str, ...]
    add_to_queue: bool


def decode_request(line: str) -> ShellRequest:
    try:
        payload = json.loads(line)
    except (TypeError, ValueError) as error:
        raise ShellRequestError(INVALID_REQUEST_MESSAGE) from error
    if not isinstance(payload, dict) or payload.get("Schema") != 1:
        raise ShellRequestError(INVALID_REQUEST_MESSAGE)
    operation = payload.get("Operation")
    files = payload.get("Files")
    if operation not in ("open", "queue") or not isinstance(files, list):
        raise ShellRequestError(INVALID_REQUEST_MESSAGE)
    if not files or len(files) > 100 or any(
        not isinstance(path, str) or not path.strip() for path in files
    ):
        raise ShellRequestError(INVALID_REQUEST_MESSAGE)
    normalized = tuple(path.strip() for path in files)
    if operation == "open" and len(normalized) != 1:
        raise ShellRequestError(INVALID_REQUEST_MESSAGE)
    return ShellRequest(normalized, add_to_queue=operation == "queue")


def start_request_reader(
    dispatch: Callable[[ShellRequest], None],
    report_error: Callable[[str], None],
    *,
    schedule: Callable[[Callable[..., None], object], None],
    stream: TextIO | None = None,
) -> threading.Thread:
    """Czytaj kanał launchera w tle; wszystkie wywołania GUI planuj przez wx."""

    source = stream or sys.stdin

    def read() -> None:
        for line in source:
            if not line.strip():
                continue
            try:
                request = decode_request(line)
            except ShellRequestError as error:
                schedule(report_error, str(error))
            else:
                schedule(dispatch, request)

    thread = threading.Thread(
        target=read,
        name="AMC shell requests",
        daemon=True,
    )
    thread.start()
    return thread
