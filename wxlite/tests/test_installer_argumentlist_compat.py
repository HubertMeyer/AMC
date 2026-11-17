"""Rzeczywisty kontrakt cytowania argumentów dla Windows PowerShell 5.1."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "wxlite" / "tools" / "Start-ArgumentListSafeProcess.ps1"
BUILD = ROOT / "wxlite" / "tools" / "Build-AMCInstaller.ps1"
POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")


def _powershell_path(path: Path) -> str:
    """Mapuj WSL do ścieżki UNC tylko dla rzeczywistego hosta Windows."""

    unc_root = os.environ.get("AMC_WSL_UNC_ROOT")
    if unc_root and path.is_relative_to(ROOT):
        return unc_root.rstrip("\\/") + "\\" + str(path.relative_to(ROOT)).replace("/", "\\")
    return str(path)


@pytest.mark.skipif(
    os.name != "nt" or not POWERSHELL,
    reason="wymaga natywnego Windows Python i PowerShell; kompilacja fixture w POSIX/UNC z WSL nie jest wspierana",
)
def test_powershell_51_fallback_preserves_real_exe_argv(tmp_path: Path) -> None:
    """Fixture .exe odbiera Unicode, spacje, cudzysłowy, backslashe i pusty argument."""

    assert HELPER.is_file(), "brakuje kompatybilnego uruchamiania procesu"
    assert 'Join-Path $PSScriptRoot "Start-ArgumentListSafeProcess.ps1"' in BUILD.read_text(
        encoding="utf-8"
    )

    fixture = tmp_path / "argv-fixture.exe"
    captured = tmp_path / "captured.txt"
    driver = tmp_path / "run-fixture.ps1"
    helper = _powershell_path(HELPER).replace("'", "''")
    fixture_text = str(fixture).replace("'", "''")
    captured_text = str(captured).replace("'", "''")
    working_directory_text = str(tmp_path).replace("'", "''")
    driver.write_text(
        f"""$ErrorActionPreference = 'Stop'
. '{helper}'
Add-Type -OutputType ConsoleApplication -OutputAssembly '{fixture_text}' -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
public static class Program
{{
    public static int Main(string[] args)
    {{
        if (args.Length < 2 || args[0] != "--out") return 2;
        var lines = new List<string>();
        for (var i = 2; i < args.Length; i++)
            lines.Add(Convert.ToBase64String(Encoding.UTF8.GetBytes(args[i])));
        File.WriteAllLines(args[1], lines.ToArray(), Encoding.ASCII);
        return 0;
    }}
}}
'@
$expected = @('dwie spacje', 'zażółć gęślą', 'cytat"wewnątrz', 'C:\\koniec\\', '')
$process = Start-ArgumentListSafeProcess -FilePath '{fixture_text}' -ArgumentList (@('--out', '{captured_text}') + $expected) -WorkingDirectory '{working_directory_text}'
try {{
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {{ throw "fixture zakończył się kodem $($process.ExitCode)" }}
}}
finally {{
    $process.Dispose()
}}
""",
        encoding="utf-8-sig",
    )
    completed = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(driver)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    decoded = [base64.b64decode(line).decode("utf-8") for line in captured.read_text(encoding="ascii").splitlines()]
    assert decoded == ["dwie spacje", "zażółć gęślą", 'cytat"wewnątrz', "C:\\koniec\\", ""]


@pytest.mark.skipif(
    os.name != "nt" or not POWERSHELL,
    reason="wymaga natywnego Windows Python i PowerShell; fixture procesu nie działa z WSL/UNC",
)
def test_process_evidence_preserves_nonzero_fixture_exit(tmp_path: Path) -> None:
    """Niezerowy kod fixture'a pozostawia argv, EXE, katalog i kod wyjścia."""

    fixture = tmp_path / "failing-fixture.exe"
    evidence = tmp_path / "process-evidence.json"
    driver = tmp_path / "run-fixture.ps1"
    helper = _powershell_path(HELPER).replace("'", "''")
    fixture_text = str(fixture).replace("'", "''")
    evidence_text = str(evidence).replace("'", "''")
    working_directory_text = str(tmp_path).replace("'", "''")
    driver.write_text(
        f"""$ErrorActionPreference = 'Stop'
. '{helper}'
Add-Type -OutputType ConsoleApplication -OutputAssembly '{fixture_text}' -TypeDefinition @'
public static class Program
{{
    public static int Main(string[] args) {{ return 23; }}
}}
'@
$result = Invoke-ArgumentListSafeProcessWithEvidence -FilePath '{fixture_text}' -ArgumentList @('argument ze spacją') -WorkingDirectory '{working_directory_text}' -SourcePath '{fixture_text}' -EvidencePath '{evidence_text}'
if ($result.ExitCode -ne 23) {{ throw "fixture zakończył się kodem $($result.ExitCode)" }}
""",
        encoding="utf-8-sig",
    )
    assert POWERSHELL is not None
    completed = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(driver)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(evidence.read_text(encoding="utf-8-sig"))
    assert payload["state"] == "exited"
    assert payload["filePath"] == str(fixture)
    assert payload["workingDirectory"] == str(tmp_path)
    assert payload["sourcePath"] == str(fixture)
    assert payload["argumentList"] == ["argument ze spacją"]
    assert payload["exitCode"] == 23


@pytest.mark.skipif(
    os.name != "nt" or not POWERSHELL,
    reason="wymaga natywnego Windows Python i PowerShell; fixture procesu nie działa z WSL/UNC",
)
def test_process_evidence_fails_closed_before_fixture_starts(tmp_path: Path) -> None:
    """Brak zapisywalnego dowodu zatrzymuje proces przed startem fixture'a."""

    fixture = tmp_path / "marker-fixture.exe"
    marker = tmp_path / "started.txt"
    driver = tmp_path / "run-fail-closed.ps1"
    helper = _powershell_path(HELPER).replace("'", "''")
    fixture_text = str(fixture).replace("'", "''")
    marker_text = str(marker).replace("'", "''")
    working_directory_text = str(tmp_path).replace("'", "''")
    driver.write_text(
        f"""$ErrorActionPreference = 'Stop'
. '{helper}'
Add-Type -OutputType ConsoleApplication -OutputAssembly '{fixture_text}' -TypeDefinition @'
using System.IO;
public static class Program
{{
    public static int Main(string[] args) {{ File.WriteAllText(args[0], "started"); return 0; }}
}}
'@
$evidenceWriteFailed = $false
try {{
    Invoke-ArgumentListSafeProcessWithEvidence -FilePath '{fixture_text}' -ArgumentList @('{marker_text}') -WorkingDirectory '{working_directory_text}' -SourcePath '{fixture_text}' -EvidencePath '{working_directory_text}'
}}
catch {{
    $evidenceWriteFailed = $true
}}
if (-not $evidenceWriteFailed) {{ throw 'dowod w katalogu nie moze zostac zapisany jako sukces' }}
if (Test-Path -LiteralPath '{marker_text}') {{ throw 'fixture wystartowal mimo braku zapisywalnego dowodu' }}
""",
        encoding="utf-8-sig",
    )
    assert POWERSHELL is not None
    completed = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(driver)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert not marker.exists()
