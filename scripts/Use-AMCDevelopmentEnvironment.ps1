[CmdletBinding()]
param(
    [string]$DependencyRoot = "D:\Projekty Codex\AMC - zależności",
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DependencyRoot = [IO.Path]::GetFullPath($DependencyRoot)
$rustVersion = "1.98.1"
$nodeVersion = "22.23.2"
$pnpmVersion = "11.25.0"
$pytestVersion = "9.0.2"
$wheelName = "wxpython-4.3.1-cp314-cp314-win_amd64.whl"
$wheelSha256 = "bbb4cefea441cba77f81b0ac2f7445f0ad01f18fee3b72a78ed48298b3f8f0ab"

function Get-VsWherePath {
    foreach ($candidate in @(
        "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        "C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe",
        "C:\BuildTools\Common7\Tools\vswhere.exe"
    )) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    return $null
}

function Get-BuildToolsRoot {
    $vswhere = Get-VsWherePath
    if ($null -ne $vswhere) {
        $found = & $vswhere -latest -products * `
            -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
            -property installationPath
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($found)) {
            return ([string]$found).Trim()
        }
    }
    if (Test-Path -LiteralPath "C:\BuildTools\VC\Auxiliary\Build\vcvars64.bat") {
        return "C:\BuildTools"
    }
    return $null
}

function Add-PathPrefix {
    param([Parameter(Mandatory)] [string[]]$Paths)

    $all = [Collections.Generic.List[string]]::new()
    foreach ($path in @($Paths) + @($env:PATH -split ";")) {
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        if (-not $all.Contains($path)) { [void]$all.Add($path) }
    }
    $env:PATH = $all -join ";"
}

$cargoHome = Join-Path $DependencyRoot "cargo"
$rustupHome = Join-Path $DependencyRoot "rustup"
$cargoBin = Join-Path $cargoHome "bin"
$rustToolchainRoot = Join-Path $rustupHome "toolchains\${rustVersion}-x86_64-pc-windows-msvc"
$rustCompiler = Join-Path $rustToolchainRoot "bin\rustc.exe"
$rustTargetLibrary = Join-Path $rustToolchainRoot "lib\rustlib\x86_64-pc-windows-msvc"
$nodeRoot = Join-Path $DependencyRoot "node\node-v$nodeVersion-win-x64"
$pnpmHome = Join-Path $DependencyRoot "pnpm\$pnpmVersion"
$nodeExecutable = Join-Path $nodeRoot "node.exe"
$pnpmCli = Join-Path $pnpmHome "node_modules\pnpm\bin\pnpm.cjs"
$wheelPath = Join-Path $DependencyRoot "python-cache\$wheelName"
$pythonTest = Join-Path $DependencyRoot "python-test-envs\wxpython-4.3.1-cp314\Scripts\python.exe"
$pytestWheel = Join-Path $DependencyRoot "python-cache\pytest-$pytestVersion-py3-none-any.whl"
$nugetOfflineSource = Join-Path $DependencyRoot "nuget-offline-source"
$buildToolsRoot = Get-BuildToolsRoot
$vcvars = if ($null -eq $buildToolsRoot) { "" } else { Join-Path $buildToolsRoot "VC\Auxiliary\Build\vcvars64.bat" }

$requiredFiles = [ordered]@{
    "rustup" = Join-Path $cargoBin "rustup.exe"
    "rustc $rustVersion" = $rustCompiler
    "cargo" = Join-Path $cargoBin "cargo.exe"
    "Node.js" = $nodeExecutable
    "pnpm" = Join-Path $pnpmHome "pnpm.cmd"
    "pnpm CLI" = $pnpmCli
    "wheel wxPython" = $wheelPath
    "środowisko testowe wxPython" = $pythonTest
    "wheel pytest" = $pytestWheel
    "vcvars64.bat" = $vcvars
}

$missing = [Collections.Generic.List[string]]::new()
foreach ($entry in $requiredFiles.GetEnumerator()) {
    if ([string]::IsNullOrWhiteSpace($entry.Value) -or
        -not (Test-Path -LiteralPath $entry.Value -PathType Leaf)) {
        [void]$missing.Add("$($entry.Key): $($entry.Value)")
    }
}
foreach ($directory in @(
    (Join-Path $DependencyRoot "nuget"),
    $nugetOfflineSource,
    (Join-Path $DependencyRoot "pnpm-store"),
    (Join-Path $DependencyRoot "pnpm-cache"),
    $rustTargetLibrary
)) {
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        [void]$missing.Add("katalog cache: $directory")
    }
}

if (Test-Path -LiteralPath $wheelPath -PathType Leaf) {
    $actualWheelSha256 = (Get-FileHash -LiteralPath $wheelPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualWheelSha256 -ne $wheelSha256) {
        [void]$missing.Add("wheel wxPython ma niezgodną sumę SHA-256: $actualWheelSha256")
    }
}

$sdkDirectories = @(
    Get-ChildItem -LiteralPath "C:\Program Files (x86)\Windows Kits\10\Lib" `
        -Directory -ErrorAction SilentlyContinue
)
if ($sdkDirectories.Count -eq 0) {
    [void]$missing.Add("Windows SDK 10")
}

if ($missing.Count -gt 0) {
    throw "Środowisko AMC jest niekompletne:`n - $($missing -join "`n - ")"
}

$rustcVersion = & $rustCompiler --version
if ($LASTEXITCODE -ne 0 -or $rustcVersion -notmatch "^rustc $([Regex]::Escape($rustVersion))\b") {
    throw "Brak dokładnego toolchainu Rust $rustVersion. Odczytano: $rustcVersion"
}
$actualNodeVersion = & $nodeExecutable --version
if ($LASTEXITCODE -ne 0 -or $actualNodeVersion.Trim() -ne "v$nodeVersion") {
    throw "Niezgodna wersja Node.js: $actualNodeVersion"
}
$actualPnpmVersion = & $nodeExecutable $pnpmCli --version
if ($LASTEXITCODE -ne 0 -or $actualPnpmVersion.Trim() -ne $pnpmVersion) {
    throw "Niezgodna wersja pnpm: $actualPnpmVersion"
}
$pythonPackages = & $pythonTest -c "import pytest, wx; print(pytest.__version__); print(wx.__version__)"
if ($LASTEXITCODE -ne 0 -or $pythonPackages.Count -lt 2 -or
    $pythonPackages[0].Trim() -ne $pytestVersion -or $pythonPackages[1].Trim() -ne "4.3.1") {
    throw "Niezgodne środowisko testowe Pythona: $($pythonPackages -join '; ')"
}
$offlinePackageCount = @(
    Get-ChildItem -LiteralPath $nugetOfflineSource -File -Filter "*.nupkg" -ErrorAction SilentlyContinue
).Count
if ($offlinePackageCount -eq 0) {
    throw "Lokalne źródło NuGet nie zawiera pakietów."
}
$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
if ($null -eq $dotnet) {
    throw "Brak .NET SDK 8.0.423."
}
$dotnetSdks = @(& $dotnet.Source --list-sdks)
if (-not ($dotnetSdks | Where-Object { $_ -match "^8\.0\.423\s" })) {
    throw "Brak przypiętego .NET SDK 8.0.423. Odczytano: $($dotnetSdks -join '; ')"
}

if ($CheckOnly) {
    Write-Host "Środowisko AMC jest kompletne: $DependencyRoot"
    Write-Host "Rust: $rustcVersion; target x86_64-pc-windows-msvc"
    Write-Host "Node.js: $actualNodeVersion; pnpm: $actualPnpmVersion"
    Write-Host ".NET SDK: 8.0.423"
    Write-Host "Lokalne pakiety NuGet: $offlinePackageCount"
    Write-Host "MSVC: $buildToolsRoot; Windows SDK: $($sdkDirectories[-1].Name)"
    return
}

$environmentLines = & cmd.exe /d /s /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE -ne 0) {
    throw "Nie udało się ustawić środowiska MSVC przez vcvars64.bat."
}
foreach ($line in $environmentLines) {
    if ($line -match "^([^=]+)=(.*)$") {
        Set-Item -Path ("Env:" + $Matches[1]) -Value $Matches[2]
    }
}
# vcvars ustawia ogólną zmienną Platform=x64. MSBuild traktuje ją jako
# globalną platformę rozwiązania, a AMC ma konfigurację "Any CPU". Pozostałe
# zmienne VSCMD/VC/WindowsSdk wystarczają kompilatorowi C++.
Remove-Item Env:Platform -ErrorAction SilentlyContinue

$env:AMC_DEVELOPMENT_DEPENDENCIES = $DependencyRoot
$env:RUSTUP_HOME = $rustupHome
$env:CARGO_HOME = $cargoHome
$env:CARGO_TARGET_DIR = Join-Path $DependencyRoot "cargo-target"
$env:RUSTUP_TOOLCHAIN = "${rustVersion}-x86_64-pc-windows-msvc"
$env:RUSTFLAGS = "-C target-feature=+crt-static"
$env:NUGET_PACKAGES = Join-Path $DependencyRoot "nuget"
$env:NUGET_HTTP_CACHE_PATH = Join-Path $DependencyRoot "nuget-http-cache"
$env:NUGET_PLUGINS_CACHE_PATH = Join-Path $DependencyRoot "nuget-plugins-cache"
$env:DOTNET_CLI_HOME = Join-Path $DependencyRoot "dotnet-home"
$env:DOTNET = $dotnet.Source
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = "1"
$env:DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE = "1"
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE = "false"
$env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH = "false"
$env:PNPM_HOME = $pnpmHome
$env:npm_config_store_dir = Join-Path $DependencyRoot "pnpm-store"
$env:npm_config_cache = Join-Path $DependencyRoot "npm-cache"
$env:PIP_CACHE_DIR = Join-Path $DependencyRoot "pip-cache"
$env:UV_CACHE_DIR = Join-Path $DependencyRoot "uv-cache"
$env:TEMP = Join-Path $DependencyRoot "tmp"
$env:TMP = $env:TEMP
$env:AMC_PYTHON_TEST_PYTHON = $pythonTest

Add-PathPrefix -Paths @($cargoBin, $nodeRoot, $pnpmHome)

Write-Host "Ustawiono trwałe środowisko deweloperskie AMC: $DependencyRoot"
