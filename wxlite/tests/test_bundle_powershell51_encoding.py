"""Kanoniczne wejścia budowy muszą parsować się także w Windows PS 5.1."""
from __future__ import annotations

import base64
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which("powershell.exe")


@pytest.mark.skipif(not POWERSHELL, reason="wymaga rzeczywistego Windows PowerShell 5.1")
@pytest.mark.parametrize("filename", ["Build-AMCBundle.ps1", "Test-AMCBundleStartup.ps1"])
def test_bundle_entrypoint_parses_in_windows_powershell_51(filename: str) -> None:
    assert POWERSHELL is not None
    path = ROOT / "wxlite" / "tools" / filename
    native_path = str(path)
    if os.name != "nt":
        native_path = subprocess.check_output(["wslpath", "-w", str(path)], text=True).strip()
    quoted_path = native_path.replace("'", "''")
    command = f"""$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$tokens=$null; $parseErrors=$null
[void][System.Management.Automation.Language.Parser]::ParseFile('{quoted_path}', [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) {{ $parseErrors | ForEach-Object {{ Write-Output $_.Message }}; exit 1 }}
Write-Output 'PARSE_OK'
"""
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-EncodedCommand", base64.b64encode(command.encode("utf-16-le")).decode("ascii")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PARSE_OK" in result.stdout
