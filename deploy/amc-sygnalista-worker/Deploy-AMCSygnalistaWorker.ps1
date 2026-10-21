[CmdletBinding()]
param(
    [string]$WorkerBaseUrl = "",

    [string]$DependencyRoot = "D:\Projekty Codex\AMC - zależności",
    [switch]$Deploy,
    [switch]$ActivateEndpoint
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$workerRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $workerRoot "..\.."))
$configurationPath = Join-Path $workerRoot "wrangler.jsonc"
$configurationTemplatePath = Join-Path $workerRoot "wrangler.jsonc.example"
$lockPath = Join-Path $workerRoot "package-lock.json"
$npmPath = Join-Path $DependencyRoot "node\node-v22.23.2-win-x64\npm.cmd"
$endpointPath = Join-Path $repositoryRoot "wxlite\amc_wx_lite\problem-report-endpoint.txt"

if (-not (Test-Path -LiteralPath $npmPath -PathType Leaf)) {
    throw "Brak przypiętego npm: $npmPath"
}
if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
    throw "Brak package-lock.json. Wdrożenie bez przypiętych zależności jest zabronione."
}
if (-not (Test-Path -LiteralPath $configurationTemplatePath -PathType Leaf)) {
    throw "Brak wzorcowej konfiguracji wrangler.jsonc.example."
}
if ($ActivateEndpoint -and -not $Deploy) {
    throw "Włączenie endpointu wymaga jawnego przełącznika -Deploy."
}

function Get-ValidatedWorkerBaseUrl([string]$Value) {
    $workerUri = $null
    if (-not [Uri]::TryCreate($Value, [UriKind]::Absolute, [ref]$workerUri) -or
        $workerUri.Scheme -ne "https" -or
        -not [string]::IsNullOrWhiteSpace($workerUri.UserInfo) -or
        -not [string]::IsNullOrWhiteSpace($workerUri.Query) -or
        -not [string]::IsNullOrWhiteSpace($workerUri.Fragment) -or
        ($workerUri.AbsolutePath -ne "/" -and $workerUri.AbsolutePath -ne "")) {
        throw "Podaj bazowy adres HTTPS Workera bez ścieżki, danych logowania i parametrów."
    }
    return $Value.TrimEnd("/")
}

$baseUrl = ""
if ($Deploy -and -not [string]::IsNullOrWhiteSpace($WorkerBaseUrl)) {
    $baseUrl = Get-ValidatedWorkerBaseUrl $WorkerBaseUrl
}

Push-Location $workerRoot
try {
    & $npmPath ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm ci nie powiodło się." }
    & $npmPath test
    if ($LASTEXITCODE -ne 0) { throw "Testy Workera nie przeszły." }

    if (-not $Deploy) {
        $dryRunRoot = Join-Path ([IO.Path]::GetTempPath()) ("amc-sygnalista-dry-run-" + [Guid]::NewGuid().ToString("N"))
        $dryRunConfigurationPath = Join-Path $workerRoot (".wrangler-local-" + [Guid]::NewGuid().ToString("N") + ".jsonc")
        try {
            New-Item -ItemType Directory -Path $dryRunRoot -Force | Out-Null
            Copy-Item -LiteralPath $configurationTemplatePath -Destination $dryRunConfigurationPath
            & $npmPath exec -- wrangler deploy --dry-run --config $dryRunConfigurationPath --outdir $dryRunRoot
            if ($LASTEXITCODE -ne 0) { throw "Lokalne pakowanie Workera nie powiodło się." }
        } finally {
            if (Test-Path -LiteralPath $dryRunConfigurationPath -PathType Leaf) {
                Remove-Item -LiteralPath $dryRunConfigurationPath -Force
            }
            if (Test-Path -LiteralPath $dryRunRoot -PathType Container) {
                Remove-Item -LiteralPath $dryRunRoot -Recurse -Force
            }
        }
        Write-Output "Lokalna bramka Workera zaliczona: testy i pakowanie. Niczego nie wdrożono."
        return
    }

    if (-not (Test-Path -LiteralPath $configurationPath -PathType Leaf)) {
        Copy-Item -LiteralPath $configurationTemplatePath -Destination $configurationPath
        Write-Output "Utworzono lokalny, ignorowany przez Git plik wrangler.jsonc."
    }

    # Skrypt nigdy nie uruchamia logowania. Brak istniejącej sesji ma zatrzymać
    # wdrożenie i pozostawić użytkownikowi świadomą autoryzację urządzenia.
    & $npmPath exec -- wrangler whoami
    if ($LASTEXITCODE -ne 0) {
        throw "Wrangler nie ma gotowej sesji Cloudflare. Skrypt nie loguje automatycznie."
    }
    $secretJson = & $npmPath exec -- wrangler secret list --json
    if ($LASTEXITCODE -ne 0) {
        throw "Nie udało się odczytać listy sekretów Workera. Na pierwszym wdrożeniu ustaw GITHUB_TOKEN poleceniem wrangler secret put GITHUB_TOKEN, a następnie uruchom ten skrypt ponownie."
    }
    $secrets = @($secretJson | ConvertFrom-Json)
    if (-not ($secrets | Where-Object { [string]$_.name -eq "GITHUB_TOKEN" })) {
        throw "Worker nie ma wymaganego sekretu GITHUB_TOKEN. Ustaw ograniczony token poleceniem wrangler secret put GITHUB_TOKEN; nie zapisuj jego wartości w pliku."
    }
    $deployOutput = @(& $npmPath exec -- wrangler deploy 2>&1)
    $deployExitCode = $LASTEXITCODE
    foreach ($line in $deployOutput) { Write-Output ([string]$line) }
    if ($deployExitCode -ne 0) { throw "Cloudflare nie potwierdził wdrożenia Workera." }
    if ([string]::IsNullOrWhiteSpace($baseUrl)) {
        $deployText = ($deployOutput | ForEach-Object { [string]$_ }) -join "`n"
        $workerAddress = [Regex]::Match(
            $deployText,
            'https://[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.workers\.dev',
            [Text.RegularExpressions.RegexOptions]::IgnoreCase
        )
        if (-not $workerAddress.Success) {
            throw "Worker został wdrożony, ale nie udało się odczytać jego adresu. Uruchom skrypt ponownie z -WorkerBaseUrl."
        }
        $baseUrl = Get-ValidatedWorkerBaseUrl $workerAddress.Value
        Write-Output "Odczytano bazowy adres Workera: $baseUrl"
    }
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
