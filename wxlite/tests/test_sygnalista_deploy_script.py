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


def test_worker_dependencies_are_locked_to_the_pinned_wrangler() -> None:
    text = LOCK.read_text(encoding="utf-8")
    assert '"lockfileVersion": 3' in text
    assert '"wrangler": "4.151.3"' in text


def test_deployment_is_opt_in_and_never_starts_login() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "[switch]$Deploy" in source
    assert "[switch]$ActivateEndpoint" in source
    assert "if (-not $Deploy)" in source
    assert "Niczego nie wdrożono" in source
    assert "wrangler whoami" in source
    assert "wrangler login" not in source
    assert "secret list --json" in source
    assert 'GITHUB_TOKEN' in source


def test_health_is_verified_before_atomic_endpoint_activation() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    health_position = source.index('Invoke-WebRequest')
    activation_position = source.index('if ($ActivateEndpoint) {', health_position)
    assert source.index('schemaVersion') < activation_position
    assert '[IO.File]::Move($temporaryPath, $endpointPath, $true)' in source
    assert 'https' in source
    assert 'UZUPELNIJ_IDENTYFIKATOR_KV' in source
