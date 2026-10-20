[CmdletBinding()]
param(
    [Parameter(Mandatory)] [ValidateSet("public", "test")] [string]$Profile,
    [Parameter(Mandatory)] [string]$PythonRuntime,
    [Parameter(Mandatory)] [string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$runtime = [IO.Path]::GetFullPath($PythonRuntime)
$output = [IO.Path]::GetFullPath($OutputDirectory)
$temporaryParent = [IO.Path]::GetFullPath((Join-Path $repositoryRoot ".test-tmp"))
$operationRoot = Join-Path $temporaryParent ("bundle-build-" + [guid]::NewGuid().ToString("N"))
$components = Join-Path $operationRoot "components"
$candidate = Join-Path $operationRoot "candidate"
$python = Join-Path $runtime "python.exe"
$bundleTool = Join-Path $repositoryRoot "wxlite\tools\build_bundle.py"
$startupSmokeTool = Join-Path $repositoryRoot "wxlite\tools\Test-AMCBundleStartup.ps1"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Wskazany prywatny runtime nie zawiera python.exe: $runtime"
}
if (Test-Path -LiteralPath $output) {
    throw "Folder docelowy już istnieje; zachowano go bez zmian: $output"
}
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

function Invoke-FullBundleCheck {
    param([Parameter(Mandatory)] [string]$LauncherPath)

    $check = Start-Process -FilePath $LauncherPath `
        -ArgumentList @("--sprawdz-pakiet-pelny-cicho") `
        -WorkingDirectory (Split-Path -Parent $LauncherPath) `
        -Wait -PassThru -WindowStyle Hidden
    try {
        if ($check.ExitCode -ne 0) {
            throw "Pełna kontrola kandydata zakończyła się kodem $($check.ExitCode)."
        }
    }
    finally {
        $check.Dispose()
    }
}

New-Item -ItemType Directory -Path $components -Force | Out-Null
try {
    $hostOutput = Join-Path $components "host"
    $launcher = Join-Path $components "launcher"
    $updater = Join-Path $components "updater"
    $hostArtifacts = Join-Path $operationRoot "artifacts-host"
    $launcherArtifacts = Join-Path $operationRoot "artifacts-launcher"
    $updaterArtifacts = Join-Path $operationRoot "artifacts-updater"

    Invoke-Checked -FilePath "dotnet" -Stage "Publikowanie samowystarczalnego hosta" -ArgumentList @(
        "publish", (Join-Path $repositoryRoot "src\AccessibleMediaController.LiteHost\AccessibleMediaController.LiteHost.csproj"),
        "-c", "Release", "-r", "win-x64", "--self-contained", "true",
        "--artifacts-path", $hostArtifacts,
        "-p:NuGetAudit=false", "-o", $hostOutput
    )
    Invoke-Checked -FilePath "dotnet" -Stage "Publikowanie samowystarczalnego uruchamiacza" -ArgumentList @(
        "publish", (Join-Path $repositoryRoot "src\AccessibleMediaController.PythonLauncher\AccessibleMediaController.PythonLauncher.csproj"),
        "-c", "Release", "-r", "win-x64", "--self-contained", "true",
        "--artifacts-path", $launcherArtifacts,
        "-p:PublishSingleFile=true", "-p:IncludeNativeLibrariesForSelfExtract=true",
        "-p:NuGetAudit=false", "-o", $launcher
    )
    Invoke-Checked -FilePath "dotnet" -Stage "Publikowanie samowystarczalnego aktualizatora" -ArgumentList @(
        "publish", (Join-Path $repositoryRoot "src\AccessibleMediaController.PythonUpdater\AccessibleMediaController.PythonUpdater.csproj"),
        "-c", "Release", "-r", "win-x64", "--self-contained", "true",
        "--artifacts-path", $updaterArtifacts,
        "-p:PublishSingleFile=true", "-p:IncludeNativeLibrariesForSelfExtract=true",
        "-p:NuGetAudit=false", "-o", $updater
    )

    Invoke-Checked -FilePath $python -Stage "Składanie zweryfikowanej paczki" -ArgumentList @(
        $bundleTool,
        "--out", $candidate,
        "--profile", $Profile,
        "--host", $hostOutput,
        "--launcher", $launcher,
        "--updater", $updater,
        "--runtime", $runtime,
        "--clean"
    )

    Invoke-FullBundleCheck -LauncherPath (Join-Path $candidate "AMC.exe")
    & $startupSmokeTool -BundleRoot $candidate

    New-Item -ItemType Directory -Path (Split-Path -Parent $output) -Force | Out-Null
    Move-Item -LiteralPath $candidate -Destination $output
    Write-Output "Samowystarczalna paczka gotowa: $output"
}
finally {
    if (Test-Path -LiteralPath $operationRoot) {
        Remove-Item -LiteralPath $operationRoot -Recurse -Force
    }
}
