[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ClientId,

    [Parameter(Mandatory = $true)]
    [string] $BrokerEndpoint
)

$ErrorActionPreference = "Stop"

$normalizedClientId = $ClientId.Trim()
if ($normalizedClientId -notmatch '^[^\s\x00-\x1f]{20,512}\.apps\.googleusercontent\.com$') {
    throw "Nieprawidłowy identyfikator klienta Google typu Aplikacja komputerowa."
}

[Uri] $broker = $null
$brokerCreated = [Uri]::TryCreate(
    $BrokerEndpoint.Trim(),
    [UriKind]::Absolute,
    [ref] $broker)
if (-not $brokerCreated -or
    $broker.Scheme -ne "https" -or
    [string]::IsNullOrWhiteSpace($broker.Host) -or
    $broker.UserInfo -or
    $broker.Query -or
    $broker.Fragment -or
    $broker.AbsolutePath -cne "/v1/google/token") {
    throw "Adres brokera musi mieć postać https://własna-domena/v1/google/token."
}

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$appPackage = Join-Path $repositoryRoot "wxlite\amc_wx_lite"
$clientIdPath = Join-Path $appPackage "youtube-oauth-public-client-id.txt"
$brokerPath = Join-Path $appPackage "youtube-oauth-public-token-broker.txt"
$wranglerExample = Join-Path $PSScriptRoot "wrangler.jsonc.example"
$wranglerConfig = Join-Path $PSScriptRoot "wrangler.jsonc"
$utf8WithoutBom = [Text.UTF8Encoding]::new($false)

[IO.File]::WriteAllText($clientIdPath, $normalizedClientId + "`n", $utf8WithoutBom)
[IO.File]::WriteAllText($brokerPath, $broker.AbsoluteUri + "`n", $utf8WithoutBom)

if (-not (Test-Path -LiteralPath $wranglerConfig)) {
    $template = [IO.File]::ReadAllText($wranglerExample)
    $template = $template.Replace(
        "UZUPELNIJ.apps.googleusercontent.com",
        $normalizedClientId)
    [IO.File]::WriteAllText($wranglerConfig, $template, $utf8WithoutBom)
}

Write-Output "Zapisano bezpieczny identyfikator klienta: $clientIdPath"
Write-Output "Zapisano adres brokera: $brokerPath"
Write-Output "Przygotowano lokalną konfigurację Workera: $wranglerConfig"
Write-Output "Sekretu Google nie zapisano. Ustaw go osobno poleceniem wrangler secret put."
