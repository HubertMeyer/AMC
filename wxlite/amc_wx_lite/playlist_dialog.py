"""Dostępne okno członkostwa lokalnych playlist AMC.

Lista otrzymuje wyłącznie gotowe napisy użytkowe. Obiekty robocze, Id oraz
surowe rekordy protokołu nigdy nie stają się nazwą dostępną kontrolki.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
import uuid
from typing import Iterable

import wx


class PlaylistPayloadError(ValueError):
    """Niepełna odpowiedź hosta, opisana bez ujawniania technicznych danych."""


def _format_count(count: int) -> str:
    if count == 1:
        return "1 element"
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return f"{count} elementy"
    return f"{count} elementów"


def _dotnet_utc_ticks() -> int:
    return 621_355_968_000_000_000 + time.time_ns() // 100


@dataclass(slots=True)
class PlaylistChoice:
    playlist_id: str
    name: str
    created_utc_ticks: int
    item_ids: list[str]
    membership: bool | None

    @property
    def label(self) -> str:
        state = (
            "zaznaczona"
            if self.membership is True
            else "niezaznaczona"
            if self.membership is False
            else "stan mieszany"
        )
        return f"{self.name}, {state}, {_format_count(len(self.item_ids))}"

    def set_membership(self, selected_item_ids: Iterable[str], include: bool) -> None:
        selected = list(dict.fromkeys(
            value.strip() for value in selected_item_ids if value and value.strip()
        ))
        selected_set = set(selected)
        if include:
            known = set(self.item_ids)
            self.item_ids.extend(value for value in selected if value not in known)
        else:
            self.item_ids[:] = [value for value in self.item_ids if value not in selected_set]
        self.membership = include

    def toggle(self, selected_item_ids: Iterable[str]) -> bool:
        include = self.membership is not True
        self.set_membership(selected_item_ids, include)
        return include

    def payload(self) -> dict[str, object]:
        return {
            "playlistId": self.playlist_id,
            "name": self.name,
            "createdUtcTicks": self.created_utc_ticks,
            "itemIds": list(self.item_ids),
        }


def choices_from_payload(
    payload: object,
    selected_item_ids: Iterable[str],
) -> list[PlaylistChoice]:
    """Waliduj migawkę hosta i policz stan całego zaznaczenia."""
    if not isinstance(payload, dict) or not isinstance(payload.get("playlists"), list):
        raise PlaylistPayloadError("Nie udało się odczytać listy playlist AMC")
    selected = list(dict.fromkeys(
        value.strip() for value in selected_item_ids if value and value.strip()
    ))
    selected_set = set(selected)
    result: list[PlaylistChoice] = []
    seen: set[str] = set()
    for raw in payload["playlists"]:
        if not isinstance(raw, dict):
            raise PlaylistPayloadError("Lista playlist AMC zawiera uszkodzony wpis")
        playlist_id = str(raw.get("playlistId") or "").strip()
        name = str(raw.get("name") or "").strip()
        item_values = raw.get("itemIds")
        if not playlist_id or playlist_id in seen or not name or not isinstance(item_values, list):
            raise PlaylistPayloadError("Lista playlist AMC zawiera niepełny wpis")
        seen.add(playlist_id)
        item_ids = list(dict.fromkeys(
            str(value).strip()
            for value in item_values
            if isinstance(value, str) and value.strip()
        ))
        contained = len(selected_set.intersection(item_ids))
        membership: bool | None = (
            False if contained == 0 else True if contained == len(selected) else None
        )
        try:
            created = int(raw.get("createdUtcTicks") or 0)
        except (TypeError, ValueError):
            created = 0
        result.append(PlaylistChoice(
            playlist_id=playlist_id,
            name=name,
            created_utc_ticks=created if created > 0 else _dotnet_utc_ticks(),
            item_ids=item_ids,
            membership=membership,
        ))
    return result


class PlaylistMembershipDialog(wx.Dialog):
    """Natywny odpowiednik ``PlaylistWindow`` z głównego AMC."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        choices: list[PlaylistChoice],
        selected_item_ids: list[str],
        target_label: str,
    ) -> None:
        super().__init__(
            parent,
            title="Przynależność do playlist",
            size=(650, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._choices = [PlaylistChoice(
            choice.playlist_id,
            choice.name,
            choice.created_utc_ticks,
            list(choice.item_ids),
            choice.membership,
        ) for choice in choices]
        self._selected_item_ids = list(dict.fromkeys(selected_item_ids))
        self._visible_indices: list[int] = []

        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        description = (
            f"Zmień playlisty dla: {target_label}. Spacja zmienia stan, Enter zapisuje."
            if len(self._selected_item_ids) == 1
            else (
                f"Zmień playlisty dla zaznaczenia: {_format_count(len(self._selected_item_ids))}. "
                "Stan mieszany oznacza, że playlista zawiera tylko część zaznaczenia."
            )
        )
        heading = wx.StaticText(panel, label=description)
        heading.SetName(description)
        layout.Add(heading, 0, wx.ALL | wx.EXPAND, 12)

        filter_label = wx.StaticText(panel, label="&Filtruj playlisty:")
        layout.Add(filter_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        self.filter_box = wx.TextCtrl(panel)
        self.filter_box.SetName("Filtruj playlisty")
        layout.Add(self.filter_box, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        self.playlist_list = wx.ListBox(panel, choices=[], style=wx.LB_SINGLE)
        self.playlist_list.SetName("Playlisty")
        self.playlist_list.SetToolTip(
            "Strzałki wybierają playlistę. Spacja zmienia przynależność zaznaczonych elementów."
        )
        layout.Add(self.playlist_list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)

        self.status = wx.StaticText(panel, label="Gotowe")
        self.status.SetName("Wynik zmiany playlist")
        layout.Add(self.status, 0, wx.ALL | wx.EXPAND, 12)
        panel.SetSizer(layout)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.new_button = wx.Button(self, label="&Nowa…")
        self.rename_button = wx.Button(self, label="Zmień &nazwę…")
        self.delete_button = wx.Button(self, label="&Usuń playlistę…")
        self.save_button = wx.Button(self, wx.ID_OK, label="&Zapisz")
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, label="&Anuluj")
        for button, name in (
            (self.new_button, "Utwórz nową playlistę"),
            (self.rename_button, "Zmień nazwę playlisty"),
            (self.delete_button, "Usuń playlistę"),
            (self.save_button, "Zapisz zmiany playlist"),
            (self.cancel_button, "Anuluj zmiany playlist"),
        ):
            button.SetName(name)
            buttons.Add(button, 0, wx.RIGHT, 8)
        self.save_button.SetDefault()

        shell = wx.BoxSizer(wx.VERTICAL)
        shell.Add(panel, 1, wx.EXPAND)
        shell.Add(buttons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 12)
        self.SetSizer(shell)
        self.SetMinSize((520, 360))

        self.filter_box.Bind(wx.EVT_TEXT, self._filter_changed)
        self.new_button.Bind(wx.EVT_BUTTON, self._create)
        self.rename_button.Bind(wx.EVT_BUTTON, self._rename)
        self.delete_button.Bind(wx.EVT_BUTTON, self._delete)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.Bind(wx.EVT_SHOW, self._on_show)
        self._rebuild()

    @property
    def result_playlists(self) -> list[dict[str, object]]:
        return [choice.payload() for choice in self._choices]

    def _on_show(self, event: wx.ShowEvent) -> None:
        event.Skip()
        if event.IsShown():
            wx.CallAfter(
                self.playlist_list.SetFocus
                if self._visible_indices
                else self.new_button.SetFocus
            )

    def _selected_choice(self) -> PlaylistChoice | None:
        visible_index = self.playlist_list.GetSelection()
        if not 0 <= visible_index < len(self._visible_indices):
            return None
        return self._choices[self._visible_indices[visible_index]]

    def _rebuild(self, preferred_id: str | None = None) -> None:
        previous = preferred_id
        if previous is None and (choice := self._selected_choice()) is not None:
            previous = choice.playlist_id
        filter_text = self.filter_box.GetValue().strip().casefold()
        self._visible_indices = [
            index for index, choice in enumerate(self._choices)
            if not filter_text or filter_text in choice.name.casefold()
        ]
        labels = [self._choices[index].label for index in self._visible_indices]
        self.playlist_list.Set(labels)
        selected = next((
            index for index, source_index in enumerate(self._visible_indices)
            if self._choices[source_index].playlist_id == previous
        ), 0 if labels else wx.NOT_FOUND)
        self.playlist_list.SetSelection(selected)
        available = selected != wx.NOT_FOUND
        self.rename_button.Enable(available)
        self.delete_button.Enable(available)

    def _filter_changed(self, _event: wx.CommandEvent) -> None:
        self._rebuild()

    def _set_status(self, message: str) -> None:
        self.status.SetLabel(message)
        self.status.SetName(message)

    def _toggle(self) -> None:
        choice = self._selected_choice()
        if choice is None:
            self._set_status("Brak playlisty do zmiany")
            return
        included = choice.toggle(self._selected_item_ids)
        self._rebuild(choice.playlist_id)
        message = (
            f"Zaznaczona: {choice.name}"
            if included
            else f"Niezaznaczona: {choice.name}"
        )
        self._set_status(message)

    def _ask_name(self, title: str, current: str = "") -> str | None:
        dialog = wx.TextEntryDialog(self, "Nazwa playlisty:", title, current)
        try:
            dialog.SetName(title)
            if dialog.ShowModal() != wx.ID_OK:
                return None
            name = dialog.GetValue().strip()
        finally:
            dialog.Destroy()
        if not name:
            self._set_status("Nazwa playlisty jest pusta")
            return None
        if len(name) > 200:
            self._set_status("Nazwa playlisty może mieć najwyżej 200 znaków")
            return None
        return name

    def _name_exists(self, name: str, ignored_id: str | None = None) -> bool:
        return any(
            choice.playlist_id != ignored_id
            and choice.name.casefold() == name.casefold()
            for choice in self._choices
        )

    def _create(self, _event=None) -> None:
        name = self._ask_name("Nowa playlista")
        if name is None:
            self.playlist_list.SetFocus() if self._visible_indices else self.new_button.SetFocus()
            return
        if self._name_exists(name):
            self._set_status(f"Playlista „{name}” już istnieje")
            self.playlist_list.SetFocus() if self._visible_indices else self.new_button.SetFocus()
            return
        choice = PlaylistChoice(
            playlist_id=uuid.uuid4().hex,
            name=name,
            created_utc_ticks=_dotnet_utc_ticks(),
            item_ids=list(self._selected_item_ids),
            membership=True,
        )
        self._choices.append(choice)
        self.filter_box.ChangeValue("")
        self._rebuild(choice.playlist_id)
        self._set_status(f"Utworzono roboczo playlistę: {name}")
        self.playlist_list.SetFocus()

    def _rename(self, _event=None) -> None:
        choice = self._selected_choice()
        if choice is None:
            self._set_status("Wybierz playlistę do zmiany nazwy")
            return
        name = self._ask_name("Zmień nazwę playlisty", choice.name)
        if name is None:
            self.playlist_list.SetFocus()
            return
        if self._name_exists(name, choice.playlist_id):
            self._set_status(f"Playlista „{name}” już istnieje")
            self.playlist_list.SetFocus()
            return
        choice.name = name
        self.filter_box.ChangeValue("")
        self._rebuild(choice.playlist_id)
        self._set_status(f"Zmieniono roboczo nazwę playlisty na: {name}")
        self.playlist_list.SetFocus()

    def _delete(self, _event=None) -> None:
        choice = self._selected_choice()
        if choice is None:
            self._set_status("Wybierz playlistę do usunięcia")
            return
        dialog = wx.MessageDialog(
            self,
            f"Usunąć playlistę „{choice.name}”? Pliki multimedialne pozostaną bez zmian.",
            "Usuń playlistę",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        try:
            dialog.SetName("Potwierdzenie usunięcia playlisty")
            accepted = dialog.ShowModal() == wx.ID_YES
        finally:
            dialog.Destroy()
        if not accepted:
            self.playlist_list.SetFocus()
            return
        removed_name = choice.name
        self._choices = [
            candidate for candidate in self._choices
            if candidate.playlist_id != choice.playlist_id
        ]
        self._rebuild()
        self._set_status(f"Usunięto roboczo playlistę: {removed_name}")
        self.playlist_list.SetFocus() if self._visible_indices else self.new_button.SetFocus()

    def _on_key(self, event: wx.KeyEvent) -> None:
        key = event.GetKeyCode()
        modifiers = event.GetModifiers()
        if modifiers == wx.MOD_CONTROL and key in (ord("K"), ord("k")):
            self.filter_box.SetFocus()
            self.filter_box.SelectAll()
            return
        if modifiers == wx.MOD_NONE and key == wx.WXK_ESCAPE and self.filter_box.GetValue():
            self.filter_box.ChangeValue("")
            self._rebuild()
            self.playlist_list.SetFocus() if self._visible_indices else self.new_button.SetFocus()
            return
        if (
            (modifiers == wx.MOD_NONE and key == wx.WXK_INSERT)
            or (modifiers == wx.MOD_CONTROL and key in (ord("N"), ord("n")))
        ):
            self._create()
            return
        if modifiers == wx.MOD_NONE and key == wx.WXK_F2:
            self._rename()
            return
        if modifiers == wx.MOD_NONE and key == wx.WXK_DELETE:
            self._delete()
            return
        if (
            modifiers == wx.MOD_NONE
            and key == wx.WXK_SPACE
            and self.playlist_list.HasFocus()
        ):
            self._toggle()
            return
        if modifiers == wx.MOD_NONE and key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self.EndModal(wx.ID_OK)
            return
        event.Skip()
