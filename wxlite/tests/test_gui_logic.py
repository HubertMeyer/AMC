"""Testy czystej logiki z gui.py BEZ pulpitu.

wx nie jest w WSL dostepne (i nie wolno tu zaklada GUI), a mimo to dwie rzeczy
z okna MUSZA byc sprawdzone maszynowo: tlumaczenie zdarzenia klawisza na akord
oraz formatowanie czasu czytane przez czytnik ekranu. Podstawiamy minimalny
zastepnik modulu ``wx`` z samymi stalymi, ktorych te funkcje uzywaja.

Testu samego OKNA tu nie ma - okno wymaga pulpitu Windows i odbierze je rodzic.
"""

from __future__ import annotations

import sys
import types


def install_wx_stub() -> None:
    """Minimalny zastepnik wx: tylko kody klawiszy i atrapy klas bazowych."""
    if "wx" in sys.modules and getattr(sys.modules["wx"], "_amc_stub", False):
        return

    wx = types.ModuleType("wx")
    wx._amc_stub = True  # type: ignore[attr-defined]

    codes = {
        "WXK_RETURN": 13, "WXK_NUMPAD_ENTER": 370, "WXK_BACK": 8, "WXK_ESCAPE": 27,
        "WXK_SPACE": 32, "WXK_DELETE": 127, "WXK_F1": 340, "WXK_F2": 341, "WXK_F6": 345,
        "WXK_F10": 349,
        "WXK_LEFT": 314, "WXK_RIGHT": 316, "WXK_UP": 315, "WXK_DOWN": 317, "WXK_TAB": 9,
        "WXK_HOME": 313, "WXK_END": 312, "WXK_PAGEUP": 366, "WXK_PAGEDOWN": 367,
    }
    for name, value in codes.items():
        setattr(wx, name, value)

    # Stale uzywane przy budowie okna (nie wykonujemy go, ale import ich dotyka).
    for name in (
        "LC_REPORT", "LC_VIRTUAL", "LC_SINGLE_SEL", "BORDER_SUNKEN", "ID_ANY", "ID_EXIT",
        # OK/CANCEL/YES NIE sa tu atrapami -- maja liczby, patrz nizej.
        "ID_HELP", "ID_OK", "ID_CANCEL", "YES_NO", "NO_DEFAULT",
        "ICON_QUESTION", "ICON_INFORMATION", "ICON_WARNING",
        # Flagi ukladu i przyciskow maja LICZBY (patrz nizej), nie atrapy.
        "SL_HORIZONTAL", "SL_LABELS", "FONTWEIGHT_BOLD", "DD_DIR_MUST_EXIST",
        "FD_OPEN", "FD_FILE_MUST_EXIST", "EVT_TIMER", "EVT_CLOSE", "EVT_KEY_DOWN",
        "EVT_CHAR_HOOK", "EVT_CONTEXT_MENU",
        "EVT_HOTKEY",
        "EVT_LIST_ITEM_ACTIVATED", "EVT_LIST_ITEM_FOCUSED", "EVT_LIST_ITEM_SELECTED",
        "EVT_LIST_ITEM_DESELECTED",
        "EVT_BUTTON", "EVT_SLIDER", "EVT_CHOICE",
        "EVT_MENU", "ITEM_NORMAL", "ITEM_CHECK", "ITEM_RADIO", "ID_OPEN", "ID_COPY",
        "ID_PREFERENCES", "ID_ABOUT", "ACCEL_CTRL", "ACCEL_SHIFT", "ACCEL_ALT",
        "ACCEL_NORMAL",
    ):
        setattr(wx, name, object())

    # Bity stanu ListCtrl: nasz kod sklada z nich maske dla ``SetItemState``,
    # wiec musza byc LICZBAMI, nie atrapami. Wartosci ODCZYTANE z naglowka
    # wxWidgets ``include/wx/listbase.h`` (nie z pamieci):
    #   #define wxLIST_STATE_FOCUSED   0x0002
    #   #define wxLIST_STATE_SELECTED  0x0004
    wx.LIST_STATE_FOCUSED = 0x0002  # type: ignore[attr-defined]
    wx.LIST_STATE_SELECTED = 0x0004  # type: ignore[attr-defined]

    # Flagi przyciskow dialogu. Nasz kod sklada z nich maske (``wx.OK |
    # wx.CANCEL``) dla ``CreateStdDialogButtonSizer``, wiec MUSZA byc
    # liczbami -- atrapa ``object()`` wywala sie na operatorze ``|``.
    #
    # Wartosci ODCZYTANE z naglowka wxWidgets ``include/wx/defs.h``
    # (nie z pamieci):
    #   #define wxYES     0x00000002
    #   #define wxOK      0x00000004
    #   #define wxNO      0x00000008
    #   #define wxCANCEL  0x00000010
    wx.YES = 0x0002  # type: ignore[attr-defined]
    wx.OK = 0x0004  # type: ignore[attr-defined]
    wx.NO = 0x0008  # type: ignore[attr-defined]
    wx.CANCEL = 0x0010  # type: ignore[attr-defined]
    wx.YES_NO = wx.YES | wx.NO  # type: ignore[attr-defined]
    wx.NO_DEFAULT = 0x0080  # type: ignore[attr-defined]
    wx.ICON_WARNING = 0x0100  # type: ignore[attr-defined]
    wx.MOD_CONTROL = 0x0002  # type: ignore[attr-defined]
    wx.MOD_SHIFT = 0x0004  # type: ignore[attr-defined]

    # Flagi ukladu sizerow. Tez skladane operatorem ``|`` (``wx.ALL |
    # wx.EXPAND``), wiec musza byc liczbami. Wartosci ODCZYTANE z
    # ``include/wx/defs.h`` (enum wxOrientation/wxDirection/wxAlignment/
    # wxStretch), nie z pamieci:
    #   wxHORIZONTAL 0x0004, wxVERTICAL 0x0008
    #   wxLEFT 0x0010, wxRIGHT 0x0020, wxUP 0x0040, wxDOWN 0x0080
    #   wxALL = wxUP|wxDOWN|wxRIGHT|wxLEFT = 0x00F0
    #   wxALIGN_RIGHT 0x0200, wxALIGN_CENTER_VERTICAL 0x0800
    #   wxGROW 0x2000, wxEXPAND = wxGROW
    wx.HORIZONTAL = 0x0004  # type: ignore[attr-defined]
    wx.VERTICAL = 0x0008  # type: ignore[attr-defined]
    wx.LEFT = 0x0010  # type: ignore[attr-defined]
    wx.RIGHT = 0x0020  # type: ignore[attr-defined]
    wx.TOP = 0x0040  # type: ignore[attr-defined]
    wx.BOTTOM = 0x0080  # type: ignore[attr-defined]
    wx.ALL = 0x00F0  # type: ignore[attr-defined]
    wx.ALIGN_RIGHT = 0x0200  # type: ignore[attr-defined]
    wx.ALIGN_CENTER_VERTICAL = 0x0800  # type: ignore[attr-defined]
    wx.EXPAND = 0x2000  # type: ignore[attr-defined]

    class _Any:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __getattr__(self, name):
            return _Any()

        def __call__(self, *args, **kwargs):
            return _Any()

    for name in (
        "Frame", "Panel", "App", "Dialog", "ListCtrl", "StaticText", "TextCtrl", "Button",
        "Slider", "Choice", "BoxSizer", "FlexGridSizer", "Timer", "MenuBar", "Menu", "KeyEvent",
        "ListEvent", "CommandEvent", "TimerEvent", "CloseEvent", "DirDialog", "FileDialog",
        "Window",
    ):
        setattr(wx, name, _Any)

    wx.CallAfter = lambda fn, *a, **k: fn(*a, **k)  # type: ignore[attr-defined]
    wx.MessageBox = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules["wx"] = wx


install_wx_stub()

from amc_wx_lite.gui import (  # noqa: E402
    CLIPBOARD_COMMAND_DELAY_MS,
    LiteFrame,
    YOUTUBE_EXPORT_WILDCARD,
    _WindowsPreset10HotKey,
    chord_from_event,
    defer_clipboard_command,
    format_time,
    relation_destination_labels,
    session_selection_labels,
    youtube_export_path_for_filter,
)
from amc_wx_lite.shortcuts import Action, Chord, resolve  # noqa: E402
from amc_wx_lite.navigation import LibraryView, Navigator, SessionId, View  # noqa: E402


class FakeKeyEvent:
    """Zdarzenie klawisza o tym samym interfejsie, ktorego uzywa okno."""

    def __init__(
        self,
        code: int,
        ctrl: bool = False,
        shift: bool = False,
        alt: bool = False,
        *,
        raw_code: int | None = None,
    ) -> None:
        self._code = code
        self._raw_code = code if raw_code is None else raw_code
        self._ctrl = ctrl
        self._shift = shift
        self._alt = alt

    def GetKeyCode(self) -> int:  # noqa: N802 - API wx
        return self._code

    def GetRawKeyCode(self) -> int:  # noqa: N802 - API wx
        return self._raw_code

    def ControlDown(self) -> bool:  # noqa: N802
        return self._ctrl

    def ShiftDown(self) -> bool:  # noqa: N802
        return self._shift

    def AltDown(self) -> bool:  # noqa: N802
        return self._alt


def test_youtube_export_format_is_explicit_and_follows_selected_file_type() -> None:
    assert "NewPipe" in YOUTUBE_EXPORT_WILDCARD
    assert "FreeTube" in YOUTUBE_EXPORT_WILDCARD
    assert "CSV kanałów" in YOUTUBE_EXPORT_WILDCARD
    assert "czytników RSS" in YOUTUBE_EXPORT_WILDCARD
    assert youtube_export_path_for_filter("Kanaly YouTube AMC.csv", 1).endswith(".opml")
    assert youtube_export_path_for_filter("Kanaly YouTube AMC.opml", 0).endswith(".csv")


# ------------------------------------------------- klawisz -> akord -> akcja


def test_enter_from_both_keyboards_activates() -> None:
    import wx

    for code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
        chord = chord_from_event(FakeKeyEvent(code))
        assert resolve(chord, player_view=False, radio_session=False) is Action.ACTIVATE


def test_session_list_labels_are_explicit_and_never_expose_model_values() -> None:
    labels = session_selection_labels()
    assert labels == (
        "Ctrl+1, Pliki lokalne",
        "Ctrl+2, Radio internetowe",
        "Ctrl+3, Podcasty i YouTube",
        "Ctrl+4, TIDAL",
        "Ctrl+5, WiiM",
        "Ctrl+6, Sonos",
        "Ctrl+7, Spotify",
    )
    assert all("SessionId" not in label and "{" not in label for label in labels)


def test_letter_keys_are_upper_cased_so_ctrl_o_matches() -> None:
    """Ctrl+O to PLIKI, tak jak w oryginale (MainWindow.xaml:42-45).

    Ten test dlugo wymagal odwrotnie (folder) i dlatego utrwalal blad, ktory
    Michal zglosil: ``OpenLocalFilesMenuItem`` ma ``InputGestureText="Ctrl+O"``.
    """
    chord = chord_from_event(FakeKeyEvent(ord("o"), ctrl=True))
    assert chord.canonical == "Ctrl+O"
    assert resolve(chord, player_view=False, radio_session=False) is Action.OPEN_FILE_DIALOG


def test_ctrl_shift_o_opens_a_folder() -> None:
    """Ctrl+Shift+O to FOLDER (MainWindow.xaml:46-49, OpenLocalFolderMenuItem)."""
    chord = chord_from_event(FakeKeyEvent(ord("O"), ctrl=True, shift=True))
    assert chord.canonical == "Ctrl+Shift+O"
    assert resolve(chord, player_view=False, radio_session=False) is Action.OPEN_FOLDER_DIALOG


def test_digit_keys_switch_sessions() -> None:
    chord = chord_from_event(FakeKeyEvent(ord("1"), ctrl=True))
    assert resolve(chord, player_view=False, radio_session=False) is Action.SESSION_FILES


def test_ctrl_shift_zero_uses_physical_windows_key_for_preset_10(monkeypatch) -> None:
    """MSW CHAR_HOOK may expose Shift+0 as ``)`` instead of physical zero."""

    monkeypatch.setattr(
        "amc_wx_lite.gui._windows_virtual_key_down",
        lambda _virtual_key: False,
    )
    chord = chord_from_event(FakeKeyEvent(
        ord(")"),
        ctrl=True,
        shift=True,
        raw_code=0x30,
    ))
    assert chord.canonical == "Ctrl+Shift+0"
    assert resolve(chord, player_view=False, radio_session=False) is Action.PRESET_10


def test_ctrl_shift_zero_recovers_modifier_omitted_by_wx(monkeypatch) -> None:
    """Stare AMC też musiało dopełniać modyfikatory stanem klawiatury Win32."""

    monkeypatch.setattr(
        "amc_wx_lite.gui._windows_virtual_key_down",
        lambda virtual_key: virtual_key in (0x11, 0x10),
    )
    chord = chord_from_event(FakeKeyEvent(
        0,
        raw_code=0x30,
    ))
    assert chord.canonical == "Ctrl+Shift+0"
    assert resolve(chord, player_view=True, radio_session=False) is Action.PRESET_10


def test_ctrl_shift_zero_is_global_in_every_session_and_view() -> None:
    chord = Chord(key="0", ctrl=True, shift=True)
    session_flags = (
        {},
        {"radio_session": True},
        {"podcast_session": True},
        {"tidal_session": True},
        {"spotify_session": True},
        {"wiim_session": True},
        {"sonos_session": True},
    )

    for player_view in (False, True):
        for flags in session_flags:
            assert resolve(
                chord,
                player_view=player_view,
                radio_session=flags.get("radio_session", False),
                podcast_session=flags.get("podcast_session", False),
                tidal_session=flags.get("tidal_session", False),
                spotify_session=flags.get("spotify_session", False),
                wiim_session=flags.get("wiim_session", False),
                sonos_session=flags.get("sonos_session", False),
            ) is Action.PRESET_10


def test_raw_zero_does_not_rewrite_ordinary_shift_zero(monkeypatch) -> None:
    monkeypatch.setattr(
        "amc_wx_lite.gui._windows_virtual_key_down",
        lambda _virtual_key: False,
    )
    chord = chord_from_event(FakeKeyEvent(
        ord(")"),
        shift=True,
        raw_code=0x30,
    ))
    assert chord.canonical == "Shift+)"


def test_native_keyboard_boundary_recognizes_only_first_ctrl_shift_zero() -> None:
    from amc_wx_lite.gui import _native_preset_10_keydown

    assert _native_preset_10_keydown(
        0, 0x30, 0, ctrl_down=True, shift_down=True, alt_down=False
    )
    for virtual_key, flags, ctrl, shift, alt in (
        (0x39, 0, True, True, False),
        (0x30, 1 << 30, True, True, False),
        (0x30, 1 << 31, True, True, False),
        (0x30, 0, False, True, False),
        (0x30, 0, True, False, False),
        (0x30, 0, True, True, True),
    ):
        assert not _native_preset_10_keydown(
            0,
            virtual_key,
            flags,
            ctrl_down=ctrl,
            shift_down=shift,
            alt_down=alt,
        )


def test_foreground_hotkey_registers_physical_ctrl_shift_zero(monkeypatch) -> None:
    calls = []

    class Owner:
        filter_box = object()
        _keyboard_help_active = False

        def Bind(self, event_type, handler, *, id):
            calls.append(("bind", event_type, id))
            self.handler = handler

        def RegisterHotKey(self, id, modifiers, virtual_key):
            calls.append(("register", id, modifiers, virtual_key))
            return True

        def UnregisterHotKey(self, id):
            calls.append(("unregister", id))

        def _activate_preset(self, slot):
            calls.append(("preset", slot))

    owner = Owner()
    monkeypatch.setattr("amc_wx_lite.gui.os.name", "nt")
    monkeypatch.setattr(
        "amc_wx_lite.gui.wx.Window.FindFocus",
        lambda: object(),
        raising=False,
    )
    hotkey = _WindowsPreset10HotKey(owner)

    assert hotkey.register()
    assert ("register", hotkey._ID, 0x0002 | 0x0004 | 0x4000, 0x30) in calls
    owner.handler(None)
    assert ("preset", 10) in calls
    hotkey.unregister()
    assert ("unregister", hotkey._ID) in calls


def test_amc_copy_waits_past_nvda_global_clipboard_probe(monkeypatch) -> None:
    scheduled = []
    completed = []
    monkeypatch.setattr(
        "amc_wx_lite.gui.wx.CallLater",
        lambda delay, callback: scheduled.append((delay, callback)),
        raising=False,
    )

    defer_clipboard_command(lambda: completed.append("copy"))

    assert CLIPBOARD_COMMAND_DELAY_MS > 100
    assert scheduled[0][0] == CLIPBOARD_COMMAND_DELAY_MS
    assert completed == []
    scheduled[0][1]()
    assert completed == ["copy"]


def test_relation_destinations_use_natural_short_labels_unless_details_enabled() -> None:
    labels = (
        "Przejdź do albumu",
        "Przejdź do wykonawcy",
        "Przejdź do podcastu",
        "Pokaż albumy wykonawcy",
        "Pokaż utwory wykonawcy",
    )

    assert relation_destination_labels(labels, detailed_hints=False) == (
        "Album",
        "Wykonawca",
        "Podcasty",
        "Albumy",
        "Utwory",
    )
    assert relation_destination_labels(labels, detailed_hints=True) == labels


def test_shift_f10_opens_the_list_context_menu_without_running_a_list_action() -> None:
    import wx

    calls: list[tuple[object, bool]] = []
    control = types.SimpleNamespace()
    frame = object.__new__(LiteFrame)
    frame._active_list = lambda: control
    frame._show_context_menu = lambda target, *, player: calls.append(
        (target, player)
    )

    frame._on_list_shortcut_hook(FakeKeyEvent(wx.WXK_F10, shift=True))

    assert calls == [(control, False)]


def test_native_context_event_is_bound_to_every_media_list() -> None:
    import wx

    bindings: list[tuple[object, object]] = []
    control = types.SimpleNamespace(
        Bind=lambda event_type, handler: bindings.append((event_type, handler))
    )
    frame = object.__new__(LiteFrame)

    frame._bind_list(control)

    assert (wx.EVT_CONTEXT_MENU, frame._on_list_context_menu) in bindings


def test_context_menu_reuses_only_enabled_user_facing_menu_entries() -> None:
    from amc_wx_lite import menu_model

    class Native:
        def __init__(self, label: str, *, enabled: bool) -> None:
            self.label = label
            self.enabled = enabled

        def IsEnabled(self):  # noqa: N802 - wx API
            return self.enabled

        def GetItemLabel(self):  # noqa: N802 - wx API
            return self.label

    frame = object.__new__(LiteFrame)
    frame.navigator = types.SimpleNamespace(
        active=SessionId.FILES,
        session=types.SimpleNamespace(
            model=types.SimpleNamespace(selected_row=object()),
        ),
    )
    frame._refresh_menu_state = lambda: None
    frame._menu_items = [
        (
            Native("&Otwórz zaznaczone\tEnter", enabled=True),
            menu_model.MenuItem(
                "&Otwórz zaznaczone",
                Action.ACTIVATE,
                shortcut="Return",
            ),
        ),
        (
            Native("&Skopiuj nazwę (Ctrl+C)", enabled=True),
            menu_model.MenuItem("&Skopiuj nazwę", Action.COPY_NAME),
        ),
        (
            Native("Zmień nazwę w Bibliote&ce (F2)", enabled=False),
            menu_model.MenuItem(
                "Zmień nazwę w Bibliote&ce",
                Action.RENAME_LIBRARY_ITEM,
            ),
        ),
    ]

    groups = frame._context_menu_command_groups(player=False)
    commands = [command for group in groups for command in group]

    assert [command.action for command in commands] == [
        Action.ACTIVATE,
        Action.COPY_NAME,
    ]
    assert [command.label for command in commands] == [
        "&Otwórz zaznaczone\tEnter",
        "&Skopiuj nazwę (Ctrl+C)",
    ]
    assert all("Action." not in command.label for command in commands)


def test_spotify_context_relation_exposes_only_the_intentional_podcast_label() -> None:
    row = types.SimpleNamespace(
        kind="episode",
        item_id="episode-row",
        related_podcast_service_id="spotify:show:private-id",
        related_podcast_title="Podcast użytkowy",
    )
    frame = object.__new__(LiteFrame)
    frame.navigator = types.SimpleNamespace(
        active=SessionId.SPOTIFY,
        session=types.SimpleNamespace(
            model=types.SimpleNamespace(selected_row=row),
        ),
        _spotify_relation_choices=Navigator._spotify_relation_choices,
    )

    commands = frame._relation_context_menu_commands()

    assert [command.label for command in commands] == [
        "Przejdź do Podcast użytkowy"
    ]
    assert all("private-id" not in command.label for command in commands)


def test_native_context_popup_dispatches_once_and_restores_list_focus() -> None:
    from amc_wx_lite import gui

    handlers: dict[int, object] = {}
    labels: list[str] = []
    invoked: list[object] = []

    class Item:
        def __init__(self, identifier: int) -> None:
            self.identifier = identifier

        def GetId(self):  # noqa: N802 - wx API
            return self.identifier

        def Check(self, _checked):  # noqa: N802 - wx API
            pass

    class Menu:
        def __init__(self) -> None:
            self.identifiers: list[int] = []
            self.destroyed = False

        def Append(self, _identifier, label):  # noqa: N802 - wx API
            labels.append(label)
            item = Item(7000 + len(self.identifiers))
            self.identifiers.append(item.identifier)
            return item

        def AppendCheckItem(self, identifier, label):  # noqa: N802 - wx API
            return self.Append(identifier, label)

        def AppendSeparator(self):  # noqa: N802 - wx API
            labels.append("---")

        def Destroy(self):  # noqa: N802 - wx API
            self.destroyed = True

    class Control:
        focused = 0

        def PopupMenu(self, menu, *_position):  # noqa: N802 - wx API
            handlers[menu.identifiers[0]](None)

        def SetFocus(self):  # noqa: N802 - wx API
            self.focused += 1

    command = gui._ContextMenuCommand(
        label="&Skopiuj nazwę (Ctrl+C)",
        action=Action.COPY_NAME,
    )
    control = Control()
    frame = object.__new__(LiteFrame)
    frame.navigator = types.SimpleNamespace(view=View.LIST)
    frame.announcer = types.SimpleNamespace(say=lambda _text: None)
    frame._context_menu_command_groups = lambda *, player: ((command,),)
    frame._context_menu_position = lambda _control, _event: None
    frame._invoke_context_menu_command = invoked.append
    frame._active_list = lambda: control
    frame.Bind = lambda _event, handler, *, id: handlers.__setitem__(id, handler)
    frame.Unbind = lambda _event, *, id: handlers.pop(id, None) is not None

    original_menu = gui.wx.Menu
    gui.wx.Menu = Menu
    try:
        frame._show_context_menu(control, player=False)
    finally:
        gui.wx.Menu = original_menu

    assert labels == ["&Skopiuj nazwę (Ctrl+C)"]
    assert invoked == [command]
    assert control.focused == 1
    assert handlers == {}


def test_player_context_exposes_queue_navigation_with_readable_shortcuts() -> None:
    from amc_wx_lite import menu_model

    play_pause = next(
        item
        for menu in menu_model.menus_for_session(SessionId.SPOTIFY)
        for item in menu.items
        if item.action is Action.PLAY_PAUSE
    )

    class Native:
        def IsEnabled(self):  # noqa: N802 - wx API
            return True

        def GetItemLabel(self):  # noqa: N802 - wx API
            return "&Pauza albo wznowienie (Spacja)"

    frame = object.__new__(LiteFrame)
    frame.navigator = types.SimpleNamespace(
        active=SessionId.SPOTIFY,
        session=types.SimpleNamespace(
            model=types.SimpleNamespace(selected_row=None),
        ),
    )
    frame._menu_items = [(Native(), play_pause)]
    frame._refresh_menu_state = lambda: None
    frame._action_available_in_active_session = lambda _action: True

    groups = frame._context_menu_command_groups(player=True)
    labels = {
        command.action: command.label
        for group in groups
        for command in group
    }

    assert labels[Action.QUEUE_PREVIOUS] == "&Poprzedni utwór kolejki\tPage Up"
    assert labels[Action.QUEUE_NEXT] == "&Następny utwór kolejki\tPage Down"


def test_shift_f6_returns_to_the_list() -> None:
    import wx

    chord = chord_from_event(FakeKeyEvent(wx.WXK_F6, shift=True))
    assert chord.canonical == "Shift+F6"
    assert resolve(chord, player_view=True, radio_session=False) is Action.SHOW_LIST


def test_ctrl_f1_describes_keys_without_executing_them() -> None:
    import wx

    calls: list[str] = []
    frame = object.__new__(LiteFrame)
    frame._keyboard_help_active = False
    frame._refresh_menu_state = lambda: calls.append("menu")
    frame.announcer = types.SimpleNamespace(say=lambda text: calls.append(text))
    session = types.SimpleNamespace(library_view=LibraryView.ALL_FILES)
    frame.navigator = types.SimpleNamespace(
        view=View.LIST,
        active=SessionId.FILES,
        sessions={SessionId.FILES: session},
    )

    assert frame._handle_keyboard_help_event(
        FakeKeyEvent(wx.WXK_F1, ctrl=True)
    ) is True
    assert frame._keyboard_help_active is True
    assert "Pomoc klawiatury włączona" in calls[-1]

    # Ctrl+F zostaje tylko opisane: nie wywołujemy dispatchera ani okna
    # wyszukiwania. Jedynym skutkiem jest użytkowy komunikat w Announcerze.
    assert frame._handle_keyboard_help_event(
        FakeKeyEvent(ord("F"), ctrl=True)
    ) is True
    assert calls[-1] == (
        "Ctrl+F. Szukaj w bieżącej usłudze. Pliki lokalne"
    )
    assert frame._keyboard_help_active is True

    assert frame._handle_keyboard_help_event(
        FakeKeyEvent(wx.WXK_ESCAPE)
    ) is True
    assert frame._keyboard_help_active is False
    assert calls[-1] == "Pomoc klawiatury wyłączona"


def test_arrow_keys_on_the_list_are_left_to_the_control() -> None:
    import wx

    # LEWA ma wyjatek z oryginalu (krotka informacja, cs:23206-23216); pozostale
    # strzalki i Home/End nadal chodza po wierszach w samej kontrolce.
    for code in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_RIGHT, wx.WXK_HOME, wx.WXK_END):
        chord = chord_from_event(FakeKeyEvent(code))
        assert resolve(chord, player_view=False, radio_session=False) is None
    left = chord_from_event(FakeKeyEvent(wx.WXK_LEFT))
    assert resolve(left, player_view=False, radio_session=False) is Action.QUICK_INFORMATION


def test_unknown_key_never_resolves_to_an_action() -> None:
    chord = chord_from_event(FakeKeyEvent(9999))
    assert chord.key.startswith("#")
    assert resolve(chord, player_view=False, radio_session=False) is None
    assert resolve(chord, player_view=True, radio_session=False) is None


# ------------------------------------------------------------ czas po polsku


def test_time_is_spoken_short_and_in_polish() -> None:
    assert format_time(0) == "0 s"
    assert format_time(5) == "5 s"
    assert format_time(65) == "1 min 5 s"
    assert format_time(3725) == "1 godz 2 min 5 s"


def test_unknown_duration_is_named_not_shown_as_a_number() -> None:
    # Strumien radiowy nie ma dlugosci - czytnik ma powiedziec "nieznany",
    # nie "-1 s".
    assert format_time(None) == "nieznany"
    assert format_time(-1) == "nieznany"


def test_zaznaczenie_wiersza_odswieza_bramki_menu() -> None:
    """Regresja ZMIERZONA na zywym GUI (statusclip-2).

    Ctrl+Shift+C fizycznie dotarlo do okna (hook.key: keyCode 67, mods 6) i
    NIE wywolalo zadnej akcji, mimo ze na liscie byl zaznaczony plik.

    Przyczyna: ``needs_selection=True`` wylacza pozycje menu, dopoki nic nie
    jest zaznaczone, a ``_refresh_menu_state`` lecial TYLKO z ``_sync_views``
    (zmiana widoku/sesji). Zaznaczenie wiersza strzalka zmienia model, ale nie
    bylo zdarzeniem odswiezajacym menu -- wiec WYLACZONY akcelerator okna
    polykal klawisz, zamiast przepuscic go do listy.

    Ten test pilnuje SPRZEZENIA: po ``_on_item_selected`` stan menu musi byc
    przeliczony. Nie sprawdza samego ``Enable`` (to robi
    ``_refresh_menu_state``), tylko ze ktos go w ogole wola.
    """
    from amc_wx_lite import gui

    calls = []

    class Model:
        rows = [1]
        selected_index = 0
        selected_row = object()

        def select_id(self, item_id):
            calls.append(("select_id", item_id))

        def select_index(self, index):
            calls.append(("select_index", index))

    class Session:
        model = Model()

    class Nav:
        session = Session()

    frame = gui.LiteFrame.__new__(gui.LiteFrame)
    frame.navigator = Nav()
    frame._refresh_menu_state = lambda: calls.append(("refresh", None))

    class Ctrl(gui.MediaListCtrl):
        updating = False

        def __init__(self):
            pass

        def shown_item_id(self, index):
            return "i1"

    class Event:
        def GetEventObject(self):
            return ctrl

        def GetIndex(self):
            return 0

        def Skip(self):
            pass

    ctrl = Ctrl()
    frame._on_item_selected(Event())

    assert ("refresh", None) in calls, (
        "zaznaczenie wiersza nie przeliczylo stanu menu; wylaczony akcelerator "
        f"nadal polykalby Ctrl+Shift+C (wywolania: {calls})")


def test_shift_space_menu_names_and_marks_the_actual_recording_state() -> None:
    """Shift+Spacja ma byc jednym stanowym poleceniem, nie trzema wpisami.

    NVDA musi uslyszec aktualna czynnosc: przy trwajacym nagraniu
    ``Wstrzymaj``, przy wstrzymanym ``Wznow``. Zaznaczenie pozycji oznacza
    stan wstrzymany. Bez nagrania polecenie pozostaje niedostepne i nie
    sugeruje, ze cos aktualnie nagrywamy.
    """
    from amc_wx_lite import menu_model

    entry = next(
        item
        for menu in menu_model.build_menus()
        for item in menu.items
        if item.action is Action.RECORD_PAUSE
    )

    class FakeMenuItem:
        def __init__(self) -> None:
            self.enabled = True
            self.checked = False
            self.label = ""

        def IsEnabled(self):  # noqa: N802 - API wx
            return self.enabled

        def Enable(self, value):  # noqa: N802 - API wx
            self.enabled = value

        def Check(self, value):  # noqa: N802 - API wx
            self.checked = value

        def GetItemLabel(self):  # noqa: N802 - API wx
            return self.label

        def SetItemLabel(self, value):  # noqa: N802 - API wx
            self.label = value

    selected = types.SimpleNamespace(
        kind="station",
        item_id="radio-poznan",
        url="https://example.test/radio",
    )
    session = types.SimpleNamespace(
        view=View.LIST,
        library_view=LibraryView.ALL_FILES,
        library_playlist_id=None,
        model=types.SimpleNamespace(selected_row=selected),
    )
    frame = object.__new__(LiteFrame)
    frame.navigator = types.SimpleNamespace(
        active=SessionId.RADIO,
        sessions={SessionId.RADIO: session},
    )
    frame._last_status = {}
    frame._podcast_inbox_sort_mode = ""
    frame._tidal_effective_sort_modes = {}
    frame.options = types.SimpleNamespace(
        radio_recognition_monitoring=False,
        radio_recognition_announcements=False,
    )
    frame._keyboard_help_active = False

    menu_item = FakeMenuItem()
    frame._menu_items = [(menu_item, entry)]

    frame._last_recording_status = {
        "recordings": [{"stationId": "radio-poznan", "paused": False}]
    }
    frame._refresh_menu_state()
    assert menu_item.enabled is True
    assert menu_item.checked is False
    assert menu_item.label.startswith("&Wstrzymaj nagrywanie")

    frame._last_recording_status = {
        "recordings": [{"stationId": "radio-poznan", "state": "paused"}]
    }
    frame._refresh_menu_state()
    assert menu_item.enabled is True
    assert menu_item.checked is True
    assert menu_item.label.startswith("&Wznów nagrywanie")

    frame._last_recording_status = {"recordings": []}
    frame._refresh_menu_state()
    assert menu_item.enabled is False
    assert menu_item.checked is False
    assert menu_item.label.startswith("&Wstrzymaj albo wznów nagrywanie")


def test_mute_menu_names_and_marks_the_active_session_state() -> None:
    """Ctrl+M ma opisywac stan aktywnej sesji, bez technicznych etykiet."""
    from amc_wx_lite import menu_model

    entry = next(
        item
        for menu in menu_model.build_menus()
        for item in menu.items
        if item.action is Action.TOGGLE_MUTE
    )

    class FakeMenuItem:
        def __init__(self) -> None:
            self.enabled = True
            self.checked = False
            self.label = ""

        def IsEnabled(self):  # noqa: N802 - API wx
            return self.enabled

        def Enable(self, value):  # noqa: N802 - API wx
            self.enabled = value

        def Check(self, value):  # noqa: N802 - API wx
            self.checked = value

        def GetItemLabel(self):  # noqa: N802 - API wx
            return self.label

        def SetItemLabel(self, value):  # noqa: N802 - API wx
            self.label = value

    session = types.SimpleNamespace(
        view=View.LIST,
        library_view=LibraryView.ALL_FILES,
        library_playlist_id=None,
        model=types.SimpleNamespace(selected_row=None),
    )
    frame = object.__new__(LiteFrame)
    frame.navigator = types.SimpleNamespace(
        active=SessionId.FILES,
        sessions={SessionId.FILES: session},
    )
    frame._last_status = {"engine": "media"}
    frame._last_recording_status = {"recordings": []}
    frame._podcast_inbox_sort_mode = ""
    frame._tidal_effective_sort_modes = {}
    frame.options = types.SimpleNamespace(
        radio_recognition_monitoring=False,
        radio_recognition_announcements=False,
    )
    frame._keyboard_help_active = False

    menu_item = FakeMenuItem()
    frame._menu_items = [(menu_item, entry)]
    frame._transport_status_by_session = {
        SessionId.FILES: {"muted": False},
    }

    frame._refresh_menu_state()
    assert menu_item.enabled is True
    assert menu_item.checked is False
    assert menu_item.label.startswith("Wycisz bieżącą sesję")

    frame._transport_status_by_session[SessionId.FILES]["muted"] = True
    frame._refresh_menu_state()
    assert menu_item.enabled is True
    assert menu_item.checked is True
    assert menu_item.label.startswith("Włącz dźwięk bieżącej sesji")


def test_membership_menu_gates_follow_the_selected_user_facing_item() -> None:
    """Menu nie oferuje operacji, którą wykonawca zaraz musiałby odrzucić."""
    from amc_wx_lite import menu_model

    entries = {
        action: next(
            item
            for menu in menu_model.build_menus()
            for item in menu.items
            if item.action is action
        )
        for action in (
            Action.ADD_TO_QUEUE,
            Action.TOGGLE_PLAY_NEXT,
            Action.TOGGLE_PODCAST_LIBRARY,
            Action.TIDAL_TOGGLE_LIBRARY,
            Action.SPOTIFY_TOGGLE_LIBRARY,
        )
    }

    class FakeMenuItem:
        def __init__(self) -> None:
            self.enabled = True

        def IsEnabled(self):  # noqa: N802 - API wx
            return self.enabled

        def Enable(self, value):  # noqa: N802 - API wx
            self.enabled = value

    def enabled(action: Action, active: SessionId, **row_values: object) -> bool:
        defaults = {
            "kind": "",
            "item_id": "item",
            "url": "",
            "parent_id": "",
            "service_id": "",
            "related_album_service_id": "",
        }
        defaults.update(row_values)
        row = types.SimpleNamespace(**defaults)
        view = {
            SessionId.PODCASTS: LibraryView.PODCAST_LIBRARY,
            SessionId.TIDAL: LibraryView.TIDAL_LIBRARY,
            SessionId.SPOTIFY: LibraryView.SPOTIFY_LIBRARY,
        }.get(active, LibraryView.ALL_FILES)
        session = types.SimpleNamespace(
            view=View.LIST,
            library_view=view,
            library_playlist_id=None,
            model=types.SimpleNamespace(selected_row=row),
            spotify_context=None,
        )
        frame = object.__new__(LiteFrame)
        frame.navigator = types.SimpleNamespace(
            active=active,
            sessions={active: session},
        )
        frame._last_status = {}
        frame._last_recording_status = {"recordings": []}
        frame._transport_status_by_session = {}
        frame._podcast_inbox_sort_mode = ""
        frame._tidal_effective_sort_modes = {}
        frame._keyboard_help_active = False
        native = FakeMenuItem()
        frame._menu_items = [(native, entries[action])]
        frame._refresh_menu_state()
        return native.enabled

    assert enabled(Action.ADD_TO_QUEUE, SessionId.FILES, kind="track")
    assert enabled(Action.TOGGLE_PLAY_NEXT, SessionId.FILES, kind="track")
    assert enabled(
        Action.ADD_TO_QUEUE,
        SessionId.PODCASTS,
        kind="episode",
        parent_id="podcast",
    )
    assert enabled(
        Action.TOGGLE_PODCAST_LIBRARY,
        SessionId.PODCASTS,
        kind="episode",
        parent_id="podcast",
    )
    assert not enabled(
        Action.TOGGLE_PODCAST_LIBRARY,
        SessionId.PODCASTS,
        kind="episode",
    )
    assert enabled(
        Action.ADD_TO_QUEUE,
        SessionId.TIDAL,
        kind="track",
        service_id="tidal-track",
        related_album_service_id="tidal-album",
    )
    assert not enabled(
        Action.ADD_TO_QUEUE,
        SessionId.TIDAL,
        kind="track",
        service_id="tidal-track",
    )
    assert enabled(
        Action.TIDAL_TOGGLE_LIBRARY,
        SessionId.TIDAL,
        kind="album",
        service_id="tidal-album",
    )
    assert not enabled(
        Action.TIDAL_TOGGLE_LIBRARY,
        SessionId.TIDAL,
        kind="track",
        service_id="tidal-track",
        related_album_service_id="tidal-album",
    )
    assert enabled(
        Action.SPOTIFY_TOGGLE_LIBRARY,
        SessionId.SPOTIFY,
        kind="album",
        service_id="spotify-album",
    )
    assert enabled(
        Action.SPOTIFY_TOGGLE_LIBRARY,
        SessionId.SPOTIFY,
        kind="episode",
        service_id="spotify-episode",
    )
    assert not enabled(
        Action.SPOTIFY_TOGGLE_LIBRARY,
        SessionId.SPOTIFY,
        kind="track",
        service_id="spotify-track",
    )
