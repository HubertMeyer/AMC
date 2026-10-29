"""Bezsekretowy transport HTTPS dla internetowego Sygnalisty AMC."""

from __future__ import annotations

import json
import os
import socket
import uuid
from pathlib import Path
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .problem_report import (
    DeliveryResult,
    DeliveryStatus,
    LocalOnlyTransport,
    PreparedReport,
)


ENDPOINT_ENVIRONMENT_VARIABLE = "AMC_PROBLEM_REPORT_ENDPOINT"
ENDPOINT_RESOURCE_NAME = "problem-report-endpoint.txt"
MAX_RESPONSE_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 15.0


def _validated_https_endpoint(value: object) -> str | None:
    candidate = str(value or "").strip()
    if not candidate or len(candidate) > 2048 or "\n" in candidate or "\r" in candidate:
        return None
    parsed = urlsplit(candidate)
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return None
    return candidate


class HttpReportTransport:
    """Wysyła wyłącznie zredagowaną treść, bez tokenu i bez automatycznych prób."""

    def __init__(
        self,
        endpoint: str,
        *,
        opener: Callable[..., object] = urlopen,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        validated = _validated_https_endpoint(endpoint)
        if validated is None:
            raise ValueError("Endpoint Sygnalisty musi być prawidłowym adresem HTTPS")
        self.endpoint = validated
        self._opener = opener
        self._timeout = max(1.0, min(float(timeout), 60.0))

    def send(self, report: PreparedReport) -> DeliveryResult:
        try:
            uuid.UUID(report.report_id)
        except (ValueError, AttributeError, TypeError):
            return DeliveryResult(DeliveryStatus.FAILED)
        payload = {
            "schemaVersion": 1,
            "reportId": report.report_id,
            "kind": report.kind.value,
            "title": report.title,
            "reportText": report.body,
            "includedLog": report.included_log,
            "channel": report.channel,
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "AMC-Problem-Reporter/1",
            },
            method="POST",
        )
        try:
            response = self._opener(request, timeout=self._timeout)
            with response:
                status = int(getattr(response, "status", 0) or response.getcode())
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            if error.code == 413:
                return DeliveryResult(DeliveryStatus.TOO_LARGE)
            if error.code == 429:
                return DeliveryResult(DeliveryStatus.RATE_LIMITED)
            if error.code in (408, 502, 503, 504):
                return DeliveryResult(DeliveryStatus.OFFLINE)
            return DeliveryResult(DeliveryStatus.FAILED)
        except (URLError, TimeoutError, socket.timeout, OSError):
            return DeliveryResult(DeliveryStatus.OFFLINE)

        if status == 413:
            return DeliveryResult(DeliveryStatus.TOO_LARGE)
        if status == 429:
            return DeliveryResult(DeliveryStatus.RATE_LIMITED)
        if status != 201 or len(raw) > MAX_RESPONSE_BYTES:
            return DeliveryResult(DeliveryStatus.FAILED)
        try:
            decoded = json.loads(raw.decode("utf-8"))
            issue_number = int(decoded["issueNumber"])
            issue_url = str(decoded["issueUrl"])
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
            return DeliveryResult(DeliveryStatus.FAILED)
        if issue_number <= 0 or _validated_https_endpoint(issue_url) is None:
            return DeliveryResult(DeliveryStatus.FAILED)
        return DeliveryResult(DeliveryStatus.SUCCESS, issue_number, issue_url)


def configured_report_transport(
    *,
    environment: Mapping[str, str] | None = None,
    resource_path: Path | None = None,
):
    """Wybierz HTTPS tylko z jawnej konfiguracji; brak kończy się trybem lokalnym."""

    env = os.environ if environment is None else environment
    configured = env.get(ENDPOINT_ENVIRONMENT_VARIABLE, "")
    if not configured:
        source = resource_path or Path(__file__).with_name(ENDPOINT_RESOURCE_NAME)
        try:
            if source.is_file() and source.stat().st_size <= 2048:
                configured = source.read_text(encoding="utf-8")
        except OSError:
            configured = ""
    endpoint = _validated_https_endpoint(configured)
    return HttpReportTransport(endpoint) if endpoint else LocalOnlyTransport()


def transport_is_online(transport: object) -> bool:
    return isinstance(transport, HttpReportTransport)
