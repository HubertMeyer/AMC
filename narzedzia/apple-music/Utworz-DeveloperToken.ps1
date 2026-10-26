#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[A-Za-z0-9]{10}$')]
    [string] $TeamId,

    [Parameter(Mandatory)]
    [ValidatePattern('^[A-Za-z0-9]{10}$')]
    [string] $KeyId,

    [Parameter(Mandatory)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string] $PrivateKeyPath,

    [ValidateRange(1, 180)]
    [int] $DaysValid = 90,

    [string] $OutputFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-Base64Url {
    param([Parameter(Mandatory)][byte[]] $Bytes)
    [Convert]::ToBase64String($Bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

$resolvedKey = (Resolve-Path -LiteralPath $PrivateKeyPath).Path
if ([IO.Path]::GetExtension($resolvedKey) -ne '.p8') {
    throw 'Wybierz prywatny klucz Media Services z rozszerzeniem .p8.'
}

$issuedAt = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$expiresAt = [DateTimeOffset]::UtcNow.AddDays($DaysValid).ToUnixTimeSeconds()
$header = [ordered]@{ alg = 'ES256'; kid = $KeyId; typ = 'JWT' }
$payload = [ordered]@{ iss = $TeamId; iat = $issuedAt; exp = $expiresAt }
$utf8 = [Text.UTF8Encoding]::new($false)
$headerPart = ConvertTo-Base64Url -Bytes $utf8.GetBytes(
    ($header | ConvertTo-Json -Compress))
$payloadPart = ConvertTo-Base64Url -Bytes $utf8.GetBytes(
    ($payload | ConvertTo-Json -Compress))
$unsignedToken = "$headerPart.$payloadPart"

$ecdsa = [Security.Cryptography.ECDsa]::Create()
try {
    $ecdsa.ImportFromPem([IO.File]::ReadAllText($resolvedKey))
    $signature = $ecdsa.SignData(
        $utf8.GetBytes($unsignedToken),
        [Security.Cryptography.HashAlgorithmName]::SHA256,
        [Security.Cryptography.DSASignatureFormat]::IeeeP1363FixedFieldConcatenation)
    $token = "$unsignedToken.$(ConvertTo-Base64Url -Bytes $signature)"

    if ([string]::IsNullOrWhiteSpace($OutputFile)) {
        Set-Clipboard -Value $token
        Write-Host "Gotowy developer token Apple Music skopiowano do schowka. Ważność: $DaysValid dni."
    }
    else {
        $fullOutput = [IO.Path]::GetFullPath($OutputFile)
        $parent = [IO.Path]::GetDirectoryName($fullOutput)
        if ([string]::IsNullOrWhiteSpace($parent) -or -not [IO.Directory]::Exists($parent)) {
            throw 'Folder pliku wyjściowego nie istnieje.'
        }
        [IO.File]::WriteAllText($fullOutput, $token, $utf8)
        Write-Host "Gotowy developer token Apple Music zapisano w: $fullOutput"
    }
}
finally {
    $ecdsa.Dispose()
}

Write-Host 'Prywatny klucz .p8 nie został skopiowany ani zmieniony.'
