#!/usr/bin/env python3
"""Sprawdź prawdziwe Ctrl+Spacja w natywnej liście wxPython na Windows.

Test nie uruchamia AMC ani nie wysyła wejścia do aktywnego okna użytkownika.
Tworzy poza ekranem zwykły ``wx.ListCtrl``, ustawia fokus listy na trzecim
wierszu i przekazuje bezpośrednio do tej kontrolki komunikat klawiatury przy
stanie Ctrl. Sukces oznacza, że Windows dodał i następnie usunął trzeci wiersz
z nieprzylegającego zaznaczenia, pozostawiając pierwszy zaznaczony.
"""

from __future__ import annotations

import ctypes
import sys


WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_CONTROL = 0x11
VK_SPACE = 0x20


def _selected_indexes(control) -> list[int]:
    selected: list[int] = []
    index = control.GetFirstSelected()
    while index >= 0:
        selected.append(index)
        index = control.GetNextSelected(index)
    return selected


def main() -> int:
    if sys.platform != "win32":
        print("Ten test wymaga Windows.")
        return 2

    import wx

    app = wx.App(False)
    frame = wx.Frame(
        None,
        title="Próba wielokrotnego zaznaczania AMC",
        pos=(-32000, -32000),
        size=(360, 180),
        style=wx.FRAME_NO_TASKBAR,
    )
    control = wx.ListCtrl(
        frame,
        style=wx.LC_REPORT | wx.BORDER_SUNKEN,
    )
    control.InsertColumn(0, "Nazwa")
    for title in ("Pierwszy", "Drugi", "Trzeci"):
        control.InsertItem(control.GetItemCount(), title)
    control.SetItemState(
        0,
        wx.LIST_STATE_SELECTED,
        wx.LIST_STATE_SELECTED,
    )
    control.SetItemState(
        2,
        wx.LIST_STATE_FOCUSED,
        wx.LIST_STATE_FOCUSED,
    )
    frame.ShowWithoutActivating()
    app.Yield()

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
    user32.GetKeyboardState.restype = ctypes.c_bool
    user32.SetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
    user32.SetKeyboardState.restype = ctypes.c_bool
    user32.SendMessageW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_size_t,
        ctypes.c_ssize_t,
    ]
    user32.SendMessageW.restype = ctypes.c_ssize_t

    original = (ctypes.c_ubyte * 256)()
    if not user32.GetKeyboardState(original):
        print("Nie można odczytać stanu klawiatury.")
        frame.Destroy()
        return 3
    modified = (ctypes.c_ubyte * 256).from_buffer_copy(original)
    modified[VK_CONTROL] |= 0x80

    try:
        if not user32.SetKeyboardState(modified):
            print("Nie można ustawić stanu Ctrl dla kontrolki próbnej.")
            return 4
        handle = int(control.GetHandle())
        user32.SendMessageW(handle, WM_KEYDOWN, VK_SPACE, 1)
        user32.SendMessageW(handle, WM_KEYUP, VK_SPACE, 0xC0000001)
        app.Yield()
        after_add = _selected_indexes(control)

        user32.SendMessageW(handle, WM_KEYDOWN, VK_SPACE, 1)
        user32.SendMessageW(handle, WM_KEYUP, VK_SPACE, 0xC0000001)
        app.Yield()
        after_remove = _selected_indexes(control)
    finally:
        user32.SetKeyboardState(original)
        frame.Destroy()
        app.Yield()

    if after_add != [0, 2] or after_remove != [0]:
        print(
            "Ctrl+Spacja nie przełączyło nieprzylegającego zaznaczenia: "
            f"po dodaniu {after_add}, po usunięciu {after_remove}."
        )
        return 1
    print("Ctrl+Spacja: natywne zaznaczenie nieprzylegające działa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
