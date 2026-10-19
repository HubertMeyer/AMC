#!/usr/bin/env python3
"""Odwracalna poprawka zgodności Ctrl+C dla NVDAExtensionGlobalPlugin.

Narzędzie nie uruchamia ani nie restartuje NVDA. Domyślnie tylko sprawdza,
czy wskazany plik dodatku można bezpiecznie poprawić. ``--apply`` zapisuje
kopię oryginału obok pliku i podmienia go atomowo; ``--restore`` wymaga jawnej
ścieżki tej kopii.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import tempfile


BEGIN = "# AMC CTRL+C COMPATIBILITY BEGIN"
END = "# AMC CTRL+C COMPATIBILITY END"

IMPORT_ANCHOR = "import os\nimport sys\n"
EDITABLE_ANCHOR = "\tdef initOverlayClass(self):\n\t\tif isInstall(FCT_ClipboardCommandAnnouncement):\n"
OVERLAY_ANCHOR = "\telif isInstall(FCT_ClipboardCommandAnnouncement):\n\t\tclsList.insert(0, ClipboardCommandAnnouncement)\n"

HELPER = '''# AMC CTRL+C COMPATIBILITY BEGIN
def _isAmcApplicationObject(obj):
\t"""Recognize an installed AMC runtime without relying on its window title."""
\ttry:
\t\tappPath = os.path.normcase(os.path.abspath(obj.appModule.appPath))
\t\truntimeDir = os.path.dirname(appPath)
\t\tinstallRoot = os.path.dirname(runtimeDir)
\t\tif os.path.basename(appPath).casefold() != "python.exe":
\t\t\treturn False
\t\tif os.path.basename(runtimeDir).casefold() != "runtime":
\t\t\treturn False
\t\tmanifestPath = os.path.join(installRoot, "bundle-manifest.json")
\t\tlauncherPath = os.path.join(installRoot, "AMC.exe")
\t\tif not os.path.isfile(manifestPath) or not os.path.isfile(launcherPath):
\t\t\treturn False
\t\twith open(manifestPath, "r", encoding="utf-8") as manifestFile:
\t\t\tmanifest = json.load(manifestFile)
\t\treturn (
\t\t\tmanifest.get("pythonModule") == "amc_wx_lite"
\t\t\tand manifest.get("entryPoint") == "AMC.exe"
\t\t\tand manifest.get("application") in ("AMC Python", "AMC Test", "AMC")
\t\t)
\texcept (AttributeError, OSError, TypeError, ValueError, json.JSONDecodeError):
\t\treturn False
# AMC CTRL+C COMPATIBILITY END
'''


def default_target() -> Path:
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "nvda" / "addons" / "NVDAExtensionGlobalPlugin" / (
        "globalPlugins/NVDAExtensionGlobalPlugin/clipboardCommandAnnouncement/__init__.py"
    )


def build_patched_text(source: str) -> str:
    """Return one deterministic patch or reject an unknown upstream layout."""

    if BEGIN in source:
        return source
    missing = [
        label
        for label, anchor in (
            ("imports", IMPORT_ANCHOR),
            ("EditableTextEx", EDITABLE_ANCHOR),
            ("ClipboardCommandAnnouncement", OVERLAY_ANCHOR),
        )
        if source.count(anchor) != 1
    ]
    if missing:
        raise ValueError(
            "Nieznany układ NVDAExtensionGlobalPlugin: " + ", ".join(missing)
        )
    patched = source.replace(
        IMPORT_ANCHOR,
        "import json\n" + IMPORT_ANCHOR + "\n" + HELPER + "\n",
        1,
    )
    patched = patched.replace(
        EDITABLE_ANCHOR,
        "\tdef initOverlayClass(self):\n"
        "\t\tif _isAmcApplicationObject(self):\n"
        "\t\t\treturn\n"
        "\t\tif isInstall(FCT_ClipboardCommandAnnouncement):\n",
        1,
    )
    patched = patched.replace(
        OVERLAY_ANCHOR,
        "\telif (\n"
        "\t\tisInstall(FCT_ClipboardCommandAnnouncement)\n"
        "\t\tand not _isAmcApplicationObject(obj)\n"
        "\t):\n"
        "\t\tclsList.insert(0, ClipboardCommandAnnouncement)\n",
        1,
    )
    compile(patched, "NVDAExtensionGlobalPlugin/clipboardCommandAnnouncement/__init__.py", "exec")
    return patched


def backup_path(target: Path, source: bytes) -> Path:
    digest = hashlib.sha256(source).hexdigest()[:12]
    return target.with_name(f"{target.name}.amc-original-{digest}")


def atomic_write(target: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{target.name}.amc-",
        suffix=".tmp",
        dir=target.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def apply_patch(target: Path) -> tuple[str, Path | None]:
    source_bytes = target.read_bytes()
    raw_source = source_bytes.decode("utf-8")
    # Dry-run reads translate CRLF automatically.  Applying starts from exact
    # bytes, so normalize only for matching and then preserve the installed
    # add-on's newline convention in the atomically written replacement.
    crlf_only = "\r\n" in raw_source and "\n" not in raw_source.replace("\r\n", "")
    source = raw_source.replace("\r\n", "\n") if crlf_only else raw_source
    patched = build_patched_text(source)
    if patched == source:
        return "already-applied", None
    backup = backup_path(target, source_bytes)
    if not backup.exists():
        shutil.copy2(target, backup)
    elif backup.read_bytes() != source_bytes:
        raise ValueError(f"Istniejąca kopia nie odpowiada oryginałowi: {backup}")
    output = patched.replace("\n", "\r\n") if crlf_only else patched
    atomic_write(target, output.encode("utf-8"))
    return "applied", backup


def restore_patch(target: Path, backup: Path) -> None:
    if not backup.is_file():
        raise FileNotFoundError(backup)
    current = target.read_text(encoding="utf-8")
    if BEGIN not in current or END not in current:
        raise ValueError("Bieżący plik nie zawiera poprawki AMC; odmowa nadpisania")
    atomic_write(target, backup.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=default_target())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", type=Path)
    args = parser.parse_args()
    target = args.target.resolve()
    if args.restore:
        restore_patch(target, args.restore.resolve())
        print(f"Przywrócono oryginał: {target}")
        return 0
    source = target.read_text(encoding="utf-8")
    patched = build_patched_text(source)
    if not args.apply:
        print("Poprawka jest już obecna." if patched == source else "Poprawkę można zastosować.")
        return 0
    status, backup = apply_patch(target)
    if status == "already-applied":
        print("Poprawka jest już obecna.")
    else:
        print(f"Zastosowano poprawkę. Kopia oryginału: {backup}")
    print("Aby zmiana zaczęła działać, NVDA trzeba później świadomie zrestartować.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
