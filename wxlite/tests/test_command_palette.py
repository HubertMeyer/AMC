"""Paleta udostępnia wyłącznie jawne nazwy istniejących akcji."""

from __future__ import annotations

from amc_wx_lite.command_palette import count_label, entries_for_session, filter_entries
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.shortcuts import Action, Chord, resolve


def test_palette_is_reachable_from_both_views() -> None:
    chord = Chord("K", ctrl=True, shift=True)
    assert resolve(chord, player_view=False, radio_session=False) is Action.COMMAND_PALETTE
    assert resolve(chord, player_view=True, radio_session=False) is Action.COMMAND_PALETTE


def test_palette_entries_are_unique_user_facing_actions_for_the_session() -> None:
    for session in SessionId:
        entries = entries_for_session(session)
        assert entries
        assert len({entry.action for entry in entries}) == len(entries)
        assert all(entry.label and "Action." not in entry.label for entry in entries)
        assert all("{" not in entry.label for entry in entries)
        assert any(entry.action is Action.COMMAND_PALETTE for entry in entries)

    tidal = entries_for_session(SessionId.TIDAL)
    assert not any(entry.action is Action.RECORD_TOGGLE for entry in tidal)
    radio = entries_for_session(SessionId.RADIO)
    assert any(entry.action is Action.RECORD_TOGGLE for entry in radio)


def test_palette_filter_is_accent_insensitive_and_requires_every_word() -> None:
    entries = entries_for_session(SessionId.RADIO)
    result = filter_entries(entries, "paleta polecen")
    assert [entry.action for entry in result] == [Action.COMMAND_PALETTE]
    assert filter_entries(entries, "nieistniejące polecenie") == ()


def test_palette_count_labels_are_intentional_polish_text() -> None:
    assert count_label(0) == "Brak pasujących poleceń"
    assert count_label(1) == "1 polecenie"
    assert count_label(3) == "3 polecenia"
    assert count_label(5) == "5 poleceń"


def test_palette_shortcuts_never_expose_internal_key_names() -> None:
    labels = [entry.label for entry in entries_for_session(SessionId.FILES)]
    assert any("Page Down" in label for label in labels)
    assert all("Prior" not in label and "Next" not in label for label in labels)
    assert all("Page strzałka" not in label for label in labels)
