"""Natywne kontrolki z jawnym kontraktem klawiatury i czytnika ekranu."""

from __future__ import annotations

import wx


class FocusableReadOnlyTextCtrl(wx.TextCtrl):
    """Pole tylko do odczytu, które pozostaje przystankiem nawigacji Tab.

    wxWidgets domyślnie zwraca ``False`` z ``AcceptsFocusFromKeyboard`` dla
    ``TextCtrl`` ze stylem ``TE_READONLY``.  Pole nadal można wskazać myszą,
    ale Tab je pomija, więc NVDA nie odczytuje nazwy i bieżącej wartości.
    Nadpisanie tej jednej decyzji zachowuje natywną rolę pola tekstowego oraz
    blokadę edycji, a przywraca zwykłą kolejność klawiatury.
    """

    def __init__(self, *args, style: int = 0, **kwargs) -> None:
        super().__init__(*args, style=style | wx.TE_READONLY, **kwargs)

    def AcceptsFocusFromKeyboard(self) -> bool:  # noqa: N802 - API wxWidgets
        return self.IsEnabled() and self.IsShownOnScreen() and self.CanAcceptFocus()
