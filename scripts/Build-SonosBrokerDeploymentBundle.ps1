[CmdletBinding()]
param(
    [string]$OutputRoot,
    [ValidatePattern('^[a-z0-9]+-[a-z0-9]+$')]
    [string]$RuntimeIdentifier = 'linux-x64',
    [switch]$KeepSymbols
)

$ErrorActionPreference = 'Stop'

$scriptDirectory = Split-Path -Parent $PSCommandPath
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDirectory '..'))
$projectPath = Join-Path $repositoryRoot 'src\AccessibleMediaController.SonosBroker\AccessibleMediaController.SonosBroker.csproj'
$testProjectPath = Join-Path $repositoryRoot 'tests\AccessibleMediaController.SonosBroker.SmokeTests\AccessibleMediaController.SonosBroker.SmokeTests.csproj'
$propsPath = Join-Path $repositoryRoot 'Directory.Build.props'
$deploymentSource = Join-Path $repositoryRoot 'deploy\sonos-broker'

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $repositoryRoot '.test-output\sonos-deployment'
}
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)

foreach ($required in @(
    $projectPath,
    $testProjectPath,
    $propsPath,
    (Join-Path $deploymentSource 'compose.yaml'),
    (Join-Path $deploymentSource 'Caddyfile'),
    (Join-Path $deploymentSource 'Dockerfile.runtime'),
    (Join-Path $deploymentSource '.env.example'),
    (Join-Path $deploymentSource 'README.md'),
    (Join-Path $deploymentSource 'MIGRATION_FROM_LEGACY.md'),
    (Join-Path $deploymentSource 'SYSTEMD_CLOUDFLARE_HANDOFF.md')
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

& dotnet restore $testProjectPath
if ($LASTEXITCODE -ne 0) {
    throw "Odtworzenie zależności testów brokera Sonos nie powiodło się. Katalog diagnostyczny pozostawiono: $stagePath"
}

& dotnet run --project $testProjectPath --configuration Release --no-restore
if ($LASTEXITCODE -ne 0) {
    throw "Testy brokera Sonos nie powiodły się. Katalog diagnostyczny pozostawiono: $stagePath"
}

& dotnet restore $projectPath --runtime $RuntimeIdentifier
if ($LASTEXITCODE -ne 0) {
    throw "Odtworzenie zależności publikacji brokera Sonos nie powiodło się. Katalog diagnostyczny pozostawiono: $stagePath"
}

& dotnet publish $projectPath `
    --configuration Release `
    --runtime $RuntimeIdentifier `
    --no-restore `
    --self-contained false `
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
Copy-Item -LiteralPath (Join-Path $deploymentSource 'MIGRATION_FROM_LEGACY.md') `
    -Destination $stagePath
Copy-Item -LiteralPath (Join-Path $deploymentSource 'SYSTEMD_CLOUDFLARE_HANDOFF.md') `
    -Destination $stagePath

$sourceRoot = Join-Path $stagePath 'source'
$sourceFiles = @(& git -C $repositoryRoot ls-files -- `
    'Directory.Build.props' `
    'src/AccessibleMediaController.SonosBroker' `
    'tests/AccessibleMediaController.SonosBroker.SmokeTests')
if ($LASTEXITCODE -ne 0 -or $sourceFiles.Count -eq 0) {
    throw 'Nie odczytano minimalnego zestawu źródeł brokera i testów.'
}
foreach ($relativePath in $sourceFiles) {
    $sourceFile = Join-Path $repositoryRoot $relativePath
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Brakuje śledzonego pliku źródłowego: $relativePath"
    }

    $destination = Join-Path $sourceRoot $relativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile -Destination $destination
}

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
    runtimeIdentifier = $RuntimeIdentifier
    selfContained = $false
    includesSecrets = $false
    includesSource = $true
    smokeTestCommand = 'dotnet run --project source/tests/AccessibleMediaController.SonosBroker.SmokeTests/AccessibleMediaController.SonosBroker.SmokeTests.csproj --configuration Release'
    expectedSmokeTests = 20
    createdUtc = [DateTime]::UtcNow.ToString('O')
    files = @($manifestFiles)
}
[System.IO.File]::WriteAllText(
    (Join-Path $stagePath 'deployment-manifest.json'),
    ($manifest | ConvertTo-Json -Depth 8),
    [System.Text.UTF8Encoding]::new($false))

Move-Item -LiteralPath $stagePath -Destination $bundlePath
Compress-Archive -Path (Join-Path $bundlePath '*') -DestinationPath $archivePath -CompressionLevel Optimal
$archiveSha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
$checksumPath = $archivePath + '.sha256.txt'
[System.IO.File]::WriteAllText(
    $checksumPath,
    "$archiveSha256  $([System.IO.Path]::GetFileName($archivePath))`n",
    [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{
    BundlePath = $bundlePath
    ArchivePath = $archivePath
    ArchiveSize = (Get-Item -LiteralPath $archivePath).Length
    ArchiveSha256 = $archiveSha256
    ChecksumPath = $checksumPath
    SourceCommit = $commit
    WorkingTreeClean = $workingTreeClean
}
