"""Dostępny wybór natywnych playlist Spotify dla Ctrl+Shift+P.

Identyfikatory i ``snapshot_id`` pozostają danymi modelu. Lista wx otrzymuje
wyłącznie celowe etykiety użytkowe; żaden rekord ani identyfikator techniczny
nie może stać się nazwą dostępną kontrolki.
"""

from __future__ import annotations

from dataclasses import dataclass

import wx


class SpotifyPlaylistPayloadError(ValueError):
    """Krótki błąd odpowiedzi hosta bez ujawniania danych technicznych."""


@dataclass(slots=True)
class SpotifyPlaylistChoice:
    playlist_id: str
    name: str
    description: str
    selected: bool = False
    new_public: bool | None = None

    @property
    def label(self) -> str:
        state = "zaznaczona" if self.selected else "niezaznaczona"
        return f"{self.description}, {state}"

    def __str__(self) -> str:
        return self.label


def choices_from_payload(payload: object) -> list[SpotifyPlaylistChoice]:
    if not isinstance(payload, dict) or not isinstance(payload.get("playlists"), list):
        raise SpotifyPlaylistPayloadError("Nie udało się odczytać playlist Spotify")
    result: list[SpotifyPlaylistChoice] = []
    seen: set[str] = set()
    for raw in payload["playlists"]:
        if not isinstance(raw, dict):
            raise SpotifyPlaylistPayloadError("Lista playlist Spotify zawiera uszkodzony wpis")
        playlist_id = str(raw.get("id") or "").strip()
        name = str(raw.get("name") or "").strip()
        label = str(raw.get("accessibleLabel") or "").strip()
        if not playlist_id or playlist_id in seen or not name or not label:
            raise SpotifyPlaylistPayloadError("Lista playlist Spotify zawiera niepełny wpis")
        seen.add(playlist_id)
        result.append(SpotifyPlaylistChoice(playlist_id, name, label))
    return result


class SpotifyPlaylistDialog(wx.Dialog):
    """Jedna lista: Spacja zaznacza wiele celów, Enter zapisuje."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        choices: list[SpotifyPlaylistChoice],
        target_label: str,
    ) -> None:
        super().__init__(
            parent,
            title="Dodaj do playlist Spotify",
            size=(690, 470),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._choices = list(choices)
        self._temporary_counter = 0

        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        instruction = (
            f"Dodaj do playlist Spotify: {target_label}. "
            "Spacja zaznacza lub odznacza playlistę. Enter wykonuje zmianę."
        )
        heading = wx.StaticText(panel, label=instruction)
        heading.SetName(instruction)
        layout.Add(heading, 0, wx.ALL | wx.EXPAND, 12)

        self.playlist_list = wx.ListBox(panel, choices=[], style=wx.LB_SINGLE)
        self.playlist_list.SetName("Playlisty Spotify do dodania")
        self.playlist_list.SetToolTip(
            "Strzałki wybierają playlistę. Spacja zmienia jej zaznaczenie."
        )
        layout.Add(self.playlist_list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)

        self.status = wx.StaticText(panel, label="Wybierz co najmniej jedną playlistę")
        self.status.SetName("Stan wyboru playlist Spotify")
        layout.Add(self.status, 0, wx.ALL | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.new_button = wx.Button(self, label="&Nowa playlista…")
        self.save_button = wx.Button(self, wx.ID_OK, label="&Dodaj")
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        self.new_button.SetName("Utwórz nową playlistę Spotify")
        self.save_button.SetName("Dodaj do zaznaczonych playlist Spotify")
        self.cancel_button.SetName("Anuluj dodawanie do playlist Spotify")
        for button in (self.new_button, self.save_button, self.cancel_button):
            buttons.Add(button, 0, wx.RIGHT, 8)
        self.save_button.SetDefault()

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((540, 350))

        self.new_button.Bind(wx.EVT_BUTTON, self._create)
        self.save_button.Bind(wx.EVT_BUTTON, self._save)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.Bind(wx.EVT_SHOW, self._on_show)
        self._rebuild()

    @property
    def selected_playlist_ids(self) -> list[str]:
        return [
            choice.playlist_id
            for choice in self._choices
            if choice.selected and choice.new_public is None
        ]

    @property
    def new_playlists(self) -> list[tuple[str, bool]]:
        return [
            (choice.name, bool(choice.new_public))
            for choice in self._choices
            if choice.selected and choice.new_public is not None
        ]

    def _selected_choice(self) -> SpotifyPlaylistChoice | None:
        index = self.playlist_list.GetSelection()
        return self._choices[index] if 0 <= index < len(self._choices) else None

    def _rebuild(self, preferred_id: str | None = None) -> None:
        previous = preferred_id
        if previous is None and (choice := self._selected_choice()) is not None:
            previous = choice.playlist_id
        self.playlist_list.Set([choice.label for choice in self._choices])
        selected = next((
            index for index, choice in enumerate(self._choices)
            if choice.playlist_id == previous
        ), 0 if self._choices else wx.NOT_FOUND)
        self.playlist_list.SetSelection(selected)
        count = sum(choice.selected for choice in self._choices)
        message = (
            "Wybierz co najmniej jedną playlistę"
            if count == 0
            else f"Wybrane playlisty: {count}"
        )
        self.status.SetLabel(message)
        self.status.SetName(message)

    def _toggle(self) -> None:
        choice = self._selected_choice()
        if choice is None:
            self.status.SetLabel("Brak playlisty do zaznaczenia")
            return
        choice.selected = not choice.selected
        self._rebuild(choice.playlist_id)

    def _create(self, _event: object | None = None) -> None:
        name_dialog = wx.TextEntryDialog(
            self,
            "Nazwa nowej playlisty Spotify:",
            "Nowa playlista Spotify",
        )
        try:
            name_dialog.SetName("Nazwa nowej playlisty Spotify")
            if name_dialog.ShowModal() != wx.ID_OK:
                return
            name = name_dialog.GetValue().strip()
        finally:
            name_dialog.Destroy()
        if not 1 <= len(name) <= 100:
            self.status.SetLabel("Nazwa playlisty musi mieć od 1 do 100 znaków")
            self.status.SetName(self.status.GetLabel())
            return
        visibility = wx.SingleChoiceDialog(
            self,
            "Wybierz widoczność nowej playlisty:",
            "Widoczność playlisty Spotify",
            ["Prywatna (domyślna)", "Publiczna"],
        )
        try:
            visibility.SetName("Widoczność playlisty Spotify")
            visibility.SetSelection(0)
            if visibility.ShowModal() != wx.ID_OK:
                return
            is_public = visibility.GetSelection() == 1
        finally:
            visibility.Destroy()
        self._temporary_counter += 1
        kind = "publiczna" if is_public else "prywatna"
        choice = SpotifyPlaylistChoice(
            f"new-{self._temporary_counter}",
            name,
            f"Nowa playlista {name}, {kind}",
            selected=True,
            new_public=is_public,
        )
        self._choices.append(choice)
        self._rebuild(choice.playlist_id)
        self.playlist_list.SetFocus()

    def _save(self, _event: object | None = None) -> None:
        if not any(choice.selected for choice in self._choices):
            self.status.SetLabel("Wybierz co najmniej jedną playlistę")
            self.status.SetName(self.status.GetLabel())
            self.playlist_list.SetFocus() if self._choices else self.new_button.SetFocus()
            return
        self.EndModal(wx.ID_OK)

    def _on_key(self, event: wx.KeyEvent) -> None:
        if (
            event.GetModifiers() == wx.MOD_NONE
            and event.GetKeyCode() == wx.WXK_SPACE
            and self.playlist_list.HasFocus()
        ):
            self._toggle()
            return
        event.Skip()

    def _on_show(self, event: wx.ShowEvent) -> None:
        event.Skip()
        if event.IsShown():
            wx.CallAfter(
                self.playlist_list.SetFocus if self._choices else self.new_button.SetFocus
            )
