[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet("public", "test")]
    [string]$Profile,

    [Parameter(Mandatory)]
    [ValidatePattern('^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$')]
    [string]$Version,

    [Parameter(Mandatory)]
    [string]$ArtifactsDirectory,

    [string]$NotesPath = "",
    [string]$SummaryPath = "",
    [string]$Repository = "michalkasperczak/AMC",
    [switch]$Publish
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$artifacts = [IO.Path]::GetFullPath($ArtifactsDirectory)
$displayName = if ($Profile -eq "test") { "AMC Test" } else { "AMC Public" }
$productId = if ($Profile -eq "test") {
    "org.accessible-media-controller.test"
} else {
    "org.accessible-media-controller.public"
}
$installId = if ($Profile -eq "test") { "AMC.Test.win-x64" } else { "AMC.Public.win-x64" }
$expectedInstallerPrefix = if ($Profile -eq "test") { "AMC-Test-" } else { "AMC-Public-" }
$preparedNotesPath = Join-Path $artifacts ("release-notes-$Profile-$Version.md")
$preparedManifestPath = Join-Path $artifacts ("release-ready-$Profile-$Version.json")
$updateManifestPath = Join-Path $artifacts ("amc-update-$Profile.json")

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
            [string]$candidate.profile -eq $Profile -and
            [string]$candidate.version -eq $Version) {
            [pscustomobject]@{ Path = $candidatePath.FullName; Data = $candidate }
        }
    }
)
if ($matchingIntegrity.Count -ne 1) {
    throw "Oczekiwano dokładnie jednego pliku integralności $displayName dla wersji $Version."
}
$integrityPath = [string]$matchingIntegrity[0].Path
$integrity = $matchingIntegrity[0].Data
$secretScanProperty = $integrity.PSObject.Properties["secretScan"]
if ($null -eq $secretScanProperty -or [string]$secretScanProperty.Value -ne "passed") {
    throw "Artefakt nie ma potwierdzonej kontroli sekretów i poświadczeń."
}

$baseName = [string]$integrity.fileName
if ([string]::IsNullOrWhiteSpace($baseName) -or
    [IO.Path]::GetFileName($baseName) -cne $baseName -or
    -not $baseName.EndsWith(".exe", [StringComparison]::OrdinalIgnoreCase) -or
    -not $baseName.StartsWith($expectedInstallerPrefix, [StringComparison]::Ordinal)) {
    throw "Plik integralności zawiera nieprawidłową nazwę instalatora dla profilu $Profile."
}
$installerPath = Join-Path $artifacts $baseName
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Brak oczekiwanego instalatora: $baseName"
}

$displayVersion = [string]$integrity.displayVersion
$displayVersionMatch = [Regex]::Match(
    $displayVersion,
    '^(?<day>\d{2})\.(?<month>\d{2})\.(?<year>\d{4}), (?<hour>\d{2}):(?<minute>\d{2})$'
)
if (-not $displayVersionMatch.Success) {
    throw "Plik integralności nie zawiera czytelnej daty i godziny $displayName."
}
$tagTimestamp = (
    $displayVersionMatch.Groups["year"].Value + "." +
    $displayVersionMatch.Groups["month"].Value + "." +
    $displayVersionMatch.Groups["day"].Value + "." +
    $displayVersionMatch.Groups["hour"].Value +
    $displayVersionMatch.Groups["minute"].Value
)
$tag = "$Profile-$tagTimestamp"
$isPrerelease = $Profile -eq "test"

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

$releaseNotesText = ""
$notes = New-Object System.Collections.Generic.List[string]
if (-not [string]::IsNullOrWhiteSpace($NotesPath)) {
    $resolvedNotes = [IO.Path]::GetFullPath($NotesPath)
    if (-not (Test-Path -LiteralPath $resolvedNotes -PathType Leaf)) {
        throw "Nie istnieje plik opisu wydania: $resolvedNotes"
    }
    $releaseNotesText = (Get-Content -LiteralPath $resolvedNotes -Raw).Trim()
    $notes.Add($releaseNotesText)
    $notes.Add("")
}
$summary = ""
if (-not [string]::IsNullOrWhiteSpace($SummaryPath)) {
    $resolvedSummary = [IO.Path]::GetFullPath($SummaryPath)
    if (-not (Test-Path -LiteralPath $resolvedSummary -PathType Leaf)) {
        throw "Nie istnieje plik krótkiego podsumowania: $resolvedSummary"
    }
    $summary = (Get-Content -LiteralPath $resolvedSummary -Raw).Trim()
}
elseif (-not [string]::IsNullOrWhiteSpace($releaseNotesText)) {
    $summary = $releaseNotesText
}
else {
    $summary = "Poprawki działania, dostępności i zgodności AMC."
}
if ([string]::IsNullOrWhiteSpace($summary) -or $summary.Length -gt 6000) {
    throw "Krótkie podsumowanie aktualizacji musi mieć od 1 do 6000 znaków."
}
$notes.Add("## Sumy kontrolne SHA-256")
$notes.Add("")
$notes.Add($baseName)
$notes.Add($actualHash)
$notes.Add("")
$notes.Add("Źródła: $sourceRevision")
[IO.File]::WriteAllLines($preparedNotesPath, $notes, [Text.UTF8Encoding]::new($false))

$updateChannel = if ($Profile -eq "test") { "test" } else { "stable" }
$updateManifest = [ordered]@{
    schemaVersion = 1
    repository = $Repository
    tag = $tag
    version = $Version
    displayName = $displayName
    displayVersion = $displayVersion
    profile = $Profile
    productId = $productId
    installId = $installId
    updateChannel = $updateChannel
    prerelease = $isPrerelease
    sourceRevision = $sourceRevision
    summary = $summary
    installer = [ordered]@{
        fileName = $baseName
        bytes = $installer.Length
        sha256 = $actualHash
    }
}
$updateManifest | ConvertTo-Json -Depth 4 | Set-Content `
    -LiteralPath $updateManifestPath -Encoding utf8

$prepared = [ordered]@{
    schemaVersion = 1
    repository = $Repository
    tag = $tag
    version = $Version
    displayName = $displayName
    displayVersion = $displayVersion
    profile = $Profile
    updateChannel = $updateChannel
    prerelease = $isPrerelease
    installer = $baseName
    bytes = $installer.Length
    sha256 = $actualHash
    updateManifestFile = [IO.Path]::GetFileName($updateManifestPath)
    sourceRevision = $sourceRevision
    integrityFile = [IO.Path]::GetFileName($integrityPath)
    notesFile = [IO.Path]::GetFileName($preparedNotesPath)
    published = $false
}
$prepared | ConvertTo-Json | Set-Content -LiteralPath $preparedManifestPath -Encoding utf8

if (-not $Publish) {
    Write-Output "Weryfikacja $displayName zakończona. Niczego nie opublikowano."
    Write-Output "Opis wydania: $preparedNotesPath"
    Write-Output "Manifest aktualizacji: $updateManifestPath"
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
& gh release view $tag --repo $Repository *> $null
if ($LASTEXITCODE -eq 0) {
    throw "Wydanie $tag już istnieje. Skrypt nie zastępuje opublikowanych plików."
}

$releaseArguments = @(
    "release", "create", $tag,
    "--repo", $Repository,
    "--target", $sourceRevision,
    "--title", "$displayName — $displayVersion",
    "--notes-file", $preparedNotesPath
)
if ($isPrerelease) {
    $releaseArguments += "--prerelease"
}
$releaseArguments += @(
    $installerPath,
    $updateManifestPath,
    $integrityPath
)
& gh @releaseArguments
if ($LASTEXITCODE -ne 0) {
    throw "GitHub nie potwierdził utworzenia wydania."
}

$releaseJson = & gh release view $tag --repo $Repository --json tagName,isPrerelease,body,assets
if ($LASTEXITCODE -ne 0) {
    throw "Nie udało się odczytać opublikowanego wydania."
}
$release = $releaseJson | ConvertFrom-Json
if ([bool]$release.isPrerelease -ne $isPrerelease) {
    throw "GitHub zapisał wydanie w niewłaściwym kanale."
}
$asset = @($release.assets) | Where-Object { [string]$_.name -eq $baseName } | Select-Object -First 1
$integrityAsset = @($release.assets) | Where-Object {
    [string]$_.name -eq [IO.Path]::GetFileName($integrityPath)
} | Select-Object -First 1
$updateManifestAsset = @($release.assets) | Where-Object {
    [string]$_.name -eq [IO.Path]::GetFileName($updateManifestPath)
} | Select-Object -First 1
if ($null -eq $asset -or [long]$asset.size -ne $installer.Length -or [string]$asset.state -ne "uploaded") {
    throw "Opublikowany instalator nie przeszedł kontroli nazwy, rozmiaru i stanu."
}
if ($null -eq $integrityAsset -or [string]$integrityAsset.state -ne "uploaded") {
    throw "GitHub nie potwierdził pliku integralności."
}
if ($null -eq $updateManifestAsset -or
    [string]$updateManifestAsset.state -ne "uploaded") {
    throw "GitHub nie potwierdził manifestu kanału aktualizacji."
}
if (-not [string]$release.body.Contains($baseName) -or
    -not [string]$release.body.Contains($actualHash)) {
    throw "Opis opublikowanego wydania nie zawiera nazwy i sumy SHA-256 instalatora."
}

$prepared.published = $true
$prepared | ConvertTo-Json | Set-Content -LiteralPath $preparedManifestPath -Encoding utf8
Write-Output "Wydanie $tag opublikowane i odczytowo zweryfikowane."
