"""Statyczny kontrakt jednorazowej chronionej budowy AMC Public i Test."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "amc-protected-public-test-build.yml"


def _workflow() -> str:
    assert WORKFLOW_PATH.is_file(), "Brak workflow chronionej budowy Public/Test."
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_workflow_is_one_shot_read_only_and_targets_exact_new_branch() -> None:
    workflow = _workflow()
    for required in (
        "codex/amc-protected-public-test-20261118-issue21",
        "github.run_attempt == '1'",
        "github.event.before == '0000000000000000000000000000000000000000'",
        "github.ref == 'refs/heads/codex/amc-protected-public-test-20261118-issue21'",
        "runs-on: windows-2025",
        "contents: read",
        "persist-credentials: false",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ):
        assert required in workflow
    for forbidden in (
        "workflow_dispatch",
        "self-hosted",
        "actions/cache",
        "Publish-AMCRelease",
        "gh release",
        "permissions: write",
        "strategy:",
    ):
        assert forbidden not in workflow


def test_workflow_builds_public_then_test_from_one_source_revision() -> None:
    workflow = _workflow()
    public_bundle = "Build-AMCBundle.ps1 -Profile public"
    test_bundle = "Build-AMCBundle.ps1 -Profile test"
    public_installer = "Build-AMCInstaller.ps1 -Profile public"
    test_installer = "Build-AMCInstaller.ps1 -Profile test"
    for required in (
        "sourceSha = (git rev-parse HEAD).Trim()",
        "sourceVersion",
        "0.1.0-alpha.511",
        public_bundle,
        test_bundle,
        public_installer,
        test_installer,
        "-AppleMusicSitePackages $env:AMC_SITE_PACKAGES",
        "-Profile public",
        "-Profile test",
    ):
        assert required in workflow
    assert workflow.index(public_bundle) < workflow.index(test_bundle)
    assert workflow.index(public_installer) < workflow.index(test_installer)
    assert "-AppleMusicSitePackages $env:AMC_SITE_PACKAGES" in workflow[workflow.index(test_bundle):]
    assert "-AppleMusicSitePackages $env:AMC_SITE_PACKAGES" not in workflow[:workflow.index(test_bundle)]


def test_workflow_reuses_fail_closed_defender_gates_and_separate_profile_evidence() -> None:
    workflow = _workflow()
    for required in (
        "Enable-AMCDiagnosticProtection.ps1",
        "Start-MpScan -ScanType CustomScan",
        "-WarningAction Continue -WarningVariable +diagWarnings",
        "NoMatchingEventsFound",
        "$jobStarted",
        "Get-MpThreatDetection",
        "public-bundle.json",
        "public-installer.json",
        "test-bundle.json",
        "test-installer.json",
        "final-defender-audit.json",
        "if: success()",
        "if: always()",
    ):
        assert required in workflow
    assert workflow.count("Invoke-DefenderGate -Target") >= 10


def test_canonical_builders_scan_before_each_candidate_execution() -> None:
    bundle = (ROOT / "wxlite" / "tools" / "Build-AMCBundle.ps1").read_text(encoding="utf-8-sig")
    installer = (ROOT / "wxlite" / "tools" / "Build-AMCInstaller.ps1").read_text(encoding="utf-8-sig")
    for source in (bundle, installer):
        assert "[scriptblock]$BeforeCandidateExecution = $null" in source
        assert "function Invoke-BeforeCandidateExecution" in source
    assert bundle.index("components-before-apple-music-web-pipe") < bundle.index("Test-AppleMusicWebPipe.ps1")
    assert bundle.index("candidate-before-first-execution") < bundle.index("Invoke-FullBundleCheck -LauncherPath")
    assert installer.index("bundle-before-installer-checks") < installer.index("Start-Process -FilePath $launcher")
