"""REL-001: wdrożenie Workera pozostaje jawne i fail-closed."""

from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPOSITORY_ROOT
    / "deploy"
    / "amc-sygnalista-worker"
    / "Deploy-AMCSygnalistaWorker.ps1"
)
LOCK = REPOSITORY_ROOT / "deploy" / "amc-sygnalista-worker" / "package-lock.json"
CONFIGURATION_TEMPLATE = (
    REPOSITORY_ROOT / "deploy" / "amc-sygnalista-worker" / "wrangler.jsonc.example"
)


def test_worker_dependencies_are_locked_to_the_pinned_wrangler() -> None:
    text = LOCK.read_text(encoding="utf-8")
    assert '"lockfileVersion": 3' in text
    assert '"wrangler": "4.151.3"' in text


def test_deployment_is_opt_in_and_never_starts_login() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "[switch]$Bootstrap" in source
    assert "[switch]$SetGitHubToken" in source
    assert "[switch]$Deploy" in source
    assert "[switch]$ActivateEndpoint" in source
    assert "if (-not $performRemoteAction)" in source
    assert "Niczego nie wdrożono" in source
    assert "wrangler whoami" in source
    assert "wrangler login" not in source
    assert "secret list --format json" in source
    assert "secret list --json" not in source
    assert 'GITHUB_TOKEN' in source
    assert '[string]$WorkerBaseUrl = ""' in source
    assert 'if (($Bootstrap -or $Deploy) -and -not [string]::IsNullOrWhiteSpace($WorkerBaseUrl)) {' in source


def test_first_deploy_uses_ignored_local_config_and_durable_coordinator() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    configuration = CONFIGURATION_TEMPLATE.read_text(encoding="utf-8")
    assert '"name": "REPORT_COORDINATORS"' in configuration
    assert '"new_sqlite_classes": ["ReportCoordinator"]' in configuration
    assert "Copy-Item -LiteralPath $configurationTemplatePath" in source
    assert 'Destination $configurationPath' in source
    assert "wrangler.jsonc" in (
        REPOSITORY_ROOT / "deploy" / "amc-sygnalista-worker" / ".gitignore"
    ).read_text(encoding="utf-8")
    bootstrap = source[
        source.index("if ($Bootstrap) {") : source.index("if ($SetGitHubToken) {")
    ]
    assert "Worker już istnieje" in bootstrap
    assert "Invoke-WorkerDeployment" in bootstrap
    assert "New-WorkerBootstrapConfiguration $bootstrapConfigurationPath" in bootstrap
    assert "Invoke-WorkerDeployment $bootstrapConfigurationPath" in bootstrap
    assert "Remove-Item -LiteralPath $bootstrapConfigurationPath" in bootstrap
    assert "Assert-WorkerBootstrapState" in bootstrap
    assert "nieaktywnym stanie 503" in source
    assert "bez aktywacji endpointu AMC" in bootstrap
    assert "ActivateEndpoint" not in bootstrap


def test_github_secret_is_a_separate_explicit_interactive_step() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    secret_step = source[
        source.index("if ($SetGitHubToken) {") : source.index(
            "if (-not ($secretInventory.Names"
        )
    ]
    assert "wrangler secret put GITHUB_TOKEN" in secret_step
    assert "interaktywnie" in secret_step
    assert "od razu wdraża nową wersję Workera" in secret_step
    assert "Get-WorkerSecretInventory" in secret_step
    assert "Endpoint AMC nadal pozostaje wyłączony" in secret_step
    assert "Read-Host" not in secret_step


def test_workers_dev_address_is_read_from_confirmed_deployment_output() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert '$output = @(& $npmPath exec -- wrangler deploy 2>&1)' in source
    assert '$output = @(& $npmPath exec -- wrangler deploy --config $ConfigPath 2>&1)' in source
    assert 'ExitCode = $LASTEXITCODE' in source
    assert '\\.workers\\.dev' in source
    assert 'Get-ValidatedWorkerBaseUrl $workerAddress.Value' in source
    assert 'Uruchom skrypt ponownie z -WorkerBaseUrl' in source


def test_local_gate_packs_worker_without_deploying_or_requiring_an_endpoint() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    local_gate = source[
        source.index("if (-not $performRemoteAction)") : source.index("# Skrypt nigdy")
    ]
    assert "wrangler deploy --dry-run" in local_gate
    assert "Copy-Item -LiteralPath $configurationTemplatePath" in local_gate
    assert "New-WorkerBootstrapConfiguration $bootstrapDryRunConfigurationPath" in local_gate
    assert "Lokalne pakowanie bootstrapu Workera nie powiodło się" in local_gate
    assert "$dryRunConfigurationPath" in local_gate
    assert "GetTempPath" in local_gate
    assert "Remove-Item -LiteralPath $dryRunConfigurationPath" in local_gate
    assert "Remove-Item -LiteralPath $bootstrapDryRunConfigurationPath" in local_gate
    assert "Remove-Item -LiteralPath $dryRunRoot" in local_gate
    assert "WorkerBaseUrl" not in local_gate


def test_health_is_verified_before_atomic_endpoint_activation() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    readiness_position = source.index('Assert-WorkerReadiness $baseUrl')
    activation_position = source.index('if ($ActivateEndpoint) {', readiness_position)
    readiness_functions = source[
        source.index('function Assert-WorkerHealth') : source.index('Push-Location')
    ]
    assert readiness_position < activation_position
    assert '"$WorkerBaseUrl/health" "GET"' in readiness_functions
    assert '"$WorkerBaseUrl/v1/report" "GET"' in readiness_functions
    assert "'{\"schemaVersion\":999}'" in readiness_functions
    assert 'StatusCode -ne 405' in readiness_functions
    assert 'StatusCode -ne 400' in readiness_functions
    assert 'Nieobsługiwana wersja raportu' in readiness_functions
    assert '[IO.File]::Move($temporaryPath, $endpointPath, $true)' in source
    assert 'https' in source
    assert 'UZUPELNIJ_IDENTYFIKATOR_KV' not in source
