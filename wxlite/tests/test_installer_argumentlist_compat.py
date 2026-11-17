"""Rzeczywisty kontrakt cytowania argumentów dla Windows PowerShell 5.1."""

from __future__ import annotations

import base64
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


@pytest.mark.skipif(not POWERSHELL, reason="wymaga Windows PowerShell")
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
