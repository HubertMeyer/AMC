[CmdletBinding()]
param(
    [string]$WorkerBaseUrl = "",

    [string]$DependencyRoot = "D:\Projekty Codex\AMC - zależności",
    [switch]$Bootstrap,
    [switch]$SetGitHubToken,
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
$actionCount = 0
foreach ($action in @($Bootstrap, $SetGitHubToken, $Deploy)) {
    if ($action) { $actionCount++ }
}
if ($actionCount -gt 1) {
    throw "Wybierz tylko jeden etap zdalny: -Bootstrap, -SetGitHubToken albo -Deploy."
}
$performRemoteAction = $Bootstrap -or $SetGitHubToken -or $Deploy

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
if (($Bootstrap -or $Deploy) -and -not [string]::IsNullOrWhiteSpace($WorkerBaseUrl)) {
    $baseUrl = Get-ValidatedWorkerBaseUrl $WorkerBaseUrl
}

function Get-WorkerSecretInventory {
    $output = @(& $npmPath exec -- wrangler secret list --format json 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | ForEach-Object { [string]$_ }) -join "`n"
    if ($exitCode -ne 0) {
        return [pscustomobject]@{
            Success = $false
            Names = @()
            Output = $text
        }
    }
    try {
        $items = @($text | ConvertFrom-Json)
    } catch {
        throw "Wrangler zwrócił nieprawidłową listę sekretów."
    }
    return [pscustomobject]@{
        Success = $true
        Names = @($items | ForEach-Object { [string]$_.name })
        Output = ""
    }
}

function Invoke-WorkerDeployment([string]$ConfigPath = "") {
    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        $output = @(& $npmPath exec -- wrangler deploy 2>&1)
    } else {
        $output = @(& $npmPath exec -- wrangler deploy --config $ConfigPath 2>&1)
    }
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Lines = $output
        Text = ($output | ForEach-Object { [string]$_ }) -join "`n"
    }
}

function New-WorkerBootstrapConfiguration([string]$DestinationPath) {
    $bootstrapConfiguration = Get-Content -LiteralPath $configurationTemplatePath -Raw | ConvertFrom-Json
    $bootstrapConfiguration.PSObject.Properties.Remove("secrets")
    [IO.File]::WriteAllText(
        $DestinationPath,
        (($bootstrapConfiguration | ConvertTo-Json -Depth 20) + "`n"),
        [Text.UTF8Encoding]::new($false)
    )
}

function Resolve-WorkerBaseUrl([string]$ConfiguredUrl, [string]$DeploymentText) {
    if (-not [string]::IsNullOrWhiteSpace($ConfiguredUrl)) {
        return Get-ValidatedWorkerBaseUrl $ConfiguredUrl
    }
    $workerAddress = [Regex]::Match(
        $DeploymentText,
        'https://[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.workers\.dev',
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $workerAddress.Success) {
        throw "Worker został wdrożony, ale nie udało się odczytać jego adresu. Uruchom skrypt ponownie z -WorkerBaseUrl."
    }
    return Get-ValidatedWorkerBaseUrl $workerAddress.Value
}

function Invoke-WorkerHttpProbe(
    [string]$Uri,
    [string]$Method,
    [AllowNull()][string]$Body = $null
) {
    $handler = [Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(20)
    $request = [Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::new($Method), $Uri)
    if ($null -ne $Body) {
        $request.Content = [Net.Http.StringContent]::new(
            $Body,
            [Text.UTF8Encoding]::new($false),
            "application/json"
        )
    }
    try {
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        try {
            return [pscustomobject]@{
                StatusCode = [int]$response.StatusCode
                Content = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
            }
        } finally {
            $response.Dispose()
        }
    } finally {
        $request.Dispose()
        $client.Dispose()
    }
}

function Assert-WorkerHealth([string]$WorkerBaseUrl) {
    $response = Invoke-WorkerHttpProbe "$WorkerBaseUrl/health" "GET"
    if ($response.StatusCode -ne 200) {
        throw "Endpoint zdrowia zwrócił status $($response.StatusCode)."
    }
    try {
        $health = $response.Content | ConvertFrom-Json
    } catch {
        throw "Endpoint zdrowia nie zwrócił prawidłowego JSON."
    }
    if ([string]$health.status -ne "ok" -or [int]$health.schemaVersion -ne 1) {
        throw "Endpoint zdrowia zwrócił niezgodny kontrakt."
    }
}

function Assert-WorkerBootstrapState([string]$WorkerBaseUrl) {
    $response = Invoke-WorkerHttpProbe "$WorkerBaseUrl/health" "GET"
    if ($response.StatusCode -ne 503) {
        throw "Bootstrap Workera nie pozostał w oczekiwanym, nieaktywnym stanie 503."
    }
    try {
        $status = $response.Content | ConvertFrom-Json
    } catch {
        throw "Nieaktywny bootstrap Workera nie zwrócił prawidłowego JSON."
    }
    if ([string]$status.error -ne "Serwer zgłoszeń nie jest skonfigurowany") {
        throw "Nieaktywny bootstrap Workera zwrócił nieoczekiwany kontrakt."
    }
}

function Assert-WorkerReadiness([string]$WorkerBaseUrl) {
    Assert-WorkerHealth $WorkerBaseUrl

    $methodProbe = Invoke-WorkerHttpProbe "$WorkerBaseUrl/v1/report" "GET"
    if ($methodProbe.StatusCode -ne 405) {
        throw "Endpoint raportów nie odrzucił bezpiecznej próby GET statusem 405."
    }

    # Niepoprawna wersja schematu jest odrzucana przed limiterem i GitHubem,
    # ale dopiero po sprawdzeniu sekretu, koordynatora i limitera.
    $schemaProbe = Invoke-WorkerHttpProbe `
        "$WorkerBaseUrl/v1/report" `
        "POST" `
        '{"schemaVersion":999}'
    if ($schemaProbe.StatusCode -ne 400) {
        throw "Endpoint raportów nie odrzucił nieobsługiwanego schematu statusem 400."
    }
    try {
        $schemaError = $schemaProbe.Content | ConvertFrom-Json
    } catch {
        throw "Próba schematu nie zwróciła prawidłowego JSON."
    }
    if ([string]$schemaError.error -ne "Nieobsługiwana wersja raportu") {
        throw "Próba schematu zwróciła nieoczekiwany kontrakt."
    }
}

Push-Location $workerRoot
try {
    & $npmPath ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm ci nie powiodło się." }
    & $npmPath test
    if ($LASTEXITCODE -ne 0) { throw "Testy Workera nie przeszły." }

    if (-not $performRemoteAction) {
        $dryRunRoot = Join-Path ([IO.Path]::GetTempPath()) ("amc-sygnalista-dry-run-" + [Guid]::NewGuid().ToString("N"))
        $dryRunConfigurationPath = Join-Path $workerRoot (".wrangler-local-" + [Guid]::NewGuid().ToString("N") + ".jsonc")
        $bootstrapDryRunConfigurationPath = Join-Path $workerRoot (".wrangler-bootstrap-" + [Guid]::NewGuid().ToString("N") + ".jsonc")
        try {
            New-Item -ItemType Directory -Path $dryRunRoot -Force | Out-Null
            Copy-Item -LiteralPath $configurationTemplatePath -Destination $dryRunConfigurationPath
            & $npmPath exec -- wrangler deploy --dry-run --config $dryRunConfigurationPath --outdir $dryRunRoot
            if ($LASTEXITCODE -ne 0) { throw "Lokalne pakowanie Workera nie powiodło się." }
            New-WorkerBootstrapConfiguration $bootstrapDryRunConfigurationPath
            & $npmPath exec -- wrangler deploy --dry-run --config $bootstrapDryRunConfigurationPath --outdir $dryRunRoot
            if ($LASTEXITCODE -ne 0) { throw "Lokalne pakowanie bootstrapu Workera nie powiodło się." }
        } finally {
            if (Test-Path -LiteralPath $dryRunConfigurationPath -PathType Leaf) {
                Remove-Item -LiteralPath $dryRunConfigurationPath -Force
            }
            if (Test-Path -LiteralPath $bootstrapDryRunConfigurationPath -PathType Leaf) {
                Remove-Item -LiteralPath $bootstrapDryRunConfigurationPath -Force
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

    $secretInventory = Get-WorkerSecretInventory

    if ($Bootstrap) {
        if ($secretInventory.Success) {
            throw "Worker już istnieje. Bootstrap jest przeznaczony wyłącznie do pierwszego wdrożenia."
        }
        if ($secretInventory.Output -notmatch 'Worker\s+"?amc-sygnalista"?\s+not found|run\s+.+deploy\s+first') {
            throw "Nie udało się bezpiecznie potwierdzić, że Worker jeszcze nie istnieje."
        }
        # Wersjonowana konfiguracja wymaga sekretu podczas zwykłego wdrożenia.
        # Pierwszy bootstrap celowo nie ma jeszcze GITHUB_TOKEN, dlatego używa
        # jednorazowej kopii bez samej deklaracji wymaganych sekretów. Kopia
        # zachowuje nazwę Workera, bindingi, limiter i migrację Durable Object.
        $bootstrapConfigurationPath = Join-Path $workerRoot (".wrangler-bootstrap-" + [Guid]::NewGuid().ToString("N") + ".jsonc")
        try {
            New-WorkerBootstrapConfiguration $bootstrapConfigurationPath
            $deployment = Invoke-WorkerDeployment $bootstrapConfigurationPath
        } finally {
            if (Test-Path -LiteralPath $bootstrapConfigurationPath -PathType Leaf) {
                Remove-Item -LiteralPath $bootstrapConfigurationPath -Force
            }
        }
        foreach ($line in $deployment.Lines) { Write-Output ([string]$line) }
        if ($deployment.ExitCode -ne 0) {
            throw "Cloudflare nie potwierdził bootstrapowego wdrożenia Workera."
        }
        $baseUrl = Resolve-WorkerBaseUrl $baseUrl $deployment.Text
        Assert-WorkerBootstrapState $baseUrl
        Write-Output "Bootstrap Workera zakończony bez aktywacji endpointu AMC."
        Write-Output "Worker nie przyjmuje jeszcze zgłoszeń. Następny jawny krok: -SetGitHubToken."
        return
    }

    if (-not $secretInventory.Success) {
        throw "Worker jeszcze nie istnieje albo nie można go odczytać. Najpierw wykonaj jawny etap -Bootstrap."
    }

    if ($SetGitHubToken) {
        Write-Output "Wrangler poprosi teraz interaktywnie o ograniczony token GitHuba."
        Write-Output "Polecenie secret put tworzy i od razu wdraża nową wersję Workera. Token nie jest zapisywany przez ten skrypt w pliku ani w dzienniku."
        & $npmPath exec -- wrangler secret put GITHUB_TOKEN
        if ($LASTEXITCODE -ne 0) {
            throw "Cloudflare nie potwierdził ustawienia sekretu GITHUB_TOKEN."
        }
        $confirmedSecrets = Get-WorkerSecretInventory
        if (-not $confirmedSecrets.Success -or -not ($confirmedSecrets.Names -contains "GITHUB_TOKEN")) {
            throw "Cloudflare nie potwierdził obecności sekretu GITHUB_TOKEN."
        }
        Write-Output "Sekret GITHUB_TOKEN został potwierdzony. Endpoint AMC nadal pozostaje wyłączony."
        Write-Output "Następny jawny krok: -Deploy, opcjonalnie razem z -ActivateEndpoint po odbiorze gotowości."
        return
    }

    if (-not ($secretInventory.Names -contains "GITHUB_TOKEN")) {
        throw "Worker nie ma wymaganego sekretu GITHUB_TOKEN. Uruchom osobny jawny etap -SetGitHubToken."
    }

    $deployment = Invoke-WorkerDeployment
    foreach ($line in $deployment.Lines) { Write-Output ([string]$line) }
    if ($deployment.ExitCode -ne 0) {
        throw "Cloudflare nie potwierdził wdrożenia Workera."
    }
    $baseUrl = Resolve-WorkerBaseUrl $baseUrl $deployment.Text
} finally {
    Pop-Location
}

Assert-WorkerReadiness $baseUrl

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
