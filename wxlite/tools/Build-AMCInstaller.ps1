[CmdletBinding()]
param(
    [Parameter(Mandatory)] [ValidateSet("public", "test")] [string]$Profile,
    [Parameter(Mandatory)] [string]$BundleRoot,
    [Parameter(Mandatory)] [ValidatePattern('^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$')] [string]$Version,
    [Parameter(Mandatory)] [string]$OutputDirectory,
    [string]$IsccPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$bundle = [IO.Path]::GetFullPath($BundleRoot)
$output = [IO.Path]::GetFullPath($OutputDirectory)
$installerScript = Join-Path $repositoryRoot "installer\AMC_Wx_Setup.iss"
$manifestPath = Join-Path $bundle "bundle-manifest.json"
$launcher = Join-Path $bundle "AMC.exe"

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Brak bundle-manifest.json w folderze paczki: $bundle"
}
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "Brak AMC.exe w folderze paczki: $bundle"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ([string]$manifest.releaseProfile -ne $Profile) {
    throw "Profil manifestu nie zgadza się z wybranym profilem instalatora."
}
if ([bool]$manifest.sourceDirty) {
    throw "Instalator nie może powstać z niezapisanych źródeł roboczych."
}

$check = Start-Process -FilePath $launcher `
    -ArgumentList @("--sprawdz-pakiet-pelny-cicho") `
    -WorkingDirectory $bundle `
    -Wait -PassThru -WindowStyle Hidden
try {
    if ($check.ExitCode -ne 0) {
        throw "Pełna kontrola paczki przed instalatorem zakończyła się kodem $($check.ExitCode)."
    }
}
finally {
    $check.Dispose()
}

if ([string]::IsNullOrWhiteSpace($IsccPath)) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        $IsccPath = $command.Source
    }
    else {
        $candidate = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $IsccPath = $candidate
        }
    }
}
if ([string]::IsNullOrWhiteSpace($IsccPath) -or
    -not (Test-Path -LiteralPath $IsccPath -PathType Leaf)) {
    throw "Nie znaleziono kompilatora Inno Setup ISCC.exe."
}

New-Item -ItemType Directory -Path $output -Force | Out-Null
$compile = Start-Process -FilePath $IsccPath `
    -ArgumentList @(
        "/DProfil=$Profile",
        "/DWersja=$Version",
        ('/DZrodlo="{0}"' -f $bundle),
        ('/DWyjscie="{0}"' -f $output),
        ('"{0}"' -f $installerScript)
    ) `
    -WorkingDirectory $repositoryRoot `
    -Wait -PassThru -WindowStyle Hidden
try {
    if ($compile.ExitCode -ne 0) {
        throw "Kompilacja instalatora zakończyła się kodem $($compile.ExitCode)."
    }
}
finally {
    $compile.Dispose()
}

$baseName = if ($Profile -eq "public") {
    "AMC-$Version-win-x64.exe"
} else {
    "AMC-Test-$Version-win-x64.exe"
}
$installer = Join-Path $output $baseName
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "Kompilator nie utworzył oczekiwanego instalatora: $installer"
}

$integrity = [ordered]@{
    schemaVersion = 1
    profile = $Profile
    version = $Version
    fileName = $baseName
    bytes = (Get-Item -LiteralPath $installer).Length
    sha256 = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
    bundleId = [string]$manifest.bundleId
    sourceRevision = [string]$manifest.sourceRevision
}
$integrityPath = Join-Path $output ($baseName + ".integrity.json")
$integrity | ConvertTo-Json | Set-Content -LiteralPath $integrityPath -Encoding utf8

Write-Output "Instalator gotowy: $installer"
Write-Output "Integralność: $integrityPath"
