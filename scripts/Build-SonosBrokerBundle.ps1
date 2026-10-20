[CmdletBinding()]
param(
    [string]$OutputRoot,
    [switch]$KeepSymbols
)

$ErrorActionPreference = 'Stop'

$scriptDirectory = Split-Path -Parent $PSCommandPath
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDirectory '..'))
$projectPath = Join-Path $repositoryRoot 'src\AccessibleMediaController.SonosBroker\AccessibleMediaController.SonosBroker.csproj'
$propsPath = Join-Path $repositoryRoot 'Directory.Build.props'

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $repositoryRoot '.test-output\sonos-broker'
}
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)

if (-not (Test-Path -LiteralPath $projectPath -PathType Leaf)) {
    throw "Nie znaleziono projektu brokera Sonos: $projectPath"
}
if (-not (Test-Path -LiteralPath $propsPath -PathType Leaf)) {
    throw "Nie znaleziono pliku wersji: $propsPath"
}

[xml]$props = Get-Content -Raw -LiteralPath $propsPath
$version = [string]$props.Project.PropertyGroup.Version
if ([string]::IsNullOrWhiteSpace($version)) {
    throw 'Nie odczytano wersji brokera z Directory.Build.props.'
}

$commit = (& git -C $repositoryRoot rev-parse --verify HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') {
    throw 'Nie odczytano pełnego commitu źródeł.'
}
$trackedChanges = @(& git -C $repositoryRoot status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0) {
    throw 'Nie sprawdzono stanu śledzonych plików repozytorium.'
}
$workingTreeClean = $trackedChanges.Count -eq 0
$identitySuffix = if ($workingTreeClean) { '' } else { '-dirty' }
$bundleName = "AMC-Sonos-Broker-$version-$($commit.Substring(0, 12))$identitySuffix"

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$outputRootResolved = (Resolve-Path -LiteralPath $OutputRoot).Path
$stagePath = Join-Path $outputRootResolved ('.stage-' + [Guid]::NewGuid().ToString('N'))
$bundlePath = Join-Path $outputRootResolved $bundleName
$archivePath = $bundlePath + '.zip'

if ((Test-Path -LiteralPath $bundlePath) -or (Test-Path -LiteralPath $archivePath)) {
    throw "Pakiet o tej tożsamości już istnieje: $bundleName"
}

New-Item -ItemType Directory -Path $stagePath | Out-Null
& dotnet publish $projectPath `
    --configuration Release `
    --no-restore `
    --no-self-contained `
    --output $stagePath `
    -p:UseAppHost=false
if ($LASTEXITCODE -ne 0) {
    throw "Publikowanie brokera Sonos nie powiodło się. Katalog diagnostyczny pozostawiono: $stagePath"
}

if (-not $KeepSymbols) {
    Get-ChildItem -LiteralPath $stagePath -Filter '*.pdb' -File | Remove-Item -Force
}

$publishedFiles = @(Get-ChildItem -LiteralPath $stagePath -File -Recurse | Sort-Object FullName)
if ($publishedFiles.Count -eq 0) {
    throw "Publikowanie nie utworzyło plików. Katalog diagnostyczny pozostawiono: $stagePath"
}
if (-not ($publishedFiles.Name -contains 'AccessibleMediaController.SonosBroker.dll')) {
    throw "W pakiecie nie ma głównego pliku brokera. Katalog diagnostyczny pozostawiono: $stagePath"
}

$manifestFiles = foreach ($file in $publishedFiles) {
    $relativePath = [System.IO.Path]::GetRelativePath($stagePath, $file.FullName).Replace('\', '/')
    [ordered]@{
        path = $relativePath
        size = $file.Length
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$manifest = [ordered]@{
    product = 'AMC Sonos Broker'
    version = $version
    sourceCommit = $commit
    workingTreeClean = $workingTreeClean
    targetFramework = 'net8.0'
    selfContained = $false
    createdUtc = [DateTime]::UtcNow.ToString('O')
    files = @($manifestFiles)
}
$manifestPath = Join-Path $stagePath 'bundle-manifest.json'
$manifestText = $manifest | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($manifestPath, $manifestText, [System.Text.UTF8Encoding]::new($false))

Move-Item -LiteralPath $stagePath -Destination $bundlePath
Compress-Archive -Path (Join-Path $bundlePath '*') -DestinationPath $archivePath -CompressionLevel Optimal
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
$archiveSize = (Get-Item -LiteralPath $archivePath).Length

[pscustomobject]@{
    BundlePath = $bundlePath
    ArchivePath = $archivePath
    ArchiveSize = $archiveSize
    ArchiveSha256 = $archiveHash
    SourceCommit = $commit
    WorkingTreeClean = $workingTreeClean
}
