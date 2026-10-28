"""Mały wspólny kanał komunikatów z aktywnych okien podrzędnych wx.

Zmiana samej etykiety ``StaticText`` nie wywołuje wypowiedzi NVDA.  Okna
modalne i lekkie okna relacji nie mogą też korzystać z announcera głównej
ramki, bo podczas ich działania ramka jest nieaktywna. Ten moduł ustawia
świadomie przygotowaną nazwę użytkową i wysyła dokładnie jedno zdarzenie
regionu aktywnego dla kontrolki należącej do bieżącego okna.
"""

from __future__ import annotations

from collections.abc import Callable

from . import i18n


EVENT_OBJECT_LIVEREGIONCHANGED = 0x8019
OBJID_CLIENT = -4
CHILDID_SELF = 0


def _notify_win_event(event: int, hwnd: int, object_id: int, child_id: int) -> None:
    import ctypes

    ctypes.windll.user32.NotifyWinEvent(event, hwnd, object_id, child_id)


def announce_status(
    control,
    message: str,
    *,
    notify: Callable[[int, int, int, int], None] = _notify_win_event,
) -> str:
    """Pokaż i wypowiedz jeden komunikat w aktywnym oknie podrzędnym."""

    text = i18n.ui_text((message or "").strip())
    if not text:
        return ""
    if control.GetLabel() != text:
        control.SetLabel(text)
    control.SetName(text)
    try:
        notify(
            EVENT_OBJECT_LIVEREGIONCHANGED,
            int(control.GetHandle()),
            OBJID_CLIENT,
            CHILDID_SELF,
        )
    except OSError:
        # Komunikat jest dodatkiem do wykonanej czynności. Tekst pozostaje
        # dostępny nawet wtedy, gdy Windows chwilowo odrzuci zdarzenie MSAA.
        pass
    return text
