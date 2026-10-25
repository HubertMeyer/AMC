"""Windows probe: modeless account management must not disable AMC."""

from __future__ import annotations

import wx

from amc_wx_lite.gui import SonosAccountDialog


def main() -> int:
    app = wx.App(False)
    parent = wx.Frame(None, title="AMC modeless probe", pos=(-30000, -30000))
    parent.Show()
    dialog = SonosAccountDialog(
        parent,
        {
            "message": "Konto Sonos nie jest połączone.",
            "canLogin": True,
            "connected": False,
            "awaitingBrowser": False,
        },
        run_action=lambda _action, _dialog: None,
        copy_address=lambda _address: True,
    )
    dialog.SetPosition((-30000, -30000))
    dialog.Show()
    dialog.Raise()
    dialog.focus_primary_action()
    wx.Yield()
    wx.Yield()
    try:
        if not parent.IsEnabled():
            print("PARENT_DISABLED")
            return 2
        if not dialog.IsShown():
            print("ACCOUNT_WINDOW_HIDDEN")
            return 3
        if wx.Window.FindFocus() is not dialog.login_button:
            focused = wx.Window.FindFocus()
            print(f"WRONG_FOCUS:{focused.GetName() if focused else 'NONE'}")
            return 4
        print("MODELLESS_OK")
        return 0
    finally:
        dialog.Destroy()
        parent.Destroy()
        wx.Yield()
        del app


if __name__ == "__main__":
    raise SystemExit(main())
