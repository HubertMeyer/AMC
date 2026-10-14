"""Guard early player shortcuts; native Win32 processing eats KEY_DOWN first.

The real RED was measured on a wx.Button with NVDA and keybd_event:
Right moved focus to volume and Ctrl+E stayed silent. AST extraction tests the
small method without importing wx on Linux; the live cycle is still required.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

SOURCE = Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"

def _call(*, player=True, arrow=True, foreign=False, time_key=False,
          in_filter=False, list_chord="Tab", session="files"):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    methods: list[ast.stmt] = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
               and n.name == "_on_player_shortcut_hook"]
    assert len(methods) == 1, "early player arrow hook is missing"
    view = SimpleNamespace(PLAYER=object(), LIST=object())
    actions = []
    # Pole filtra MUSI byc w atrapie, bo hook bramkuje je PRZED reszta logiki
    # (gui.py, bramka ``FindFocus() is self.filter_box``). Atrapa bez tego pola
    # nie mierzyla zachowania, tylko wywalala sie na AttributeError.
    filter_box = SimpleNamespace(owner=None)
    frame = SimpleNamespace(navigator=SimpleNamespace(
                                view=view.PLAYER if player else view.LIST,
                                active=SimpleNamespace(value=session),
                                session=SimpleNamespace(library_view=None)),
                            filter_box=filter_box,
                            _on_filter_key=lambda event, *a, **k: actions.append("filter"),
                            _on_key=lambda event, *a, **k: actions.append("key" if arrow or time_key else "skip"))
    filter_box.owner = frame
    focus = filter_box if in_filter else SimpleNamespace(owner=object() if foreign else frame)
    wx = SimpleNamespace(KeyEvent=object, WXK_LEFT=1, WXK_RIGHT=2, WXK_UP=3, WXK_DOWN=4,
                         Window=SimpleNamespace(FindFocus=lambda: focus),
                         GetTopLevelParent=lambda focus: focus.owner)
    event = SimpleNamespace(GetKeyCode=lambda: 69 if time_key else 2 if arrow else 9,
                            Skip=lambda: actions.append("skip"))
    ns: dict[str, Any] = {
        "wx": wx,
        "View": view,
        "chord_from_event": lambda _event: SimpleNamespace(canonical=list_chord),
    }
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(SOURCE), "exec"), ns)
    ns["_on_player_shortcut_hook"](frame, event)
    return actions

def test_strzalka_odtwarzacza_przechodzi_raz_przed_nawigacja_dialogu():
    assert _call() == ["key"]

def test_ctrl_e_dociera_do_tej_samej_obslugi_przed_dialogiem():
    assert _call(arrow=False, time_key=True) == ["key"]

def test_lista_i_tabulator_zachowuja_natywna_nawigacje():
    assert _call(player=False) == ["skip"]
    assert _call(arrow=False) == ["skip"]

def test_f2_i_delete_listy_docieraja_do_amc_przed_natywna_kontrolka():
    for chord in ("F2", "Shift+F2", "Delete", "Shift+Delete"):
        assert _call(player=False, list_chord=chord) == ["key"]


def test_sonos_space_dociera_do_transportu_z_listy_bez_psucia_ctrl_space():
    assert _call(player=False, list_chord="Space", session="sonos") == ["key"]
    assert _call(player=False, list_chord="Ctrl+Space", session="sonos") == ["skip"]
    assert _call(player=False, list_chord="Space", session="files") == ["skip"]


def test_modyfikowane_polecenia_listy_nie_gina_w_wyszukiwaniu_windows():
    for chord in (
        "Ctrl+Shift+U",
        "Ctrl+Shift+L",
        "Ctrl+Shift+Q",
        "Ctrl+Shift+Return",
        "Ctrl+Shift+H",
        "Ctrl+R",
        "Shift+R",
        "Ctrl+,",
    ):
        assert _call(player=False, list_chord=chord) == ["key"]


def test_ctrl_c_is_stopped_by_the_top_level_hook_before_native_copy() -> None:
    """CHAR_HOOK okna musi zatrzymać gest przed SysListView32."""
    for chord in ("Ctrl+C", "Ctrl+Shift+C"):
        assert _call(player=False, list_chord=chord) == ["key"]


def test_lista_ma_wlasny_wczesny_hook_dla_copy_shift_r_i_ustawien():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    bind = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_bind_list"
    )
    calls = [
        node for node in ast.walk(bind)
        if isinstance(node, ast.Call)
        and ast.unparse(node.func) == "control.Bind"
        and [ast.unparse(arg) for arg in node.args]
        == ["wx.EVT_CHAR_HOOK", "self._on_list_shortcut_hook"]
    ]
    assert len(calls) == 1

    shortcut_hook = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_on_list_shortcut_hook"
    )
    handled = {
        node.value
        for node in ast.walk(shortcut_hook)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "Ctrl+C" in handled

def test_strzalka_w_modalnym_dialogu_nie_steruje_odtwarzaczem():
    assert _call(foreign=True) == ["skip"]

def test_fokus_w_polu_filtra_oddaje_klawisz_jego_wlasnej_obsludze():
    # Przypadek ROZROZNIAJACY dla bramki z 6af38115: nawet w odtwarzaczu i nawet
    # dla strzalki fokus w polu filtra oznacza, ze klawisz nalezy do pola.
    # Bez bramki wynik byl ["key"] (nawigacja globalna porywala Enter/Backspace).
    assert _call(in_filter=True) == ["filter"]
    assert _call(in_filter=True, player=False, arrow=False) == ["filter"]


def _volume_key(chord: str, current: int = 50) -> list[int]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    method = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_on_player_shortcut_hook"
    )
    view = SimpleNamespace(PLAYER=object())
    values: list[int] = []
    slider = SimpleNamespace(owner=None, GetValue=lambda: current)
    rate_choice = SimpleNamespace(owner=None)
    filter_box = SimpleNamespace(owner=None)
    frame = SimpleNamespace(
        navigator=SimpleNamespace(view=view.PLAYER),
        filter_box=filter_box,
        volume_slider=slider,
        rate_choice=rate_choice,
        _set_volume=values.append,
        _on_filter_key=lambda _event: None,
        _on_key=lambda _event: None,
    )
    slider.owner = frame
    rate_choice.owner = frame
    filter_box.owner = frame
    wx = SimpleNamespace(
        KeyEvent=object,
        Window=SimpleNamespace(FindFocus=lambda: slider),
        GetTopLevelParent=lambda focus: focus.owner,
    )
    ns: dict[str, Any] = {
        "wx": wx,
        "View": view,
        "chord_from_event": lambda _event: SimpleNamespace(canonical=chord),
    }
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), ns)
    ns["_on_player_shortcut_hook"](frame, SimpleNamespace(Skip=lambda: None))
    return values


def test_suwak_glosnosci_ma_intuicyjne_kierunki_i_krawedzie() -> None:
    assert _volume_key("Up") == [51]
    assert _volume_key("Right") == [51]
    assert _volume_key("Down") == [49]
    assert _volume_key("Left") == [49]
    assert _volume_key("Prior") == [60]
    assert _volume_key("Next") == [40]
    assert _volume_key("Home") == [0]
    assert _volume_key("End") == [100]

def test_hook_jest_podpiety_w_zwyklym_oknie():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_bind_keys")
    calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)
             and ast.unparse(n.func) == "self.Bind"
             and [ast.unparse(x) for x in n.args] == ["wx.EVT_CHAR_HOOK", "self._on_player_shortcut_hook"]]
    assert len(calls) == 1
