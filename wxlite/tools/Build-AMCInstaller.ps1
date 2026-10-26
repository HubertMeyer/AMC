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
$startupSmokeTool = Join-Path $repositoryRoot "wxlite\tools\Test-AMCBundleStartup.ps1"
$manifestPath = Join-Path $bundle "bundle-manifest.json"
$launcher = Join-Path $bundle "AMC.exe"

Push-Location $repositoryRoot
try {
    $installerSourceRevision = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($installerSourceRevision)) {
        throw "Nie można odczytać rewizji źródeł instalatora."
    }
    $trackedChanges = @(& git status --porcelain --untracked-files=no)
    if ($LASTEXITCODE -ne 0) {
        throw "Nie można sprawdzić stanu źródeł instalatora."
    }
    if ($trackedChanges.Count -gt 0) {
        throw "Instalator nie może powstać z niezapisanych zmian w śledzonych źródłach."
    }
}
finally {
    Pop-Location
}

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
if ([string]$manifest.sourceRevision -cne $installerSourceRevision) {
    throw "Paczka i instalator muszą pochodzić z tego samego commitu."
}

# Lokalny plik używany podczas rozwoju nie może stać się artefaktem GitHub
# ani instalatora. Sprawdzamy zarówno deklarację manifestu, jak i rzeczywisty
# katalog, aby dodatkowy niezarządzany plik nie ominął kontroli sum pakietu.
$forbiddenBundleFiles = @(
    "app/amc_wx_lite/youtube-oauth-client-secret.txt",
    "app/amc_wx_lite/sonos_client_secret.txt",
    "deploy/sonos-broker/secrets/sonos_client_secret.txt"
)
$manifestFiles = @($manifest.files | ForEach-Object {
    ([string]$_).Replace("\", "/").ToLowerInvariant()
})
foreach ($relative in $forbiddenBundleFiles) {
    $normalized = $relative.ToLowerInvariant()
    $actualPath = Join-Path $bundle ($relative.Replace("/", [IO.Path]::DirectorySeparatorChar))
    if ($manifestFiles -contains $normalized -or (Test-Path -LiteralPath $actualPath)) {
        throw "Instalator nie może zawierać sekretu ani lokalnego pliku poświadczeń: $relative"
    }
}

$displayVersion = [string]$manifest.displayVersion
$displayVersionMatch = [Regex]::Match(
    $displayVersion,
    '^(?<day>\d{2})\.(?<month>\d{2})\.(?<year>\d{4}), (?<hour>\d{2}):(?<minute>\d{2})$'
)
if (-not $displayVersionMatch.Success) {
    throw "Manifest nie zawiera czytelnej daty i godziny wersji użytkowej."
}
$fileTimestamp = (
    $displayVersionMatch.Groups["year"].Value + "-" +
    $displayVersionMatch.Groups["month"].Value + "-" +
    $displayVersionMatch.Groups["day"].Value + "-" +
    $displayVersionMatch.Groups["hour"].Value +
    $displayVersionMatch.Groups["minute"].Value
)

$launcherVersion = [string](Get-Item -LiteralPath $launcher).VersionInfo.ProductVersion
$launcherVersion = ($launcherVersion -split '\+', 2)[0]
if ($launcherVersion -ne $Version) {
    throw (
        "Numer instalatora $Version nie zgadza się z numerem skompilowanego " +
        "programu $launcherVersion. Najpierw ustaw i zbuduj jedną wersję źródeł."
    )
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

& $startupSmokeTool -BundleRoot $bundle

if ([string]::IsNullOrWhiteSpace($IsccPath)) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        $IsccPath = $command.Source
    }
    else {
        $candidates = @(
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
        )
        foreach ($candidate in $candidates) {
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $IsccPath = $candidate
                break
            }
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
        ('/DEtykietaUzytkowa="{0}"' -f $displayVersion),
        "/DEtykietaPliku=$fileTimestamp",
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
    "AMC-Public-$fileTimestamp.exe"
} else {
    "AMC-Test-$fileTimestamp.exe"
}
$installer = Join-Path $output $baseName
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "Kompilator nie utworzył oczekiwanego instalatora: $installer"
}

$integrity = [ordered]@{
    schemaVersion = 1
    profile = $Profile
    version = $Version
    displayVersion = $displayVersion
    fileName = $baseName
    bytes = (Get-Item -LiteralPath $installer).Length
    sha256 = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
    bundleId = [string]$manifest.bundleId
    sourceRevision = [string]$manifest.sourceRevision
    installerSourceRevision = $installerSourceRevision
    secretScan = "passed"
}
$integrityPath = Join-Path $output ($baseName + ".integrity.json")
$integrity | ConvertTo-Json | Set-Content -LiteralPath $integrityPath -Encoding utf8

Write-Output "Instalator gotowy: $installer"
Write-Output "Integralność: $integrityPath"
