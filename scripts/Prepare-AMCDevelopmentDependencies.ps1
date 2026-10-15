[CmdletBinding()]
param(
    [string]$DependencyRoot = "D:\Projekty Codex\AMC - zależności",
    [string]$InstalledAmcRoot = "D:\Projekty Codex\AMC Python",
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$DependencyRoot = [IO.Path]::GetFullPath($DependencyRoot)
$InstalledAmcRoot = [IO.Path]::GetFullPath($InstalledAmcRoot)
$UseEnvironmentScript = Join-Path $PSScriptRoot "Use-AMCDevelopmentEnvironment.ps1"
$RustVersion = "1.98.1"
$RustTarget = "x86_64-pc-windows-msvc"
$NodeVersion = "22.23.2"
$PnpmVersion = "11.25.0"
$PytestVersion = "9.0.2"
$WheelName = "wxpython-4.3.1-cp314-cp314-win_amd64.whl"
$WheelSha256 = "bbb4cefea441cba77f81b0ac2f7445f0ad01f18fee3b72a78ed48298b3f8f0ab"

function Invoke-Checked {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [string[]]$ArgumentList,
        [Parameter(Mandatory)] [string]$Stage
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "$Stage zakończył się kodem $LASTEXITCODE."
    }
}

function Save-OfficialFile {
    param(
        [Parameter(Mandatory)] [uri]$Uri,
        [Parameter(Mandatory)] [string]$Destination
    )

    if (Test-Path -LiteralPath $Destination -PathType Leaf) { return }
    Invoke-WebRequest -Uri $Uri -OutFile $Destination -UseBasicParsing
}

function Get-VsWherePath {
    foreach ($candidate in @(
        "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        "C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe",
        "C:\BuildTools\Common7\Tools\vswhere.exe"
    )) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
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

function Assert-PrivatePython {
    $python = Join-Path $InstalledAmcRoot "runtime\python.exe"
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw "Brak prywatnego runtime'u AMC: $python"
    }
    $lines = & $python -c "import sys, wx; print(sys.version.split()[0]); print(wx.__version__); print(wx.version())"
    if ($LASTEXITCODE -ne 0 -or $lines.Count -lt 3) {
        throw "Prywatny runtime AMC nie importuje wxPython."
    }
    if ($lines[0].Trim() -ne "3.14.7" -or $lines[1].Trim() -ne "4.3.1" -or
        $lines[2] -notmatch "wxWidgets 3\.3\.3") {
        throw "Niezgodny prywatny runtime AMC: $($lines -join '; ')"
    }
    Write-Host "Prywatny runtime: Python $($lines[0]), wxPython $($lines[1]), wxWidgets 3.3.3"
}

function Assert-WebView2Runtime {
    $registrations = @(
        Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\*" `
            -ErrorAction SilentlyContinue
        Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\*" `
            -ErrorAction SilentlyContinue
    ) | Where-Object { $_.name -match "WebView2" -and -not [string]::IsNullOrWhiteSpace($_.pv) }
    if ($registrations.Count -eq 0) {
        throw "Brak Microsoft Edge WebView2 Runtime."
    }
    Write-Host "WebView2 Runtime: $($registrations[0].pv)"
}

if ($CheckOnly) {
    & $UseEnvironmentScript -DependencyRoot $DependencyRoot -CheckOnly
    Assert-PrivatePython
    Assert-WebView2Runtime
    Write-Host "Kontrola środowiska AMC zakończona pomyślnie; niczego nie pobrano ani nie zainstalowano."
    return
}

$directories = @(
    "downloads", "metadata", "rustup", "cargo", "cargo-target", "node",
    "pnpm", "pnpm-store", "pnpm-cache", "pnpm-virtual-store", "npm-cache", "python-cache",
    "python-test-envs", "pip-cache", "uv-cache", "nuget", "nuget-http-cache",
    "nuget-plugins-cache", "nuget-offline-source", "nuget-offline-verify",
    "dotnet-home", "tmp"
)
foreach ($directory in $directories) {
    New-Item -ItemType Directory -Path (Join-Path $DependencyRoot $directory) -Force | Out-Null
}
$env:TEMP = Join-Path $DependencyRoot "tmp"
$env:TMP = $env:TEMP

# Rustup jest pobierany z oficjalnej dystrybucji, a jego suma z osobnego
# oficjalnego pliku SHA-256. Instalacja nie modyfikuje globalnej zmiennej PATH.
$rustupInit = Join-Path $DependencyRoot "downloads\rustup-init-$RustTarget.exe"
$rustupShaFile = "$rustupInit.sha256"
$rustupUri = "https://static.rust-lang.org/rustup/dist/$RustTarget/rustup-init.exe"
Save-OfficialFile -Uri $rustupUri -Destination $rustupInit
Save-OfficialFile -Uri "$rustupUri.sha256" -Destination $rustupShaFile
$expectedRustupSha = ((Get-Content -LiteralPath $rustupShaFile -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
$actualRustupSha = (Get-FileHash -LiteralPath $rustupInit -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualRustupSha -ne $expectedRustupSha) {
    throw "Niezgodna suma rustup-init: $actualRustupSha zamiast $expectedRustupSha."
}
$env:RUSTUP_HOME = Join-Path $DependencyRoot "rustup"
$env:CARGO_HOME = Join-Path $DependencyRoot "cargo"
$env:CARGO_TARGET_DIR = Join-Path $DependencyRoot "cargo-target"
$rustup = Join-Path $env:CARGO_HOME "bin\rustup.exe"
if (-not (Test-Path -LiteralPath $rustup -PathType Leaf)) {
    Invoke-Checked -FilePath $rustupInit -ArgumentList @(
        "-y", "--no-modify-path", "--profile", "minimal",
        "--default-host", $RustTarget, "--default-toolchain", $RustVersion
    ) -Stage "Instalacja rustup"
}
$rustToolchainRoot = Join-Path $env:RUSTUP_HOME "toolchains\${RustVersion}-$RustTarget"
if (-not (Test-Path -LiteralPath (Join-Path $rustToolchainRoot "bin\rustc.exe") -PathType Leaf)) {
    Invoke-Checked -FilePath $rustup -ArgumentList @(
        "toolchain", "install", $RustVersion, "--profile", "minimal", "--no-self-update"
    ) -Stage "Instalacja toolchainu Rust $RustVersion"
}
if (-not (Test-Path -LiteralPath (Join-Path $rustToolchainRoot "lib\rustlib\$RustTarget") -PathType Container)) {
    Invoke-Checked -FilePath $rustup -ArgumentList @(
        "target", "add", $RustTarget, "--toolchain", $RustVersion
    ) -Stage "Instalacja targetu Rust $RustTarget"
}

# Pełne Visual Studio nie jest potrzebne. Instalowany jest tylko oficjalny
# workload narzędzi C++ wraz z zalecanym SDK.
$buildToolsRoot = Get-BuildToolsRoot
if ($null -eq $buildToolsRoot) {
    $buildToolsInstaller = Join-Path $DependencyRoot "downloads\vs_BuildTools_17_bootstrapper.exe"
    Save-OfficialFile -Uri "https://aka.ms/vs/17/release/vs_BuildTools.exe" `
        -Destination $buildToolsInstaller
    $signature = Get-AuthenticodeSignature -LiteralPath $buildToolsInstaller
    if ($signature.Status -ne [Management.Automation.SignatureStatus]::Valid -or
        $signature.SignerCertificate.Subject -notmatch "Microsoft Corporation") {
        throw "Instalator Visual Studio Build Tools nie ma prawidłowego podpisu Microsoftu."
    }
    $process = Start-Process -FilePath $buildToolsInstaller -ArgumentList @(
        "--quiet", "--wait", "--norestart", "--nocache",
        "--installPath", "C:\BuildTools",
        "--add", "Microsoft.VisualStudio.Workload.VCTools", "--includeRecommended"
    ) -Verb RunAs -Wait -PassThru
    if ($process.ExitCode -notin @(0, 3010)) {
        throw "Visual Studio Build Tools zakończył instalację kodem $($process.ExitCode)."
    }
    $buildToolsRoot = Get-BuildToolsRoot
}
if ($null -eq $buildToolsRoot) {
    throw "Brak MSVC v143 po przygotowaniu Visual Studio Build Tools."
}
$windowsSdk = @(
    Get-ChildItem -LiteralPath "C:\Program Files (x86)\Windows Kits\10\Lib" `
        -Directory -ErrorAction SilentlyContinue
)
if ($windowsSdk.Count -eq 0) { throw "Brak Windows SDK 10."
}

# Node pochodzi z oficjalnego archiwum w konkretnej wersji i jest sprawdzany
# względem oficjalnego SHASUMS256.txt.
$nodeArchiveName = "node-v$NodeVersion-win-x64.zip"
$nodeArchive = Join-Path $DependencyRoot "downloads\$nodeArchiveName"
$nodeSums = Join-Path $DependencyRoot "downloads\node-v$NodeVersion-SHASUMS256.txt"
$nodeBaseUri = "https://nodejs.org/dist/v$NodeVersion"
Save-OfficialFile -Uri "$nodeBaseUri/$nodeArchiveName" -Destination $nodeArchive
Save-OfficialFile -Uri "$nodeBaseUri/SHASUMS256.txt" -Destination $nodeSums
$nodeSumLine = Get-Content -LiteralPath $nodeSums | Where-Object {
    $_ -match [Regex]::Escape($nodeArchiveName)
} | Select-Object -First 1
if ([string]::IsNullOrWhiteSpace($nodeSumLine)) {
    throw "Oficjalny wykaz sum Node.js nie zawiera $nodeArchiveName."
}
$expectedNodeSha = ($nodeSumLine -split "\s+")[0].ToLowerInvariant()
$actualNodeSha = (Get-FileHash -LiteralPath $nodeArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualNodeSha -ne $expectedNodeSha) {
    throw "Niezgodna suma archiwum Node.js: $actualNodeSha zamiast $expectedNodeSha."
}
$nodeRoot = Join-Path $DependencyRoot "node\node-v$NodeVersion-win-x64"
if (-not (Test-Path -LiteralPath (Join-Path $nodeRoot "node.exe") -PathType Leaf)) {
    Expand-Archive -LiteralPath $nodeArchive -DestinationPath (Join-Path $DependencyRoot "node") -Force
}
$node = Join-Path $nodeRoot "node.exe"
$npm = Join-Path $nodeRoot "npm.cmd"
$pnpmHome = Join-Path $DependencyRoot "pnpm\$PnpmVersion"
$pnpm = Join-Path $pnpmHome "pnpm.cmd"
if (-not (Test-Path -LiteralPath $pnpm -PathType Leaf)) {
    Invoke-Checked -FilePath $npm -ArgumentList @(
        "install", "--global", "--prefix", $pnpmHome,
        "--cache", (Join-Path $DependencyRoot "npm-cache"),
        "pnpm@$PnpmVersion", "--no-audit", "--no-fund"
    ) -Stage "Instalacja pnpm $PnpmVersion"
}
$pnpmMetadataPath = Join-Path $DependencyRoot "metadata\pnpm-$PnpmVersion.json"
if (-not (Test-Path -LiteralPath $pnpmMetadataPath -PathType Leaf)) {
    $pnpmMetadata = & $npm view "pnpm@$PnpmVersion" `
        dist.tarball dist.integrity dist.shasum --json
    if ($LASTEXITCODE -ne 0) { throw "Nie udało się odczytać metadanych pnpm $PnpmVersion."
    }
    $pnpmMetadata | Set-Content -LiteralPath $pnpmMetadataPath -Encoding utf8
}

# Dokładny wheel jest pobierany i instalowany bez indeksu do pustego,
# prywatnego środowiska próbnego. Nie zmienia systemowego Pythona.
$systemPython = (Get-Command python -ErrorAction Stop).Source
$pythonCache = Join-Path $DependencyRoot "python-cache"
$wheel = Join-Path $pythonCache $WheelName
if (-not (Test-Path -LiteralPath $wheel -PathType Leaf)) {
    Invoke-Checked -FilePath $systemPython -ArgumentList @(
        "-m", "pip", "download", "--require-hashes", "--only-binary=:all:",
        "--dest", $pythonCache, "-r", (Join-Path $RepositoryRoot "wxlite\requirements-win64.txt")
    ) -Stage "Pobranie wheel wxPython"
}
if (-not (Test-Path -LiteralPath $wheel -PathType Leaf)) {
    throw "Brak dokładnego wheel wxPython: $wheel"
}
$actualWheelSha = (Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualWheelSha -ne $WheelSha256) {
    throw "Niezgodna suma wheel wxPython: $actualWheelSha."
}
$pytestWheel = Join-Path $pythonCache "pytest-$PytestVersion-py3-none-any.whl"
if (-not (Test-Path -LiteralPath $pytestWheel -PathType Leaf)) {
    Invoke-Checked -FilePath $systemPython -ArgumentList @(
        "-m", "pip", "download", "--only-binary=:all:", "--dest", $pythonCache,
        "pytest==$PytestVersion"
    ) -Stage "Pobranie pytest $PytestVersion i jego zależności"
}
if (-not (Test-Path -LiteralPath $pytestWheel -PathType Leaf)) {
    throw "Brak przypiętego wheel pytest: $pytestWheel"
}
$pythonWheelMetadata = @(
    Get-ChildItem -LiteralPath $pythonCache -File -Filter "*.whl" |
        Sort-Object Name |
        ForEach-Object {
            [ordered]@{
                file = $_.Name
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                source = "https://pypi.org/simple/"
            }
        }
)
$pythonWheelMetadata | ConvertTo-Json -Depth 3 |
    Set-Content -LiteralPath (Join-Path $DependencyRoot "metadata\python-test-wheels.json") -Encoding utf8
$pythonTestRoot = Join-Path $DependencyRoot "python-test-envs\wxpython-4.3.1-cp314"
$pythonTest = Join-Path $pythonTestRoot "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonTest -PathType Leaf)) {
    Invoke-Checked -FilePath $systemPython -ArgumentList @("-m", "venv", $pythonTestRoot) `
        -Stage "Tworzenie środowiska testowego Pythona"
}
Invoke-Checked -FilePath $pythonTest -ArgumentList @(
    "-m", "pip", "install", "--no-index", "--find-links", $pythonCache,
    "--require-hashes", "-r", (Join-Path $RepositoryRoot "wxlite\requirements-win64.txt")
) -Stage "Instalacja wxPython z cache offline"
Invoke-Checked -FilePath $pythonTest -ArgumentList @(
    "-m", "pip", "install", "--no-index", "--find-links", $pythonCache,
    "pytest==$PytestVersion"
) -Stage "Instalacja pytest z cache offline"
Invoke-Checked -FilePath $pythonTest -ArgumentList @(
    "-c", "import pytest, wx; assert pytest.__version__ == '$PytestVersion'; assert wx.__version__ == '4.3.1'; assert 'wxWidgets 3.3.3' in wx.version(); print(f'pytest {pytest.__version__}; {wx.version()}')"
) -Stage "Import wx w środowisku testowym"
Assert-PrivatePython
Assert-WebView2Runtime

# Ustawienie środowiska jest wykonywane dopiero po przygotowaniu wszystkich
# przypiętych narzędzi. Następne polecenia nie korzystają z Hermesa ani Codex.
. $UseEnvironmentScript -DependencyRoot $DependencyRoot

# NuGet: pierwszy restore uzupełnia wspólny cache. Każdy zapisany nupkg trafia
# też do płaskiego lokalnego źródła używanego w próbie bez sieci.
Invoke-Checked -FilePath "dotnet" -ArgumentList @(
    "restore", (Join-Path $RepositoryRoot "AccessibleMediaController.sln"),
    "--runtime", "win-x64", "--packages", $env:NUGET_PACKAGES,
    "-p:NuGetAudit=false", "--disable-build-servers", "--verbosity", "minimal", "/m:1"
) -Stage "Przywracanie NuGet"
$offlineNuget = Join-Path $DependencyRoot "nuget-offline-source"
Get-ChildItem -LiteralPath $env:NUGET_PACKAGES -Recurse -File -Filter "*.nupkg" | ForEach-Object {
    $destination = Join-Path $offlineNuget $_.Name
    if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
        Copy-Item -LiteralPath $_.FullName -Destination $destination
    }
}
$offlineVerifyPackages = Join-Path $DependencyRoot "nuget-offline-verify"
Invoke-Checked -FilePath "dotnet" -ArgumentList @(
    "restore", (Join-Path $RepositoryRoot "AccessibleMediaController.sln"),
    "--runtime", "win-x64", "--packages", $offlineVerifyPackages,
    "--source", $offlineNuget, "--no-cache", "--force",
    "-p:NuGetAudit=false", "--disable-build-servers", "--verbosity", "minimal", "/m:1"
) -Stage "Przywracanie NuGet z lokalnego źródła"
$env:NUGET_PACKAGES = $offlineVerifyPackages
Invoke-Checked -FilePath "dotnet" -ArgumentList @(
    "build", (Join-Path $RepositoryRoot "AccessibleMediaController.sln"),
    "--configuration", "Release", "--no-restore", "--disable-build-servers",
    "--verbosity", "minimal", "/m:1"
) -Stage "Kompilacja .NET bez przywracania"

# Cargo: fetch i build korzystają wyłącznie z Cargo.lock. Drugi build ma
# jawnie wyłączoną sieć. Wynik pozostaje w cache; third_party nie jest ruszane.
$cargo = Join-Path $env:CARGO_HOME "bin\cargo.exe"
$cargoProject = Join-Path $RepositoryRoot "native\AmcSpotifyLibrespotHost"
Push-Location $cargoProject
try {
    & $cargo fetch --locked --offline
    if ($LASTEXITCODE -ne 0) {
        Invoke-Checked -FilePath $cargo -ArgumentList @(
            "fetch", "--locked"
        ) -Stage "cargo fetch --locked"
    }
    Invoke-Checked -FilePath $cargo -ArgumentList @(
        "build", "--release", "--locked", "--target", $RustTarget
    ) -Stage "Kompilacja hosta Librespot"
    $oldCargoOffline = $env:CARGO_NET_OFFLINE
    $env:CARGO_NET_OFFLINE = "true"
    try {
        Invoke-Checked -FilePath $cargo -ArgumentList @(
            "build", "--release", "--locked", "--target", $RustTarget
        ) -Stage "Kompilacja hosta Librespot offline"
        Invoke-Checked -FilePath $cargo -ArgumentList @(
            "test", "--release", "--locked", "--target", $RustTarget
        ) -Stage "Testy protokołu hosta Librespot offline"
    }
    finally {
        $env:CARGO_NET_OFFLINE = $oldCargoOffline
    }
}
finally {
    Pop-Location
}

$librespotBinary = Join-Path $env:CARGO_TARGET_DIR (
    "$RustTarget\release\amc_spotify_librespot_host.exe"
)
if (-not (Test-Path -LiteralPath $librespotBinary -PathType Leaf)) {
    throw "Brak kontrolnie zbudowanego hosta Librespot: $librespotBinary"
}
$peOutput = & dumpbin.exe /dependents /nologo $librespotBinary
if ($LASTEXITCODE -ne 0) { throw "Nie udało się odczytać importów PE hosta Librespot."
}
$peImports = @(
    $peOutput | ForEach-Object {
        if ($_ -match "^\s+([A-Za-z0-9_.-]+\.dll)\s*$") {
            $Matches[1].ToLowerInvariant()
        }
    } | Sort-Object -Unique
)
$dynamicCrtImports = @($peImports | Where-Object {
    $_ -match "^(vcruntime|msvcp|ucrtbase)" -or $_ -match "^api-ms-win-crt-"
})
if ($dynamicCrtImports.Count -gt 0) {
    throw "Kontrolny host wymaga dynamicznego CRT: $($dynamicCrtImports -join ', ')"
}

Push-Location $cargoProject
try {
    $oldCargoOffline = $env:CARGO_NET_OFFLINE
    $env:CARGO_NET_OFFLINE = "true"
    try {
        $metadataJson = (& $cargo metadata --locked --offline --format-version 1 | Out-String)
        if ($LASTEXITCODE -ne 0) { throw "cargo metadata --offline zakończyło się błędem."
        }
    }
    finally {
        $env:CARGO_NET_OFFLINE = $oldCargoOffline
    }
}
finally {
    Pop-Location
}
$cargoMetadata = $metadataJson | ConvertFrom-Json -AsHashtable
$cargoPackages = @($cargoMetadata["packages"])
$packagesWithoutLicense = @($cargoPackages | Where-Object {
    [string]::IsNullOrWhiteSpace([string]$_['license']) -and
    [string]::IsNullOrWhiteSpace([string]$_['license_file'])
})
if ($packagesWithoutLicense.Count -gt 0) {
    $labels = $packagesWithoutLicense | ForEach-Object { "$($_['name']) $($_['version'])" }
    throw "Pakiety Cargo bez deklaracji licencji: $($labels -join ', ')"
}
$licenseIndexPath = Join-Path $RepositoryRoot "licenses\librespot-dependencies\INDEX.txt"
$librespotLicensePath = Join-Path $RepositoryRoot "licenses\librespot-MIT.txt"
if (-not (Test-Path -LiteralPath $licenseIndexPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $librespotLicensePath -PathType Leaf)) {
    throw "Brak repozytoryjnego inwentarza licencji Librespot."
}
$licenseIndex = Get-Content -LiteralPath $licenseIndexPath -Raw
$missingFromLicenseIndex = [Collections.Generic.List[string]]::new()
foreach ($package in $cargoPackages) {
    if ([string]$package['source'] -notmatch "^registry\+") { continue }
    $label = "$($package['name']) $($package['version'])"
    if ($licenseIndex -notmatch "(?m)^$([Regex]::Escape($label))\r?$") {
        [void]$missingFromLicenseIndex.Add($label)
    }
}
if ($missingFromLicenseIndex.Count -gt 0) {
    throw "Inwentarz licencji nie obejmuje: $($missingFromLicenseIndex -join ', ')"
}

$amcCommit = (& git -C $RepositoryRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw "Nie udało się odczytać rewizji AMC."
}
$nativeStatus = @(& git -C $RepositoryRoot status --porcelain -- native/AmcSpotifyLibrespotHost)
if ($LASTEXITCODE -ne 0) { throw "Nie udało się sprawdzić stanu źródeł hosta."
}
$rustcVersion = (& (Join-Path $env:CARGO_HOME "bin\rustc.exe") --version).Trim()
$cargoVersion = (& $cargo --version).Trim()
$msvcVersion = @(Get-ChildItem -LiteralPath (Join-Path $buildToolsRoot "VC\Tools\MSVC") `
    -Directory | Sort-Object Name | Select-Object -Last 1 -ExpandProperty Name)[0]
$vswhere = Get-VsWherePath
$buildToolsVersion = if ($null -eq $vswhere) {
    "nieustalona"
} else {
    [string](& $vswhere -latest -products * -property installationVersion)
}
$provenance = [ordered]@{
    purpose = "local-control-build-not-approved-for-third-party"
    binary = "amc_spotify_librespot_host.exe"
    bytes = (Get-Item -LiteralPath $librespotBinary).Length
    sha256 = (Get-FileHash -LiteralPath $librespotBinary -Algorithm SHA256).Hash.ToLowerInvariant()
    target = $RustTarget
    crtStatic = $true
    directPeImports = $peImports
    librespotRevision = "d36f9f1907e8cc9d68a93f8ebc6b627b1bf7267d"
    amcCommit = $amcCommit
    nativeSourceDirty = ($nativeStatus.Count -gt 0)
    cargoLockSha256 = (Get-FileHash -LiteralPath (Join-Path $cargoProject "Cargo.lock") -Algorithm SHA256).Hash.ToLowerInvariant()
    cargoPackageCount = $cargoPackages.Count
    licensesCoveredByRepositoryInventory = $true
    rustc = $rustcVersion
    cargo = $cargoVersion
    rustflags = $env:RUSTFLAGS
    visualStudioBuildTools = $buildToolsVersion.Trim()
    msvcTools = $msvcVersion
    windowsSdk = $windowsSdk[-1].Name
    builtAtUtc = [DateTimeOffset]::UtcNow.ToString("o")
    verification = [ordered]@{
        cargoBuildLockedOffline = $true
        cargoTestsLockedOffline = $true
        peImportsChecked = $true
        licensesChecked = $true
    }
}
$provenancePath = Join-Path $DependencyRoot "metadata\amc-spotify-librespot-host-local-provenance.json"
$provenance | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $provenancePath -Encoding utf8

# pnpm: normalny fetch uzupełnia magazyn. Instalacja jest już wyłącznie
# offline, zamrożona lockfile'em, po czym uruchamiane są testy i build.
$tidalPlayerRoot = Join-Path $RepositoryRoot "src\AccessibleMediaController.Windows\TidalPlayerHost"
$pnpmStore = Join-Path $DependencyRoot "pnpm-store"
$pnpmCache = Join-Path $DependencyRoot "pnpm-cache"
$pnpmVirtualStore = "node_modules/.pnpm"
$env:CI = "true"
Push-Location $tidalPlayerRoot
try {
    & $pnpm fetch --offline --frozen-lockfile --store-dir $pnpmStore `
        --cache-dir $pnpmCache `
        --virtual-store-dir $pnpmVirtualStore
    if ($LASTEXITCODE -ne 0) {
        Invoke-Checked -FilePath $pnpm -ArgumentList @(
            "fetch", "--frozen-lockfile", "--store-dir", $pnpmStore,
            "--cache-dir", $pnpmCache,
            "--virtual-store-dir", $pnpmVirtualStore
        ) -Stage "pnpm fetch"
    }
    Invoke-Checked -FilePath $pnpm -ArgumentList @(
        "install", "--offline", "--frozen-lockfile", "--store-dir", $pnpmStore,
        "--cache-dir", $pnpmCache,
        "--virtual-store-dir", $pnpmVirtualStore
    ) -Stage "pnpm install offline"
    Invoke-Checked -FilePath $pnpm -ArgumentList @("test") -Stage "Testy modułu TIDAL"
    Invoke-Checked -FilePath $pnpm -ArgumentList @("build") -Stage "Budowanie modułu TIDAL"
}
finally {
    Pop-Location
}

# Pełny zestaw testów interfejsu jest wykonywany tak samo jak podczas promocji
# wydania. Pytest jest przypięty wyżej i instalowany wyłącznie z cache offline.
$env:AMC_WX_LITE_TESTS = "1"
Invoke-Checked -FilePath $pythonTest -ArgumentList @(
    "-m", "pytest", (Join-Path $RepositoryRoot "wxlite\tests"), "-q"
) -Stage "Pełne testy AMC Python"
Invoke-Checked -FilePath "dotnet" -ArgumentList @(
    "run", "--project",
    (Join-Path $RepositoryRoot "tests\AccessibleMediaController.LiteHost.ProtocolTests\AccessibleMediaController.LiteHost.ProtocolTests.csproj"),
    "--configuration", "Release", "--no-build", "--no-restore", "--disable-build-servers"
) -Stage "Testy protokołu LiteHost"

& $UseEnvironmentScript -DependencyRoot $DependencyRoot -CheckOnly
Write-Host "Zależności AMC są przygotowane i sprawdzone, także w trybach offline."
