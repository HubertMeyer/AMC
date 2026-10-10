#!/usr/bin/env python3
"""Zloz prywatny pakiet AMC-wx-Lite do uruchomienia na Windows.

Co robi: kopiuje kod Pythona, zbudowany bezokienny silnik i launcher do jednego
folderu, ktory wystarczy przeniesc na dysk NTFS i uruchomic.

Czego NIE robi swiadomie:
  * nie instaluje niczego globalnie,
  * nie kopiuje runtime ani MSVCP140.dll (prawa redystrybucji VC++ sa bramka
    publikacji - runtime dokladasz osobno, wskazujac --runtime),
  * nie dotyka danych, ustawien, stacji ani nagran pelnego AMC.

Uzycie (w WSL albo na Windows):
    python3 tools/build_bundle.py --out /tmp/AMC-wx-Lite
    python3 tools/build_bundle.py --out /tmp/AMC-wx-Lite --runtime /mnt/c/.../runtime
    python3 tools/build_bundle.py --out /tmp/AMC-wx-Lite --host-subdir host-next
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

WXLITE = Path(__file__).resolve().parent.parent
REPO = WXLITE.parent
HOST_PUBLISH = (
    REPO
    / "src"
    / "AccessibleMediaController.LiteHost"
    / "bin"
    / "Release"
    / "net8.0-windows10.0.19041.0"
    / "win-x64"
    / "publish"
)
UPDATER_PUBLISH = (
    REPO
    / "src"
    / "AccessibleMediaController.PythonUpdater"
    / "bin"
    / "Release"
    / "net8.0-windows"
    / "win-x64"
    / "publish"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_python_code(target: Path) -> list[str]:
    package = target / "app" / "amc_wx_lite"
    package.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in sorted((WXLITE / "amc_wx_lite").glob("*.py")):
        shutil.copy2(source, package / source.name)
        copied.append(f"app/amc_wx_lite/{source.name}")
    for name in ("AMC-wx-Lite.cmd", "requirements-win64.txt", "JAK_TESTOWAC.md"):
        source = WXLITE / name
        if source.exists():
            shutil.copy2(source, target / name)
            copied.append(name)
    return copied


def copy_host(
    target: Path,
    host_dir: Path,
    host_subdir: str = "host",
) -> tuple[list[str], dict]:
    """Skopiuj silnik. Brak buildu to BLAD, nie cicha atrapa."""
    if not host_dir.exists():
        raise SystemExit(
            f"Nie ma zbudowanego silnika w {host_dir}.\n"
            "Zbuduj go najpierw:\n"
            "  /home/michal/dotnet/dotnet publish "
            "src/AccessibleMediaController.LiteHost -c Release -r win-x64 --self-contained false"
        )
    if Path(host_subdir).name != host_subdir or host_subdir in {"", ".", ".."}:
        raise SystemExit(
            "Nazwa folderu hosta musi byc pojedyncza bezpieczna nazwa, "
            "np. host albo host-next."
        )
    destination = target / host_subdir
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    hashes = {}
    for source in sorted(host_dir.rglob("*")):
        if source.is_file() and source.suffix.lower() in {".exe", ".dll", ".json", ".pdb", ".txt", ".md"}:
            relative = source.relative_to(host_dir)
            output = destination / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(source, output)
            except PermissionError as error:
                raise SystemExit(
                    f"Nie można podmienić pliku hosta {output}: {error}"
                ) from error
            copied.append(f"{host_subdir}/{relative.as_posix()}")
            if source.suffix.lower() in {".exe", ".dll"}:
                hashes[relative.as_posix()] = sha256(source)
    executable = destination / "amc_lite_host.exe"
    if not executable.exists():
        raise SystemExit(f"W {host_dir} nie ma amc_lite_host.exe - build jest niepelny.")
    return copied, hashes


def copy_runtime(target: Path, runtime: Path) -> list[str]:
    if not runtime.exists():
        raise SystemExit(f"Wskazany runtime nie istnieje: {runtime}")
    destination = target / "runtime"
    # Przy aktualizacji pakietu na miejscu wskazany, juz sprawdzony runtime
    # moze byc zarazem katalogiem docelowym. Nie kasujemy wtedy zrodla;
    # wpisujemy tylko jego istniejace pliki do nowego manifestu.
    if runtime.resolve() == destination.resolve():
        return [
            p.relative_to(target).as_posix()
            for p in sorted(destination.rglob("*"))
            if p.is_file()
        ]
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(runtime, destination)
    for paths_file in destination.glob("python*._pth"):
        lines = paths_file.read_text(encoding="utf-8").splitlines()
        if "../app" not in lines:
            lines.append("../app")
        paths_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [p.relative_to(target).as_posix() for p in sorted(destination.rglob("*")) if p.is_file()]


def copy_updater(target: Path, updater_dir: Path) -> list[str]:
    executable = updater_dir / "AMC-Python-Updater.exe"
    if not executable.is_file():
        raise SystemExit(
            f"Nie ma zbudowanego aktualizatora w {executable}.\n"
            "Zbuduj go: dotnet publish "
            "src/AccessibleMediaController.PythonUpdater -c Release "
            "-r win-x64 --self-contained false"
        )
    shutil.copy2(executable, target / executable.name)
    return [executable.name]


def main() -> int:
    parser = argparse.ArgumentParser(description="Zloz pakiet AMC-wx-Lite")
    parser.add_argument("--out", required=True, type=Path, help="folder docelowy")
    parser.add_argument("--host", type=Path, default=HOST_PUBLISH, help="folder z publish silnika")
    parser.add_argument(
        "--host-subdir",
        default="host",
        help=(
            "folder silnika w pakiecie; host-next pozwala przygotowac nowa "
            "wersje bez zamykania uruchomionego hosta"
        ),
    )
    parser.add_argument(
        "--updater",
        type=Path,
        default=UPDATER_PUBLISH,
        help="folder publish wykonywalnego aktualizatora AMC Python",
    )
    parser.add_argument(
        "--runtime",
        type=Path,
        default=None,
        help="opcjonalny prywatny runtime Pythona do dolozenia (nie trafia do Git)",
    )
    parser.add_argument("--clean", action="store_true", help="wyczysc folder docelowy")
    parser.add_argument(
        "--refresh-python-only",
        action="store_true",
        help=(
            "odswiez tylko interfejs, dokumentacje i aktualizator w istniejacej "
            "paczce; nie dotykaj uruchomionego hosta ani runtime"
        ),
    )
    args = parser.parse_args()

    target: Path = args.out
    if args.refresh_python_only:
        manifest_path = target / "bundle-manifest.json"
        if not manifest_path.is_file():
            raise SystemExit(
                "Tryb --refresh-python-only wymaga istniejacej kompletnej paczki"
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = list(manifest.get("files") or [])
        files += copy_python_code(target)
        files += copy_updater(target, args.updater)
        manifest["created"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        manifest["files"] = [
            relative
            for relative in dict.fromkeys(files)
            if (target / Path(relative)).is_file()
        ]
        manifest["fileHashes"] = {
            relative: sha256(target / Path(relative))
            for relative in manifest["files"]
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Odswiezono interfejs i aktualizator: {target}")
        print(f"  plikow: {len(manifest['files'])}")
        return 0

    if args.clean and target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "Prywatny pakiet AMC-wx-Lite bez danych pełnego AMC. Zawartość runtime zależy od wskazanego źródła; publikacja wymaga sprawdzenia licencji.",
        "files": [],
    }

    manifest["files"] += copy_python_code(target)
    manifest["files"] += copy_updater(target, args.updater)
    host_files, host_hashes = copy_host(target, args.host, args.host_subdir)
    manifest["files"] += host_files
    manifest["hostHashes"] = host_hashes
    manifest["hostFolder"] = args.host_subdir

    if args.runtime is not None:
        manifest["files"] += copy_runtime(target, args.runtime)
        manifest["runtime"] = str(args.runtime)
    else:
        manifest["runtime"] = (
            "NIE DOLOZONY - wskaz --runtime albo utworz .venv i zainstaluj "
            "requirements-win64.txt"
        )

    # Aktualizator akceptuje wyłącznie kompletne paczki. Sumy obejmują każdy
    # plik wymieniony w manifeście, nie tylko binaria hosta.
    manifest["files"] = list(dict.fromkeys(manifest["files"]))
    manifest["fileHashes"] = {
        relative: sha256(target / Path(relative))
        for relative in manifest["files"]
    }

    (target / "bundle-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Pakiet gotowy: {target}")
    print(f"  plikow: {len(manifest['files'])}")
    for name, digest in host_hashes.items():
        print(f"  {name} sha256={digest}")
    print("\nUruchomienie na Windows:")
    print(r"  AMC-wx-Lite.cmd --sprawdz   (diagnostyka, bez okna)")
    print(r"  AMC-wx-Lite.cmd             (okno)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
