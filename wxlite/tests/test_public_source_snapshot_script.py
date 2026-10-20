"""REL-001: czysta publiczna linia źródeł bez zmiany bieżącej gałęzi."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY_ROOT / "scripts" / "Prepare-AMCPublicSourceSnapshot.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


def _git(repository: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    _git(repository, "init", "-b", "development")
    _git(repository, "config", "user.name", "Test User")
    _git(repository, "config", "user.email", "test@example.invalid")
    (repository / "app.txt").write_text("pierwsze źródła\n", encoding="utf-8")
    _git(repository, "add", "app.txt")
    _git(repository, "commit", "-m", "roboczy commit")
    return repository


def _run(repository: Path, version: str) -> subprocess.CompletedProcess[str]:
    assert POWERSHELL is not None
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-Version",
            version,
            "-RepositoryRoot",
            str(repository),
            "-OutputDirectory",
            str(repository / "output"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.skipif(POWERSHELL is None, reason="Brak PowerShell")
def test_snapshot_is_orphan_idempotent_and_does_not_change_checkout(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    original_head = _git(repository, "rev-parse", "HEAD").stdout.strip()
    original_branch = _git(repository, "branch", "--show-current").stdout.strip()

    first = _run(repository, "0.1.0-alpha.1")
    assert first.returncode == 0, first.stderr
    assert "Niczego nie wypchni" in first.stdout
    snapshot = _git(repository, "rev-parse", "public/release-line").stdout.strip()
    assert _git(repository, "rev-list", "--count", snapshot).stdout.strip() == "1"
    assert _git(repository, "rev-parse", f"{snapshot}^{{tree}}").stdout.strip() == _git(
        repository, "rev-parse", "HEAD^{tree}"
    ).stdout.strip()
    assert _git(repository, "rev-parse", "HEAD").stdout.strip() == original_head
    assert _git(repository, "branch", "--show-current").stdout.strip() == original_branch

    second = _run(repository, "0.1.0-alpha.1")
    assert second.returncode == 0, second.stderr
    assert _git(repository, "rev-parse", "public/release-line").stdout.strip() == snapshot
    manifest = json.loads(
        (repository / "output" / "source-ready-0.1.0-alpha.1.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert manifest["snapshotRevision"] == snapshot
    assert manifest["published"] is False


@pytest.mark.skipif(POWERSHELL is None, reason="Brak PowerShell")
def test_next_snapshot_has_previous_public_snapshot_as_its_only_parent(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    assert _run(repository, "0.1.0-alpha.1").returncode == 0
    first_snapshot = _git(repository, "rev-parse", "public/release-line").stdout.strip()

    (repository / "app.txt").write_text("drugie źródła\n", encoding="utf-8")
    _git(repository, "add", "app.txt")
    _git(repository, "commit", "-m", "kolejny roboczy commit")
    result = _run(repository, "0.1.0-alpha.2")
    assert result.returncode == 0, result.stderr
    second_snapshot = _git(repository, "rev-parse", "public/release-line").stdout.strip()
    assert second_snapshot != first_snapshot
    assert _git(repository, "rev-parse", f"{second_snapshot}^").stdout.strip() == first_snapshot
    assert _git(repository, "rev-list", "--count", second_snapshot).stdout.strip() == "2"
    assert _git(repository, "rev-parse", "HEAD").stdout.strip() != second_snapshot


@pytest.mark.skipif(POWERSHELL is None, reason="Brak PowerShell")
def test_snapshot_rejects_tracked_changes_and_never_pushes(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    (repository / "app.txt").write_text("niezapisana zmiana\n", encoding="utf-8")

    result = _run(repository, "0.1.0-alpha.1")
    assert result.returncode != 0
    assert "Snapshot wymaga czystych" in (result.stdout + result.stderr)
    source = SCRIPT.read_text(encoding="utf-8")
    assert "git push" not in source


@pytest.mark.skipif(POWERSHELL is None, reason="Brak PowerShell")
def test_snapshot_rejects_private_windows_profile_path(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    private_path = "C:\\Users\\" + "micha\\sekret\\plik.txt"
    (repository / "app.txt").write_text(
        f"przykład {private_path}\n", encoding="utf-8"
    )
    _git(repository, "add", "app.txt")
    _git(repository, "commit", "-m", "prywatna ścieżka")

    result = _run(repository, "0.1.0-alpha.1")

    assert result.returncode != 0
    assert "lokalna" in (result.stdout + result.stderr)
    assert "profilu Windows" in (result.stdout + result.stderr)
