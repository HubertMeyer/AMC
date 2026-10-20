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
$deploymentSource = Join-Path $repositoryRoot 'deploy\sonos-broker'

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $repositoryRoot '.test-output\sonos-deployment'
}
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)

foreach ($required in @(
    $projectPath,
    $propsPath,
    (Join-Path $deploymentSource 'compose.yaml'),
    (Join-Path $deploymentSource 'Caddyfile'),
    (Join-Path $deploymentSource 'Dockerfile.runtime'),
    (Join-Path $deploymentSource '.env.example'),
    (Join-Path $deploymentSource 'README.md')
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Brakuje pliku wdrożenia: $required"
    }
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
$bundleName = "AMC-Sonos-Deployment-$version-$($commit.Substring(0, 12))$identitySuffix"

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$outputRootResolved = (Resolve-Path -LiteralPath $OutputRoot).Path
$stagePath = Join-Path $outputRootResolved ('.stage-' + [Guid]::NewGuid().ToString('N'))
$bundlePath = Join-Path $outputRootResolved $bundleName
$archivePath = $bundlePath + '.zip'

if ((Test-Path -LiteralPath $bundlePath) -or (Test-Path -LiteralPath $archivePath)) {
    throw "Pakiet o tej tożsamości już istnieje: $bundleName"
}

New-Item -ItemType Directory -Path $stagePath | Out-Null
$applicationPath = Join-Path $stagePath 'app'
New-Item -ItemType Directory -Path $applicationPath | Out-Null

& dotnet publish $projectPath `
    --configuration Release `
    --no-restore `
    --no-self-contained `
    --output $applicationPath `
    -p:UseAppHost=false
if ($LASTEXITCODE -ne 0) {
    throw "Publikowanie brokera Sonos nie powiodło się. Katalog diagnostyczny pozostawiono: $stagePath"
}

if (-not $KeepSymbols) {
    Get-ChildItem -LiteralPath $applicationPath -Filter '*.pdb' -File | Remove-Item -Force
}

Copy-Item -LiteralPath (Join-Path $deploymentSource 'Caddyfile') -Destination $stagePath
Copy-Item -LiteralPath (Join-Path $deploymentSource 'Dockerfile.runtime') `
    -Destination (Join-Path $stagePath 'Dockerfile')
Copy-Item -LiteralPath (Join-Path $deploymentSource '.env.example') -Destination $stagePath
Copy-Item -LiteralPath (Join-Path $deploymentSource 'README.md') -Destination $stagePath

$composeText = Get-Content -Raw -LiteralPath (Join-Path $deploymentSource 'compose.yaml')
$composeText = $composeText.Replace('context: ../..', 'context: .')
$composeText = $composeText.Replace(
    'dockerfile: deploy/sonos-broker/Dockerfile',
    'dockerfile: Dockerfile')
if ($composeText.Contains('context: ../..') -or
    $composeText.Contains('deploy/sonos-broker/Dockerfile')) {
    throw 'Nie dostosowano ścieżek Compose do samodzielnego pakietu.'
}
[System.IO.File]::WriteAllText(
    (Join-Path $stagePath 'compose.yaml'),
    $composeText,
    [System.Text.UTF8Encoding]::new($false))

$secretsPath = Join-Path $stagePath 'secrets'
New-Item -ItemType Directory -Path $secretsPath | Out-Null
[System.IO.File]::WriteAllText(
    (Join-Path $secretsPath 'TU-UMIESC-SEKRET.txt'),
    "Nie wpisuj sekretu do tego pliku. Utwórz obok plik sonos_client_secret.txt tylko na serwerze.`n",
    [System.Text.UTF8Encoding]::new($false))

$publishedFiles = @(Get-ChildItem -LiteralPath $stagePath -File -Recurse | Sort-Object FullName)
if (-not ($publishedFiles.Name -contains 'AccessibleMediaController.SonosBroker.dll')) {
    throw "W pakiecie nie ma głównego pliku brokera. Katalog diagnostyczny pozostawiono: $stagePath"
}
if ($publishedFiles.Name -contains 'sonos_client_secret.txt') {
    throw 'Pakiet wdrożeniowy nie może zawierać sekretu Sonosa.'
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
    product = 'AMC Sonos Broker Deployment'
    version = $version
    sourceCommit = $commit
    workingTreeClean = $workingTreeClean
    targetFramework = 'net8.0'
    selfContained = $false
    includesSecrets = $false
    createdUtc = [DateTime]::UtcNow.ToString('O')
    files = @($manifestFiles)
}
[System.IO.File]::WriteAllText(
    (Join-Path $stagePath 'deployment-manifest.json'),
    ($manifest | ConvertTo-Json -Depth 8),
    [System.Text.UTF8Encoding]::new($false))

Move-Item -LiteralPath $stagePath -Destination $bundlePath
Compress-Archive -Path (Join-Path $bundlePath '*') -DestinationPath $archivePath -CompressionLevel Optimal

[pscustomobject]@{
    BundlePath = $bundlePath
    ArchivePath = $archivePath
    ArchiveSize = (Get-Item -LiteralPath $archivePath).Length
    ArchiveSha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    SourceCommit = $commit
    WorkingTreeClean = $workingTreeClean
}
