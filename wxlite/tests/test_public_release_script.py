"""REL-001: publikacja jest domyślnie lokalną, ścisłą weryfikacją."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY_ROOT / "scripts" / "Publish-AMCPublicRelease.ps1"
SHARED_SCRIPT = REPOSITORY_ROOT / "scripts" / "Publish-AMCRelease.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


def _fixture(tmp_path: Path, *, profile: str = "public", sha: str | None = None):
    version = "0.1.0-alpha.999"
    installer = tmp_path / "AMC-Public-2026-10-22-2125.exe"
    installer.write_bytes(b"syntetyczny instalator publiczny")
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    integrity = {
        "schemaVersion": 1,
        "profile": profile,
        "version": version,
        "displayVersion": "22.10.2026, 21:25",
        "fileName": installer.name,
        "bytes": installer.stat().st_size,
        "sha256": sha or digest,
        "bundleId": "synthetic",
        "sourceRevision": "1" * 40,
        "secretScan": "passed",
    }
    (tmp_path / f"{installer.name}.integrity.json").write_text(
        json.dumps(integrity), encoding="utf-8"
    )
    return version, installer, digest


def _run(tmp_path: Path, version: str):
    assert POWERSHELL is not None
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-Version",
            version,
            "-ArtifactsDirectory",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_prepare_only_verifies_installer_and_does_not_publish(tmp_path: Path) -> None:
    version, installer, digest = _fixture(tmp_path)
    result = _run(tmp_path, version)

    assert result.returncode == 0, result.stderr
    assert "Niczego nie opublikowano" in result.stdout
    notes = (tmp_path / f"release-notes-public-{version}.md").read_text(
        encoding="utf-8"
    )
    assert installer.name in notes
    assert digest in notes
    ready = json.loads(
        (tmp_path / f"release-ready-public-{version}.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert ready["profile"] == "public"
    assert ready["tag"] == "public-2026.10.22.2125"
    assert ready["updateChannel"] == "stable"
    assert ready["prerelease"] is False
    assert ready["published"] is False
    assert ready["sha256"] == digest
    update_manifest = json.loads(
        (tmp_path / "amc-update-public.json").read_text(encoding="utf-8-sig")
    )
    assert update_manifest["profile"] == "public"
    assert update_manifest["updateChannel"] == "stable"
    assert update_manifest["installer"]["fileName"] == installer.name
    assert update_manifest["installer"]["sha256"] == digest
    assert "package" not in update_manifest


def test_prepare_only_rejects_private_profile_and_changed_hash(tmp_path: Path) -> None:
    version, _installer, _digest = _fixture(tmp_path, profile="test")
    private_result = _run(tmp_path, version)
    assert private_result.returncode != 0
    assert "AMC Public" in (private_result.stdout + private_result.stderr)

    for child in tmp_path.iterdir():
        child.unlink()
    version, _installer, _digest = _fixture(tmp_path, sha="0" * 64)
    changed_result = _run(tmp_path, version)
    assert changed_result.returncode != 0
    assert "SHA-256" in (changed_result.stdout + changed_result.stderr)


def test_prepare_only_rejects_artifact_without_secret_scan(tmp_path: Path) -> None:
    version, installer, _digest = _fixture(tmp_path)
    integrity_path = tmp_path / f"{installer.name}.integrity.json"
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    integrity.pop("secretScan")
    integrity_path.write_text(json.dumps(integrity), encoding="utf-8")

    result = _run(tmp_path, version)
    assert result.returncode != 0
    assert "potwierdzonej kontroli sekret" in (result.stdout + result.stderr)


def test_publish_path_requires_remote_commit_and_verifies_uploaded_assets() -> None:
    source = SHARED_SCRIPT.read_text(encoding="utf-8")
    assert '[ValidateSet("public", "test")]' in source
    assert "[switch]$Publish" in source
    assert "--untracked-files=no" in source
    assert 'gh api "repos/$Repository/commits/$sourceRevision"' in source
    assert 'gh release create' not in source
    assert '"release", "create", $tag' in source
    assert '"--title", "$displayName — $displayVersion"' in source
    assert 'if ($isPrerelease)' in source
    assert '"--prerelease"' in source
    assert "Wydanie $tag już istnieje" in source
    assert "asset.size" in source
    assert "integrityAsset.state" in source
    assert "updateManifestAsset.state" in source
    assert "updatePackageHash" not in source
    assert "installer = [ordered]" in source
    assert "release.body.Contains($actualHash)" in source


def test_shared_gate_prepares_test_channel_as_prerelease(tmp_path: Path) -> None:
    version = "0.1.0-alpha.999"
    installer = tmp_path / "AMC-Test-2026-10-22-2125.exe"
    installer.write_bytes(b"syntetyczny instalator test")
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    integrity = {
        "schemaVersion": 1,
        "profile": "test",
        "version": version,
        "displayVersion": "22.10.2026, 21:25",
        "fileName": installer.name,
        "bytes": installer.stat().st_size,
        "sha256": digest,
        "bundleId": "synthetic",
        "sourceRevision": "2" * 40,
        "secretScan": "passed",
    }
    (tmp_path / f"{installer.name}.integrity.json").write_text(
        json.dumps(integrity), encoding="utf-8"
    )

    assert POWERSHELL is not None
    result = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-File",
            str(SHARED_SCRIPT),
            "-Profile",
            "test",
            "-Version",
            version,
            "-ArtifactsDirectory",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    ready = json.loads(
        (tmp_path / f"release-ready-test-{version}.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert ready["tag"] == "test-2026.10.22.2125"
    assert ready["updateChannel"] == "test"
    assert ready["prerelease"] is True
    assert ready["published"] is False
    update_manifest = json.loads(
        (tmp_path / "amc-update-test.json").read_text(encoding="utf-8-sig")
    )
    assert update_manifest["profile"] == "test"
    assert update_manifest["updateChannel"] == "test"
    assert update_manifest["prerelease"] is True
    assert update_manifest["installer"]["fileName"] == installer.name
    assert update_manifest["installer"]["sha256"] == digest


def test_public_wrapper_delegates_to_shared_profiled_gate() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'Profile = "public"' in source
    assert "Publish-AMCRelease.ps1" in source
