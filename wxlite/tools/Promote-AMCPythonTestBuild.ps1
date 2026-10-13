[CmdletBinding()]
param(
    [string]$InstallRoot = "D:\Projekty Codex\AMC Python",
    [switch]$SkipTests,
    [switch]$NoLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$WxliteRoot = Join-Path $RepositoryRoot "wxlite"
$BuildTool = Join-Path $WxliteRoot "tools\build_bundle.py"
$RuntimePython = Join-Path $InstallRoot "runtime\python.exe"
$InstalledLauncher = Join-Path $InstallRoot "AMC.exe"
$TestOutputRoot = Join-Path $RepositoryRoot ".test-output"
$TemporaryRoot = Join-Path $RepositoryRoot ".test-tmp"

function Invoke-Checked {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [string[]]$ArgumentList,
        [Parameter(Mandatory)] [string]$WorkingDirectory,
        [Parameter(Mandatory)] [string]$Stage
    )

    Push-Location -LiteralPath $WorkingDirectory
    try {
        & $FilePath @ArgumentList
        if ($LASTEXITCODE -ne 0) {
            throw "$Stage zakończył się kodem $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

function Read-BundleManifest {
    param([Parameter(Mandatory)] [string]$Root)

    $manifestPath = Join-Path $Root "bundle-manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Brak manifestu paczki: $manifestPath"
    }
    return Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
}

if (-not (Test-Path -LiteralPath $RuntimePython -PathType Leaf)) {
    throw "Brak prywatnego runtime'u bieżącej instalacji: $RuntimePython"
}
if (-not (Test-Path -LiteralPath $InstalledLauncher -PathType Leaf)) {
    throw "Brak stałego pliku uruchamiającego: $InstalledLauncher"
}

$trackedChanges = & git -C $RepositoryRoot status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0) {
    throw "Nie udało się sprawdzić stanu repozytorium."
}
if ($trackedChanges) {
    throw (
        "Odbiorcza paczka nie może powstać z niezatwierdzonych zmian. " +
        "Najpierw zatwierdź spójny przyrost w lokalnym Git."
    )
}

$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
if ($null -eq $dotnet) {
    throw "Brak środowiska dotnet potrzebnego do kompilacji składników AMC."
}
$env:DOTNET = $dotnet.Source

if (-not $SkipTests) {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($null -eq $uv) {
        throw "Brak polecenia uv potrzebnego do uruchomienia testów Pythona."
    }
    Invoke-Checked -FilePath $dotnet.Source -ArgumentList @(
        "build",
        (Join-Path $RepositoryRoot "tests\AccessibleMediaController.LiteHost.ProtocolTests\AccessibleMediaController.LiteHost.ProtocolTests.csproj"),
        "-c", "Release"
    ) -WorkingDirectory $RepositoryRoot -Stage "Budowanie serwera testowego protokołu"
    Invoke-Checked -FilePath $uv.Source -ArgumentList @(
        "run", "--with", "pytest", "--with", "wxpython",
        "python", "-m", "pytest", "tests", "-q"
    ) -WorkingDirectory $WxliteRoot -Stage "Testy interfejsu"
}

$projects = @(
    "src\AccessibleMediaController.PythonLauncher\AccessibleMediaController.PythonLauncher.csproj",
    "src\AccessibleMediaController.PythonUpdater\AccessibleMediaController.PythonUpdater.csproj",
    "src\AccessibleMediaController.LiteHost\AccessibleMediaController.LiteHost.csproj"
)
foreach ($project in $projects) {
    Invoke-Checked -FilePath $dotnet.Source -ArgumentList @(
        "publish", (Join-Path $RepositoryRoot $project),
        "-c", "Release", "-r", "win-x64", "--no-self-contained"
    ) -WorkingDirectory $RepositoryRoot -Stage "Budowanie $project"
}

New-Item -ItemType Directory -Path $TemporaryRoot -Force | Out-Null
New-Item -ItemType Directory -Path $TestOutputRoot -Force | Out-Null
$stagingRoot = Join-Path $TemporaryRoot ("AMC-Python-candidate-" + [guid]::NewGuid().ToString("N"))

Invoke-Checked -FilePath $RuntimePython -ArgumentList @(
    $BuildTool,
    "--out", $stagingRoot,
    "--runtime", (Join-Path $InstallRoot "runtime"),
    "--clean"
) -WorkingDirectory $WxliteRoot -Stage "Składanie paczki"

$candidateManifest = Read-BundleManifest -Root $stagingRoot
$expectedBuild = [string]$candidateManifest.buildLabel
if ([string]::IsNullOrWhiteSpace($expectedBuild) -or $expectedBuild.EndsWith("-robocza")) {
    throw "Paczka odbiorcza nie ma czystej, jednoznacznej etykiety kompilacji."
}
$candidateRoot = Join-Path $TestOutputRoot ("AMC-Python-next-" + $expectedBuild)
if (Test-Path -LiteralPath $candidateRoot) {
    throw "Paczka o tej tożsamości już istnieje: $candidateRoot"
}
Move-Item -LiteralPath $stagingRoot -Destination $candidateRoot

$candidateLauncher = Join-Path $candidateRoot "AMC.exe"
Invoke-Checked -FilePath $candidateLauncher -ArgumentList @(
    "--sprawdz-pakiet-cicho"
) -WorkingDirectory $candidateRoot -Stage "Sprawdzenie paczki kandydującej"

$updater = Join-Path $candidateRoot "AMC-Python-Updater.exe"
Invoke-Checked -FilePath $updater -ArgumentList @(
    "--source", $candidateRoot,
    "--target", $InstallRoot,
    "--silent"
) -WorkingDirectory $candidateRoot -Stage "Instalowanie paczki"

$installedManifest = Read-BundleManifest -Root $InstallRoot
$installedBuild = [string]$installedManifest.buildLabel
if ($installedBuild -ne $expectedBuild) {
    throw "Instalacja ma kompilację $installedBuild, oczekiwano $expectedBuild. Program nie zostanie uruchomiony."
}
Invoke-Checked -FilePath $InstalledLauncher -ArgumentList @(
    "--sprawdz-pakiet-cicho"
) -WorkingDirectory $InstallRoot -Stage "Sprawdzenie zainstalowanej paczki"

$runningTitle = ""
if (-not $NoLaunch) {
    Start-Process -FilePath $InstalledLauncher -WorkingDirectory $InstallRoot
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 400
        $process = Get-Process | Where-Object {
            $_.MainWindowTitle -like "AMC Python*kompilacja $expectedBuild"
        } | Select-Object -First 1
        if ($null -ne $process) {
            $runningTitle = $process.MainWindowTitle
            break
        }
    } while ([DateTime]::UtcNow -lt $deadline)
    if ([string]::IsNullOrWhiteSpace($runningTitle)) {
        throw "Nie potwierdzono uruchomienia kompilacji $expectedBuild."
    }
}

$receipt = [ordered]@{
    createdLocal = [DateTimeOffset]::Now.ToString("yyyy-MM-ddTHH:mm:sszzz")
    sourceRevision = [string]$candidateManifest.sourceRevision
    bundleId = [string]$candidateManifest.bundleId
    buildLabel = $expectedBuild
    candidateRoot = $candidateRoot
    installRoot = $InstallRoot
    installedBuildLabel = $installedBuild
    launched = -not $NoLaunch
    runningWindowTitle = $runningTitle
    tests = if ($SkipTests) { "pominięte" } else { "zaliczone" }
}
$receipt | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (
    Join-Path $TestOutputRoot "LAST_TEST_BUILD.json"
) -Encoding UTF8
$summary = if ($NoLaunch) {
    "Zainstalowano kompilację $expectedBuild. Nie uruchomiono programu."
} else {
    "Uruchomiono kompilację $expectedBuild z D:\Projekty Codex\AMC Python\AMC.exe."
}
$summary | Set-Content -LiteralPath (
    Join-Path $TestOutputRoot "LAST_TEST_BUILD.txt"
) -Encoding UTF8
Write-Output $summary
