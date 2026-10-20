[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$WorkerBaseUrl,

    [string]$DependencyRoot = "D:\Projekty Codex\AMC - zależności",
    [switch]$Deploy,
    [switch]$ActivateEndpoint
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$workerRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $workerRoot "..\.."))
$configurationPath = Join-Path $workerRoot "wrangler.jsonc"
$lockPath = Join-Path $workerRoot "package-lock.json"
$npmPath = Join-Path $DependencyRoot "node\node-v22.23.2-win-x64\npm.cmd"
$endpointPath = Join-Path $repositoryRoot "wxlite\amc_wx_lite\problem-report-endpoint.txt"

$workerUri = $null
if (-not [Uri]::TryCreate($WorkerBaseUrl, [UriKind]::Absolute, [ref]$workerUri) -or
    $workerUri.Scheme -ne "https" -or
    -not [string]::IsNullOrWhiteSpace($workerUri.UserInfo) -or
    -not [string]::IsNullOrWhiteSpace($workerUri.Query) -or
    -not [string]::IsNullOrWhiteSpace($workerUri.Fragment) -or
    ($workerUri.AbsolutePath -ne "/" -and $workerUri.AbsolutePath -ne "")) {
    throw "Podaj bazowy adres HTTPS Workera bez ścieżki, danych logowania i parametrów."
}
$baseUrl = $WorkerBaseUrl.TrimEnd("/")

if (-not (Test-Path -LiteralPath $npmPath -PathType Leaf)) {
    throw "Brak przypiętego npm: $npmPath"
}
if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
    throw "Brak package-lock.json. Wdrożenie bez przypiętych zależności jest zabronione."
}
if (-not (Test-Path -LiteralPath $configurationPath -PathType Leaf)) {
    throw "Brak lokalnego wrangler.jsonc. Skopiuj wzór i wpisz identyfikator KV."
}
$configurationText = Get-Content -LiteralPath $configurationPath -Raw
if ($configurationText.Contains("UZUPELNIJ_IDENTYFIKATOR_KV")) {
    throw "Konfiguracja nadal zawiera zastępczy identyfikator KV."
}
if ($ActivateEndpoint -and -not $Deploy) {
    throw "Włączenie endpointu wymaga jawnego przełącznika -Deploy."
}

Push-Location $workerRoot
try {
    & $npmPath ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm ci nie powiodło się." }
    & $npmPath test
    if ($LASTEXITCODE -ne 0) { throw "Testy Workera nie przeszły." }

    if (-not $Deploy) {
        Write-Output "Lokalna bramka Workera zaliczona. Niczego nie wdrożono."
        return
    }

    # Skrypt nigdy nie uruchamia logowania. Brak istniejącej sesji ma zatrzymać
    # wdrożenie i pozostawić użytkownikowi świadomą autoryzację urządzenia.
    & $npmPath exec -- wrangler whoami
    if ($LASTEXITCODE -ne 0) {
        throw "Wrangler nie ma gotowej sesji Cloudflare. Skrypt nie loguje automatycznie."
    }
    $secretJson = & $npmPath exec -- wrangler secret list --json
    if ($LASTEXITCODE -ne 0) { throw "Nie udało się odczytać listy sekretów Workera." }
    $secrets = @($secretJson | ConvertFrom-Json)
    if (-not ($secrets | Where-Object { [string]$_.name -eq "GITHUB_TOKEN" })) {
        throw "Worker nie ma wymaganego sekretu GITHUB_TOKEN."
    }
    & $npmPath exec -- wrangler deploy
    if ($LASTEXITCODE -ne 0) { throw "Cloudflare nie potwierdził wdrożenia Workera." }
} finally {
    Pop-Location
}

$healthResponse = Invoke-WebRequest `
    -Uri "$baseUrl/health" `
    -Method Get `
    -TimeoutSec 20 `
    -MaximumRedirection 0
if ($healthResponse.StatusCode -ne 200) {
    throw "Endpoint zdrowia zwrócił status $($healthResponse.StatusCode)."
}
$health = $healthResponse.Content | ConvertFrom-Json
if ([string]$health.status -ne "ok" -or [int]$health.schemaVersion -ne 1) {
    throw "Endpoint zdrowia zwrócił niezgodny kontrakt."
}

if ($ActivateEndpoint) {
    $reportEndpoint = "$baseUrl/v1/report"
    $temporaryPath = $endpointPath + ".tmp-" + [Guid]::NewGuid().ToString("N")
    try {
        [IO.File]::WriteAllText($temporaryPath, $reportEndpoint + "`n", [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($temporaryPath, $endpointPath, $true)
    } finally {
        if (Test-Path -LiteralPath $temporaryPath -PathType Leaf) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
    Write-Output "Zweryfikowany endpoint wpisano do źródeł AMC: $reportEndpoint"
} else {
    Write-Output "Worker działa, ale endpoint AMC pozostaje wyłączony."
}
