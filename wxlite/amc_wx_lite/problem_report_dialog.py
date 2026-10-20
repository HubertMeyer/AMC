"""Dostępny formularz Sygnalisty z jawnym podglądem i wysyłką w tle."""

from __future__ import annotations

import platform
import sys
import uuid
from pathlib import Path
from typing import Callable

import wx

from . import __version__
from .async_gate import BackgroundRunner, StaleResultGate
from .problem_report import (
    REPORT_KIND_LABELS,
    DeliveryResult,
    DeliveryStatus,
    PreparedReport,
    ReportDraft,
    ReportEnvironment,
    ReportKind,
    ReportTransport,
    deliver_report,
    prepare_report,
    read_log_tail,
    save_report_atomic,
)
from .problem_report_transport import configured_report_transport, transport_is_online
from .release_profile import current_profile
from .version_info import read_build_label


class ProblemReportDialog(wx.Dialog):
    """Formularz, podgląd oraz lokalne lub internetowe działania na raporcie."""

    def __init__(
        self,
        parent,
        *,
        active_session: str,
        reports_directory: Path,
        log_path: Path,
        copy_text: Callable[[str], bool],
        announce: Callable[[str], None],
        transport: ReportTransport | None = None,
        runner: BackgroundRunner | None = None,
    ) -> None:
        super().__init__(parent, title="Zgłoś błąd lub sugestię", size=(760, 720))
        self._active_session = active_session
        self._reports_directory = Path(reports_directory)
        self._log_path = Path(log_path)
        self._copy_text = copy_text
        self._announce = announce
        self._transport = transport or configured_report_transport()
        self._online = transport_is_online(self._transport)
        self._gate = StaleResultGate(alive=self._window_alive)
        self._runner = runner or BackgroundRunner(self._gate, to_gui=wx.CallAfter)
        self._prepared: PreparedReport | None = None
        self._report_id = str(uuid.uuid4())
        self._issue_url: str | None = None
        self._sending = False

        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(
            panel,
            label=(
                (
                    "Przed wysłaniem przejrzyj cały zredagowany raport. "
                    "AMC wyśle dokładnie tę widoczną treść."
                )
                if self._online
                else (
                    "Wysyłanie przez Internet nie jest jeszcze skonfigurowane. "
                    "Możesz przejrzeć cały zredagowany raport, skopiować go albo "
                    "zapisać lokalnie."
                )
            ),
        )
        intro.Wrap(700)
        root.Add(intro, 0, wx.EXPAND | wx.ALL, 10)

        root.Add(wx.StaticText(panel, label="Rodzaj zgłoszenia:"), 0, wx.LEFT | wx.RIGHT, 10)
        self.kind = wx.Choice(panel, choices=tuple(REPORT_KIND_LABELS.values()))
        self.kind.SetName("Rodzaj zgłoszenia")
        self.kind.SetSelection(0)
        root.Add(self.kind, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        root.Add(wx.StaticText(panel, label="Tytuł:"), 0, wx.LEFT | wx.RIGHT, 10)
        self.subject = wx.TextCtrl(panel)
        self.subject.SetName("Tytuł zgłoszenia")
        self.subject.SetHint("Krótko opisz problem albo pomysł")
        self.subject.SetMaxLength(200)
        root.Add(self.subject, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        root.Add(wx.StaticText(panel, label="Opis:"), 0, wx.LEFT | wx.RIGHT, 10)
        self.description = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_WORDWRAP, size=(-1, 100)
        )
        self.description.SetName("Opis zgłoszenia")
        root.Add(self.description, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        root.Add(
            wx.StaticText(panel, label="Kroki odtworzenia, nieobowiązkowe:"),
            0,
            wx.LEFT | wx.RIGHT,
            10,
        )
        self.steps = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_WORDWRAP, size=(-1, 80)
        )
        self.steps.SetName("Kroki odtworzenia, nieobowiązkowe")
        root.Add(self.steps, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.include_log = wx.CheckBox(
            panel,
            label="Dołącz ostatnie wpisy dziennika po automatycznej redakcji",
        )
        self.include_log.SetName(
            "Dołącz dziennik diagnostyczny po automatycznej redakcji, domyślnie wyłączone"
        )
        self.include_log.SetValue(False)
        root.Add(self.include_log, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        root.Add(
            wx.StaticText(
                panel,
                label=(
                    "Pełny raport, dokładnie ta treść zostanie wysłana, "
                    "skopiowana lub zapisana:"
                    if self._online
                    else "Pełny raport, dokładnie ta treść zostanie skopiowana lub zapisana:"
                ),
            ),
            0,
            wx.LEFT | wx.RIGHT,
            10,
        )
        self.preview = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
        )
        self.preview.SetName("Pełny podgląd zredagowanego raportu")
        root.Add(self.preview, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        refresh = wx.Button(panel, label="Odśwież podgląd")
        copy_button = wx.Button(panel, label="Skopiuj raport")
        save_button = wx.Button(panel, label="Zapisz raport")
        self._send_button = None
        if self._online:
            self._send_button = wx.Button(panel, label="Wyślij zgłoszenie")
            self._send_button.SetName("Wyślij widoczny zredagowany raport")
        self._copy_issue_button = wx.Button(panel, label="Skopiuj adres zgłoszenia")
        self._copy_issue_button.SetName("Skopiuj adres utworzonego zgłoszenia")
        self._copy_issue_button.Hide()
        cancel = wx.Button(panel, wx.ID_CANCEL, "Zamknij")
        action_buttons = [refresh, copy_button, save_button]
        if self._send_button is not None:
            action_buttons.append(self._send_button)
        action_buttons.extend((self._copy_issue_button, cancel))
        for button in action_buttons:
            buttons.Add(button, 0, wx.LEFT, 8)
        root.Add(buttons, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
        panel.SetSizer(root)

        refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        copy_button.Bind(wx.EVT_BUTTON, self._on_copy)
        save_button.Bind(wx.EVT_BUTTON, self._on_save)
        if self._send_button is not None:
            self._send_button.Bind(wx.EVT_BUTTON, self._on_send)
        self._copy_issue_button.Bind(wx.EVT_BUTTON, self._on_copy_issue_url)
        self.kind.Bind(wx.EVT_CHOICE, self._on_refresh)
        self.include_log.Bind(wx.EVT_CHECKBOX, self._on_refresh)
        self.subject.Bind(wx.EVT_TEXT, self._on_refresh)
        self.description.Bind(wx.EVT_TEXT, self._on_refresh)
        self.steps.Bind(wx.EVT_TEXT, self._on_refresh)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self._refresh_preview()
        wx.CallAfter(self.subject.SetFocus)

    def _window_alive(self) -> bool:
        try:
            return bool(self) and not self.IsBeingDeleted()
        except RuntimeError:
            return False

    def _environment(self) -> ReportEnvironment:
        profile = current_profile()
        system = " ".join(filter(None, (
            platform.system(), platform.release(), platform.version()
        )))
        wx_version = getattr(wx, "__version__", "nieznana")
        return ReportEnvironment(
            application_name=profile.display_name,
            version=__version__,
            build=read_build_label() or "kompilacja lokalna",
            channel=profile.update_channel,
            operating_system=system,
            active_session=self._active_session,
            components=f"Python {sys.version_info.major}.{sys.version_info.minor}; wxPython {wx_version}; host .NET 8",
        )

    def _draft(self) -> ReportDraft:
        kind = ReportKind.SUGGESTION if self.kind.GetSelection() == 1 else ReportKind.BUG
        return ReportDraft(
            kind=kind,
            title=self.subject.GetValue(),
            description=self.description.GetValue(),
            reproduction_steps=self.steps.GetValue(),
            include_log=self.include_log.GetValue(),
        )

    def _refresh_preview(self) -> PreparedReport:
        draft = self._draft()
        log = read_log_tail(self._log_path) if draft.include_log else ()
        candidate = prepare_report(
            draft,
            self._environment(),
            log_lines=log,
            report_id=self._report_id,
        )
        if self._prepared is not None and (
            candidate.title,
            candidate.body,
            candidate.included_log,
            candidate.kind,
        ) != (
            self._prepared.title,
            self._prepared.body,
            self._prepared.included_log,
            self._prepared.kind,
        ):
            self._report_id = str(uuid.uuid4())
            candidate = prepare_report(
                draft,
                self._environment(),
                log_lines=log,
                report_id=self._report_id,
            )
            self._issue_url = None
            self._copy_issue_button.Hide()
            self.Layout()
        self._prepared = candidate
        self.preview.ChangeValue(self._prepared.body)
        return self._prepared

    def _on_refresh(self, _event) -> None:
        self._refresh_preview()

    def _on_copy(self, _event) -> None:
        report = self._refresh_preview()
        self._announce(
            "Raport skopiowany do schowka"
            if self._copy_text(report.body)
            else "Nie udało się skopiować raportu do schowka"
        )
        self.preview.SetFocus()

    def _on_send(self, _event) -> None:
        if self._send_button is None or self._sending:
            return
        report = self._refresh_preview()
        self._sending = True
        self._send_button.Disable()
        self._announce("Wysyłanie zgłoszenia")
        self._runner.submit(
            "problem-report-delivery",
            lambda: deliver_report(self._transport, report),
            self._on_delivery_result,
            self._on_delivery_error,
        )

    def _on_delivery_result(self, result: DeliveryResult) -> None:
        self._sending = False
        if self._send_button is not None:
            self._send_button.Enable()
        if result.status is DeliveryStatus.SUCCESS and result.issue_url:
            self._issue_url = result.issue_url
            self._copy_issue_button.Show()
            self.Layout()
            self._copy_issue_button.SetFocus()
        elif self._send_button is not None:
            self._send_button.SetFocus()
        self._announce(result.user_message)

    def _on_delivery_error(self, _error: Exception) -> None:
        self._on_delivery_result(DeliveryResult(DeliveryStatus.FAILED))

    def _on_copy_issue_url(self, _event) -> None:
        if not self._issue_url:
            return
        self._announce(
            "Adres zgłoszenia skopiowany do schowka"
            if self._copy_text(self._issue_url)
            else "Nie udało się skopiować adresu zgłoszenia do schowka"
        )
        self._copy_issue_button.SetFocus()

    def _on_close(self, event) -> None:
        self._gate.cancel_all()
        event.Skip()

    def _on_save(self, _event) -> None:
        report = self._refresh_preview()
        try:
            path = save_report_atomic(report, self._reports_directory)
        except OSError:
            self._announce("Nie udało się zapisać raportu")
        else:
            del path
            self._announce(
                "Raport zapisany w folderze zgłoszeń bieżącej wersji AMC"
            )
        self.preview.SetFocus()
