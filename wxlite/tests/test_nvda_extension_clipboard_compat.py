from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "nvda_extension_clipboard_compat.py"
SPEC = importlib.util.spec_from_file_location("nvda_extension_clipboard_compat", TOOL)
assert SPEC is not None and SPEC.loader is not None
compat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compat)


UPSTREAM_FIXTURE = """import os
import sys

class EditableTextEx:
\tdef initOverlayClass(self):
\t\tif isInstall(FCT_ClipboardCommandAnnouncement):
\t\t\tpass

def chooseNVDAObjectOverlayClasses(obj, clsList):
\tif False:
\t\tpass
\telif isInstall(FCT_ClipboardCommandAnnouncement):
\t\tclsList.insert(0, ClipboardCommandAnnouncement)
"""


def test_patch_is_idempotent_and_does_not_use_window_title() -> None:
    patched = compat.build_patched_text(UPSTREAM_FIXTURE)

    assert compat.BEGIN in patched
    assert compat.build_patched_text(patched) == patched
    assert "obj.appModule.appPath" in patched
    assert 'manifest.get("pythonModule") == "amc_wx_lite"' in patched
    assert "windowText" not in patched
    assert "windowClassName" not in patched


def test_patch_bypasses_only_clipboard_bindings_for_amc() -> None:
    patched = compat.build_patched_text(UPSTREAM_FIXTURE)

    assert "if _isAmcApplicationObject(self):\n\t\t\treturn" in patched
    assert "and not _isAmcApplicationObject(obj)" in patched
    assert patched.count(compat.BEGIN) == 1


def test_unknown_upstream_layout_is_rejected() -> None:
    try:
        compat.build_patched_text("import os\n")
    except ValueError as error:
        assert "Nieznany układ" in str(error)
    else:
        raise AssertionError("Nieznany plik dodatku nie może zostać nadpisany")


def test_apply_preserves_crlf_installed_addon(tmp_path: Path) -> None:
    target = tmp_path / "__init__.py"
    source = UPSTREAM_FIXTURE.replace("\n", "\r\n")
    target.write_bytes(source.encode("utf-8"))

    status, backup = compat.apply_patch(target)

    assert status == "applied"
    assert backup is not None and backup.read_bytes() == source.encode("utf-8")
    patched = target.read_bytes()
    assert b"\r\n" in patched
    assert b"\n" not in patched.replace(b"\r\n", b"")
    assert compat.BEGIN.encode("utf-8") in patched
