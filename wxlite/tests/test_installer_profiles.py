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
PROMOTE_TEST = (
    ROOT / "wxlite" / "tools" / "Promote-AMCPythonTestBuild.ps1"
).read_text(encoding="utf-8")
LAUNCHER = (
    ROOT / "src" / "AccessibleMediaController.PythonLauncher" / "Program.cs"
).read_text(encoding="utf-8")
PYTHON_MAIN = (ROOT / "wxlite" / "amc_wx_lite" / "__main__.py").read_text(
    encoding="utf-8"
)
GUI = (ROOT / "wxlite" / "amc_wx_lite" / "gui.py").read_text(encoding="utf-8")


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


def test_shell_integration_is_available_and_isolated_for_both_profiles() -> None:
    """AMC oraz AMC Test mogą współistnieć w powłoce bez wspólnych wpisów."""
    for required in (
        'ShellProfileKey "Public"',
        'ShellProfileKey "Test"',
        'ShellApplicationName "Accessible Multimedia Controller"',
        'ShellApplicationName "Accessible Multimedia Controller — Test"',
        'ShellOpenLabel "Otwórz w AMC"',
        'ShellOpenLabel "Otwórz w AMC Test"',
        'ShellQueueLabel "Dodaj do kolejki AMC"',
        'ShellQueueLabel "Dodaj do kolejki AMC Test"',
        "ShellCapabilitiesRoot = 'Software\\AccessibleMultimediaController\\{#ShellProfileKey}\\Capabilities'",
        "ShellClassPrefix = 'AccessibleMediaController.{#ShellProfileKey}.'",
        "ShellVerbPrefix = 'AccessibleMediaController.{#ShellProfileKey}.'",
    ):
        assert required in ISS

    assert 'RegDeleteKeyIncludingSubkeys(HKA, ShellCapabilitiesRoot)' in ISS
    assert "AssociationRoot + 'open'" in ISS
    assert "AssociationRoot + 'queue'" in ISS
    assert "ShellClassesRoot + ClassName" in ISS
    assert "UserChoice" not in ISS


def test_installer_never_forces_running_amc_to_close() -> None:
    assert "CloseApplications=no" in ISS
    assert "RestartApplications=no" in ISS
    assert "CloseApplications=force" not in ISS
    assert "AppMutex={#LauncherMutex}" in ISS


def test_installer_shortcuts_are_optional_and_noicons_is_effective() -> None:
    assert "DisableProgramGroupPage=auto" in ISS
    assert "AllowNoIcons=yes" in ISS
    assert 'Name: "desktopicon"' in ISS
    assert 'Flags: unchecked' in ISS
    assert ISS.count("Check: not WizardNoIcons") == 3
    assert "Tasks: desktopicon" in ISS


def test_installer_performs_full_post_install_integrity_check() -> None:
    assert "--sprawdz-pakiet-pelny-cicho" in ISS
    assert "--sprawdz-start-cicho" in ISS
    assert "ewWaitUntilTerminated" in ISS
    assert "ResultCode <> 0" in ISS
    assert "RaiseException" in ISS
    assert ISS.index("--sprawdz-start-cicho") < ISS.index("RegisterShellIntegration;", ISS.index("procedure CurStepChanged"))


def test_installer_refuses_to_overlay_another_or_historical_product() -> None:
    assert 'ExpectedInstallId "AMC.Public.win-x64"' in ISS
    assert 'ExpectedInstallId "AMC.Test.win-x64"' in ISS
    assert "DirectoryHasEntries" in ISS
    assert "ExistingDirectoryBelongsToThisProfile" in ISS
    assert 'bundle-manifest.json' in ISS
    assert '"installId": "{#ExpectedInstallId}"' in ISS
    assert "function PrepareToInstall" in ISS
    assert "Instalator nie nadpisze jej plików" in ISS


def test_build_helper_verifies_profile_clean_source_and_full_bundle() -> None:
    assert 'ValidateSet("public", "test")' in BUILD
    assert "manifest.releaseProfile" in BUILD
    assert "manifest.sourceDirty" in BUILD
    assert "--sprawdz-pakiet-pelny-cicho" in BUILD
    assert "Test-AMCBundleStartup.ps1" in BUILD
    assert "& $startupSmokeTool -BundleRoot $bundle" in BUILD
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
    assert "Test-AMCBundleStartup.ps1" in BUNDLE_BUILD
    assert "& $startupSmokeTool -BundleRoot $candidate" in BUNDLE_BUILD
    assert "Start-Process -FilePath $LauncherPath" in BUNDLE_BUILD
    assert "-Wait -PassThru -WindowStyle Hidden" in BUNDLE_BUILD
    assert "Folder docelowy już istnieje" in BUNDLE_BUILD
    assert "Move-Item -LiteralPath $candidate" in BUNDLE_BUILD


def test_bundle_builder_cleans_only_its_unique_project_temporary_folder() -> None:
    assert 'Join-Path $repositoryRoot ".test-tmp"' in BUNDLE_BUILD
    assert '"bundle-build-" + [guid]::NewGuid()' in BUNDLE_BUILD
    assert "Remove-Item -LiteralPath $operationRoot -Recurse -Force" in BUNDLE_BUILD


def test_test_profile_promotion_smokes_candidate_and_installed_copy_before_launch() -> None:
    assert "Test-AMCBundleStartup.ps1" in PROMOTE_TEST
    candidate_gate = "& $StartupSmokeTool -BundleRoot $candidateRoot"
    installed_gate = "& $StartupSmokeTool -BundleRoot $InstallRoot"
    visible_launch = "Start-Process -FilePath $InstalledLauncher"
    assert candidate_gate in PROMOTE_TEST
    assert installed_gate in PROMOTE_TEST
    assert PROMOTE_TEST.index(candidate_gate) < PROMOTE_TEST.index(
        '"--source", $candidateRoot'
    )
    assert PROMOTE_TEST.index(installed_gate) < PROMOTE_TEST.index(visible_launch)


def test_startup_smoke_requires_ready_marker_timeout_and_no_leftovers() -> None:
    smoke = (ROOT / "wxlite" / "tools" / "Test-AMCBundleStartup.ps1").read_text(
        encoding="utf-8"
    )
    for required in (
        "--sprawdz-start-cicho",
        "AMC_STARTUP_SMOKE_RESULT",
        'result -ne "READY"',
        "WaitForExit($TimeoutSeconds * 1000)",
        "Get-Process -ErrorAction SilentlyContinue",
        "Kontrolowany start pozostawił procesy",
        '"startup-smoke-" + [guid]::NewGuid()',
    ):
        assert required in smoke


def test_startup_smoke_is_isolated_and_cannot_activate_an_existing_instance() -> None:
    assert '"--sprawdz-start-cicho"' in LAUNCHER
    assert "suppressFailureDialog: true" in LAUNCHER
    assert "if (!suppressFailureDialog)\n            AppendProcessLog" in LAUNCHER
    assert LAUNCHER.index("if (silentStartupCheck)") < LAUNCHER.index(
        "LauncherInstanceLease.TryAcquire"
    )
    for required in (
        "AMC_STARTUP_SMOKE",
        "AMC_WX_FIXTURE",
        "TemporaryDirectory",
        "APPDATA",
        "LOCALAPPDATA",
    ):
        assert required in PYTHON_MAIN
    assert 'frame.Hide()' in GUI
    assert 'AMC_STARTUP_SMOKE_READY' in GUI
    assert 'self._startup_smoke_ready = True' in GUI
    assert 'if not _startup_smoke_mode()' in GUI
    activation_handler = GUI[GUI.index("def _on_window_activate"):]
    activation_handler = activation_handler[: activation_handler.index("def ", 4)]
    assert "if _startup_smoke_mode():" in activation_handler
    assert activation_handler.index("if _startup_smoke_mode():") < activation_handler.index(
        "self._windows_preset_10_hotkey.register()"
    )
