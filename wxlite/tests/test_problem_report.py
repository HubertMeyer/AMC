"""REL-001: lokalny Sygnalista, prywatność i parytet odkrywania poleceń."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.problem_report import (
    MAX_REPORT_BYTES,
    DeliveryResult,
    DeliveryStatus,
    LocalOnlyTransport,
    PreparedReport,
    ReportDraft,
    ReportEnvironment,
    ReportKind,
    deliver_report,
    prepare_report,
    read_log_tail,
    redact_private_data,
    save_report_atomic,
)
from amc_wx_lite.release_profile import PUBLIC_PROFILE, TEST_PROFILE
from amc_wx_lite.shortcuts import (
    Action,
    SONOS_SUPPORTED_ACTIONS,
    SPOTIFY_SUPPORTED_ACTIONS,
    TIDAL_SUPPORTED_ACTIONS,
    WIIM_SUPPORTED_ACTIONS,
    describe,
    describe_action,
)


def _environment() -> ReportEnvironment:
    return ReportEnvironment(
        application_name="AMC Test",
        version="0.1.0",
        build="2026.10.19-abcdef0",
        channel="test",
        operating_system="Windows 11",
        active_session="Radio",
        components="Python 3.14; wxPython 4; host .NET 8",
    )


def test_private_values_are_removed_before_preview_copy_or_save() -> None:
    private = "\n".join((
        r"C:\Users\Jan\Nagrania\tajny-program.mp3",
        r"\\serwer\prywatne\sekret.wav",
        "file:///C:/Users/Jan/prywatny.txt",
        "https://example.test/private?token=sekret",
        "jan.kowalski@example.test",
        "192.168.10.52",
        "aa:bb:cc:dd:ee:ff",
        "123e4567-e89b-12d3-a456-426614174000",
        "Authorization: Bearer bardzo-tajny-token",
        '"access_token": "token-z-json"',
        "refresh_token=token-odswiezenia",
        "accountName: Jan Kowalski",
        "piosenka.mp3",
    ))

    safe = redact_private_data(private)

    for secret in (
        "Jan", "tajny-program.mp3", "sekret.wav", "prywatny.txt",
        "example.test", "jan.kowalski", "192.168.10.52",
        "aa:bb:cc:dd:ee:ff", "123e4567", "bardzo-tajny-token",
        "token-z-json", "token-odswiezenia", "Kowalski", "piosenka.mp3",
    ):
        assert secret not in safe
    assert "[ścieżka prywatna]" in safe
    assert "[wartość usunięta]" in safe


def test_report_uses_one_redacted_body_and_log_is_off_by_default() -> None:
    report = prepare_report(
        ReportDraft(
            ReportKind.BUG,
            "Problem z nagraniem.mp3",
            r"Plik C:\Users\Jan\Nagrania\audycja.mp3 nie działa",
        ),
        _environment(),
        log_lines=("Authorization: Bearer sekret",),
    )

    assert report.included_log is False
    assert "Dziennik diagnostyczny" not in report.body
    assert "sekret" not in report.body
    assert "Jan" not in report.body
    assert "Log dołączony: nie" in report.body


def test_log_reader_is_bounded_and_redacted(tmp_path: Path) -> None:
    log = tmp_path / "frontend.log"
    log.write_text(
        "\n".join(
            f"wiersz {number}: plik-{number}.mp3"
            for number in range(300)
        ) + "\nAuthorization: Bearer ostatni-sekret\n",
        encoding="utf-8",
    )

    lines = read_log_tail(log)

    assert 1 <= len(lines) <= 200
    assert not any("ostatni-sekret" in line for line in lines)
    assert not any(".mp3" in line for line in lines)
    assert not any("wiersz 0:" in line for line in lines)


def test_atomic_save_writes_exact_preview_in_selected_profile_folder(
    tmp_path: Path,
) -> None:
    report = PreparedReport("[Błąd] Tytuł", "dokładny podgląd\n", False)
    target = save_report_atomic(
        report,
        tmp_path / "AMC Test" / "reports",
        moment=datetime(2026, 10, 19, 3, 4, 5, tzinfo=timezone.utc),
    )

    assert target.parent == tmp_path / "AMC Test" / "reports"
    assert target.name == "zgloszenie-20261019-030405.txt"
    assert target.read_text(encoding="utf-8") == report.body
    assert not list(target.parent.glob("*.tmp"))


class _Transport:
    def __init__(self, result) -> None:
        self.result = result
        self.calls: list[PreparedReport] = []

    def send(self, report: PreparedReport):
        self.calls.append(report)
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


def test_transport_contract_reports_success_error_offline_rate_and_size() -> None:
    report = PreparedReport("Tytuł", "treść\n", False)
    success = _Transport(DeliveryResult(DeliveryStatus.SUCCESS, 42, "https://issue"))
    failure = _Transport(DeliveryResult(DeliveryStatus.FAILED))
    offline = _Transport(ConnectionError("brak sieci"))
    rate = _Transport(DeliveryResult(DeliveryStatus.RATE_LIMITED))
    too_large = _Transport(DeliveryResult(DeliveryStatus.SUCCESS))

    assert deliver_report(success, report).status is DeliveryStatus.SUCCESS
    assert success.calls == [report]
    assert deliver_report(failure, report).status is DeliveryStatus.FAILED
    assert deliver_report(offline, report).status is DeliveryStatus.OFFLINE
    assert deliver_report(rate, report).status is DeliveryStatus.RATE_LIMITED
    oversized = PreparedReport("Tytuł", "x" * (MAX_REPORT_BYTES + 1), False)
    assert deliver_report(too_large, oversized).status is DeliveryStatus.TOO_LARGE
    assert too_large.calls == []
    assert LocalOnlyTransport().send(report).status is DeliveryStatus.NOT_CONFIGURED


def test_report_command_has_one_name_in_menu_palette_help_and_dispatch() -> None:
    action = Action.REPORT_PROBLEM
    for session in SessionId:
        entries = {entry.action: entry for entry in entries_for_session(session)}
        assert entries[action].name == "Zgłoś błąd lub sugestię…"
        assert entries[action].shortcut is None
    assert describe_action(action) == "Zgłoś błąd lub sugestię"
    assert ("Bez skrótu", "Zgłoś błąd lub sugestię") in describe()
    gui_source = (
        Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"
    ).read_text(encoding="utf-8")
    assert "elif action is Action.REPORT_PROBLEM:" in gui_source
    assert "self._show_problem_report()" in gui_source
    for supported in (
        TIDAL_SUPPORTED_ACTIONS,
        SPOTIFY_SUPPORTED_ACTIONS,
        WIIM_SUPPORTED_ACTIONS,
        SONOS_SUPPORTED_ACTIONS,
    ):
        assert action in supported


def test_both_profiles_advertise_only_the_local_report_capability() -> None:
    assert "problem-report-local" in TEST_PROFILE.capabilities
    assert "problem-report-local" in PUBLIC_PROFILE.capabilities
    assert not any("github" in value or "worker" in value for value in PUBLIC_PROFILE.capabilities)


def test_dialog_source_keeps_log_opt_in_full_preview_and_initial_focus() -> None:
    source = (
        Path(__file__).parents[1]
        / "amc_wx_lite"
        / "problem_report_dialog.py"
    ).read_text(encoding="utf-8")

    assert "self.include_log.SetValue(False)" in source
    assert "Pełny podgląd zredagowanego raportu" in source
    assert "wx.CallAfter(self.subject.SetFocus)" in source
    assert "Wysyłanie przez Internet nie jest jeszcze skonfigurowane" in source
    assert "Wyślij" not in source
    assert "path.parent" not in source
