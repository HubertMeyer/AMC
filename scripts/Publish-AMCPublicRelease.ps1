[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$')]
    [string]$Version,

    [Parameter(Mandatory)]
    [string]$ArtifactsDirectory,

    [string]$NotesPath = "",
    [string]$Repository = "michalkasperczak/AMC",
    [switch]$Publish
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$artifacts = [IO.Path]::GetFullPath($ArtifactsDirectory)
$preparedNotesPath = Join-Path $artifacts ("release-notes-$Version.md")
$preparedManifestPath = Join-Path $artifacts ("release-ready-$Version.json")

if (-not (Test-Path -LiteralPath $artifacts -PathType Container)) {
    throw "Nie istnieje katalog artefaktów: $artifacts"
}
$matchingIntegrity = @(
    foreach ($candidatePath in Get-ChildItem -LiteralPath $artifacts -File -Filter "*.exe.integrity.json") {
        try {
            $candidate = Get-Content -LiteralPath $candidatePath.FullName -Raw | ConvertFrom-Json
        }
        catch {
            continue
        }
        if ([int]$candidate.schemaVersion -eq 1 -and
            [string]$candidate.profile -eq "public" -and
            [string]$candidate.version -eq $Version) {
            [pscustomobject]@{ Path = $candidatePath.FullName; Data = $candidate }
        }
    }
)
if ($matchingIntegrity.Count -ne 1) {
    throw "Oczekiwano dokładnie jednego pliku integralności AMC Public dla wersji $Version."
}
$integrityPath = [string]$matchingIntegrity[0].Path
$integrity = $matchingIntegrity[0].Data
$baseName = [string]$integrity.fileName
if ([string]::IsNullOrWhiteSpace($baseName) -or
    [IO.Path]::GetFileName($baseName) -cne $baseName -or
    -not $baseName.EndsWith(".exe", [StringComparison]::OrdinalIgnoreCase)) {
    throw "Plik integralności zawiera nieprawidłową nazwę instalatora."
}
$installerPath = Join-Path $artifacts $baseName
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Brak oczekiwanego instalatora: $baseName"
}
if ([string]$integrity.fileName -ne $baseName) {
    throw "Nazwa instalatora nie zgadza się z plikiem integralności."
}
$displayVersion = [string]$integrity.displayVersion
if ($displayVersion -notmatch '^\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}$') {
    throw "Plik integralności nie zawiera czytelnej daty i godziny AMC Public."
}

$installer = Get-Item -LiteralPath $installerPath
$actualHash = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ([long]$integrity.bytes -ne $installer.Length) {
    throw "Rozmiar instalatora nie zgadza się z plikiem integralności."
}
if ([string]$integrity.sha256 -cne $actualHash) {
    throw "SHA-256 instalatora nie zgadza się z plikiem integralności."
}
$sourceRevision = [string]$integrity.sourceRevision
if ($sourceRevision -notmatch '^[0-9a-f]{40}$') {
    throw "Plik integralności nie zawiera pełnej rewizji źródeł."
}

$notes = New-Object System.Collections.Generic.List[string]
if (-not [string]::IsNullOrWhiteSpace($NotesPath)) {
    $resolvedNotes = [IO.Path]::GetFullPath($NotesPath)
    if (-not (Test-Path -LiteralPath $resolvedNotes -PathType Leaf)) {
        throw "Nie istnieje plik opisu wydania: $resolvedNotes"
    }
    $notes.Add((Get-Content -LiteralPath $resolvedNotes -Raw).TrimEnd())
    $notes.Add("")
}
$notes.Add("## Sumy kontrolne SHA-256")
$notes.Add("")
$notes.Add($baseName)
$notes.Add($actualHash)
$notes.Add("")
$notes.Add("Źródła: $sourceRevision")
[IO.File]::WriteAllLines($preparedNotesPath, $notes, [Text.UTF8Encoding]::new($false))

$prepared = [ordered]@{
    schemaVersion = 1
    repository = $Repository
    tag = "v$Version"
    version = $Version
    displayName = "AMC Public"
    displayVersion = $displayVersion
    profile = "public"
    installer = $baseName
    bytes = $installer.Length
    sha256 = $actualHash
    sourceRevision = $sourceRevision
    integrityFile = [IO.Path]::GetFileName($integrityPath)
    notesFile = [IO.Path]::GetFileName($preparedNotesPath)
    published = $false
}
$prepared | ConvertTo-Json | Set-Content -LiteralPath $preparedManifestPath -Encoding utf8

if (-not $Publish) {
    Write-Output "Weryfikacja zakończona. Niczego nie opublikowano."
    Write-Output "Opis wydania: $preparedNotesPath"
    Write-Output "Manifest gotowości: $preparedManifestPath"
    return
}

$trackedChanges = & git -C $repositoryRoot status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0 -or $trackedChanges) {
    throw "Publikacja wymaga czystych śledzonych źródeł."
}
& git -C $repositoryRoot cat-file -e "$sourceRevision`^{commit}"
if ($LASTEXITCODE -ne 0) {
    throw "Rewizja źródłowa instalatora nie istnieje w lokalnym repozytorium."
}

$remoteRevision = & gh api "repos/$Repository/commits/$sourceRevision" --jq .sha
if ($LASTEXITCODE -ne 0 -or [string]$remoteRevision -ne $sourceRevision) {
    throw "Rewizja źródłowa instalatora nie jest jeszcze dostępna w repozytorium GitHub."
}
$tag = "v$Version"
& gh release view $tag --repo $Repository *> $null
if ($LASTEXITCODE -eq 0) {
    throw "Wydanie $tag już istnieje. Skrypt nie zastępuje opublikowanych plików."
}

$releaseArguments = @(
    "release", "create", $tag,
    "--repo", $Repository,
    "--target", $sourceRevision,
    "--title", "AMC Public — $displayVersion",
    "--notes-file", $preparedNotesPath
)
if ($Version.Contains("-")) {
    $releaseArguments += "--prerelease"
}
$releaseArguments += @($installerPath, $integrityPath)
& gh @releaseArguments
if ($LASTEXITCODE -ne 0) {
    throw "GitHub nie potwierdził utworzenia wydania."
}

$releaseJson = & gh release view $tag --repo $Repository --json tagName,isPrerelease,body,assets
if ($LASTEXITCODE -ne 0) {
    throw "Nie udało się odczytać opublikowanego wydania."
}
$release = $releaseJson | ConvertFrom-Json
$asset = @($release.assets) | Where-Object { [string]$_.name -eq $baseName } | Select-Object -First 1
$integrityAsset = @($release.assets) | Where-Object {
    [string]$_.name -eq [IO.Path]::GetFileName($integrityPath)
} | Select-Object -First 1
if ($null -eq $asset -or [long]$asset.size -ne $installer.Length -or [string]$asset.state -ne "uploaded") {
    throw "Opublikowany instalator nie przeszedł kontroli nazwy, rozmiaru i stanu."
}
if ($null -eq $integrityAsset -or [string]$integrityAsset.state -ne "uploaded") {
    throw "GitHub nie potwierdził pliku integralności."
}
if (-not [string]$release.body.Contains($baseName) -or
    -not [string]$release.body.Contains($actualHash)) {
    throw "Opis opublikowanego wydania nie zawiera nazwy i SHA-256 instalatora."
}

$prepared.published = $true
$prepared | ConvertTo-Json | Set-Content -LiteralPath $preparedManifestPath -Encoding utf8
Write-Output "Wydanie $tag opublikowane i odczytowo zweryfikowane."
