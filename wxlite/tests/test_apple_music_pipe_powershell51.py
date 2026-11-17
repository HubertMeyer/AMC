"""Exercise the real hidden pipe check with an explicitly supplied built host."""
from __future__ import annotations

import base64
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which("powershell.exe")
HOST = os.environ.get("AMC_APPLE_MUSIC_WEB_HOST")


@pytest.mark.skipif(
    not POWERSHELL or not HOST,
    reason="requires Windows PowerShell 5.1 and AMC_APPLE_MUSIC_WEB_HOST pointing to an actual built Windows host",
)
def test_real_apple_music_host_pipe_in_windows_powershell51():
    assert POWERSHELL is not None and HOST is not None
    script = ROOT / "wxlite/tools/Test-AppleMusicWebPipe.ps1"
    native_script = str(script)
    if os.name != "nt":
        native_script = subprocess.check_output(["wslpath", "-w", str(script)], text=True).strip()
    quoted_script = native_script.replace("'", "''")
    quoted_host = HOST.replace("'", "''")
    command = f"""$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) {{ throw 'requires PowerShell 5.1' }}
& '{quoted_script}' -Executable '{quoted_host}'
"""
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand",
         base64.b64encode(command.encode("utf-16-le")).decode("ascii")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Potok procesu Apple Music: OK" in result.stdout
