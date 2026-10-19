"""Strukturalny kontrakt dwóch instalatorów; bez uruchamiania Inno Setup."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ISS = (ROOT / "installer" / "AMC_Wx_Setup.iss").read_text(encoding="utf-8")
BUILD = (ROOT / "wxlite" / "tools" / "Build-AMCInstaller.ps1").read_text(
    encoding="utf-8"
)
BUNDLE_BUILD = (ROOT / "wxlite" / "tools" / "Build-AMCBundle.ps1").read_text(
    encoding="utf-8"
)


def test_installer_profiles_have_separate_ids_names_folders_and_mutexes() -> None:
    for required in (
        "Accessible Multimedia Controller",
        "Accessible Multimedia Controller — Test",
        "AMC-\" + Wersja + \"-win-x64",
        "AMC-Test-\" + Wersja + \"-win-x64",
        "1E437448-30B4-4E4A-BCA1-CDA114B096A9",
        "0B807571-BDC5-4287-BD7C-4F4A7C71438F",
        "PythonLauncher.Public.SingleInstance",
        "PythonLauncher.SingleInstance",
        "FolderProgramu \"AMC\"",
        "FolderProgramu \"AMC Test\"",
    ):
        assert required in ISS


def test_installer_never_forces_running_amc_to_close() -> None:
    assert "CloseApplications=no" in ISS
    assert "RestartApplications=no" in ISS
    assert "CloseApplications=force" not in ISS
    assert "AppMutex={#LauncherMutex}" in ISS


def test_installer_performs_full_post_install_integrity_check() -> None:
    assert "--sprawdz-pakiet-pelny-cicho" in ISS
    assert "ewWaitUntilTerminated" in ISS
    assert "ResultCode <> 0" in ISS
    assert "RaiseException" in ISS


def test_build_helper_verifies_profile_clean_source_and_full_bundle() -> None:
    assert 'ValidateSet("public", "test")' in BUILD
    assert "manifest.releaseProfile" in BUILD
    assert "manifest.sourceDirty" in BUILD
    assert "--sprawdz-pakiet-pelny-cicho" in BUILD
    assert "Get-FileHash" in BUILD
    assert "sha256" in BUILD
    assert "bytes" in BUILD
    assert '$env:LOCALAPPDATA "Programs\\Inno Setup 6\\ISCC.exe"' in BUILD


def test_bundle_builder_embeds_dotnet_and_private_python_runtime() -> None:
    assert "$hostOutput" in BUNDLE_BUILD
    assert "$host =" not in BUNDLE_BUILD
    assert BUNDLE_BUILD.count('"--self-contained", "true"') == 3
    assert BUNDLE_BUILD.count('"--artifacts-path"') == 3
    assert '"--profile", $Profile' in BUNDLE_BUILD
    assert '"--runtime", $runtime' in BUNDLE_BUILD
    assert "--sprawdz-pakiet-pelny-cicho" in BUNDLE_BUILD
    assert "Start-Process -FilePath $LauncherPath" in BUNDLE_BUILD
    assert "-Wait -PassThru -WindowStyle Hidden" in BUNDLE_BUILD
    assert "Folder docelowy już istnieje" in BUNDLE_BUILD
    assert "Move-Item -LiteralPath $candidate" in BUNDLE_BUILD


def test_bundle_builder_cleans_only_its_unique_project_temporary_folder() -> None:
    assert 'Join-Path $repositoryRoot ".test-tmp"' in BUNDLE_BUILD
    assert '"bundle-build-" + [guid]::NewGuid()' in BUNDLE_BUILD
    assert "Remove-Item -LiteralPath $operationRoot -Recurse -Force" in BUNDLE_BUILD
