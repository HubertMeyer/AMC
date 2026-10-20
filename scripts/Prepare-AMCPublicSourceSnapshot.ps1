[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$')]
    [string]$Version,

    [string]$BranchName = "public/release-line",
    [string]$RepositoryRoot = "",
    [string]$OutputDirectory = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments)][string[]]$Arguments)

    $result = & git -C $script:root @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Polecenie Git nie powiodło się: git $($Arguments -join ' ')"
    }
    return $result
}

$root = if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
} else {
    [IO.Path]::GetFullPath($RepositoryRoot)
}

$topLevel = [string](Invoke-Git rev-parse --show-toplevel)
if ([IO.Path]::GetFullPath($topLevel) -ne $root) {
    throw "Wskazana ścieżka nie jest katalogiem głównym repozytorium."
}

& git check-ref-format --branch $BranchName *> $null
if ($LASTEXITCODE -ne 0 -or -not $BranchName.StartsWith("public/")) {
    throw "Gałąź snapshotu musi mieć poprawną nazwę zaczynającą się od public/."
}

$trackedChanges = & git -C $root status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0 -or $trackedChanges) {
    throw "Snapshot wymaga czystych śledzonych źródeł."
}

$profileNames = @("micha", "michal", $env:USERNAME) |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    ForEach-Object { [Regex]::Escape($_) } |
    Select-Object -Unique
$profileAlternation = $profileNames -join "|"
$forbiddenPatterns = [ordered]@{
    "token GitHub" = 'gh[pousr]_[A-Za-z0-9_]{30,}'
    "token OpenAI albo Google" = 'sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}'
    "JWT" = 'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}(\.[A-Za-z0-9_-]{10,})?'
    "klucz prywatny" = 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY'
    "lokalna ścieżka profilu Windows" = "C:[\\/]+Users[\\/]+($profileAlternation)([^A-Za-z0-9]|$)"
    "lokalna ścieżka profilu Unix" = "/home/($profileAlternation)([^A-Za-z0-9]|$)"
}
foreach ($entry in $forbiddenPatterns.GetEnumerator()) {
    $matches = & git -C $root grep -I -n -i -E -- $entry.Value HEAD 2>$null
    $grepExitCode = $LASTEXITCODE
    if ($grepExitCode -notin @(0, 1)) {
        throw "Nie udało się wykonać audytu prywatności źródeł."
    }
    if ($matches) {
        throw "Snapshot zawiera zabroniony wzorzec: $($entry.Key)."
    }
}

$sourceRevision = [string](Invoke-Git rev-parse HEAD)
$sourceTree = [string](Invoke-Git rev-parse "HEAD^{tree}")
$branchRef = "refs/heads/$BranchName"
$parentRevision = ""
$snapshotRevision = ""
& git -C $root show-ref --verify --quiet $branchRef
if ($LASTEXITCODE -eq 0) {
    $parentRevision = [string](Invoke-Git rev-parse $branchRef)
    $parentTree = [string](Invoke-Git rev-parse "$parentRevision^{tree}")
    if ($parentTree -eq $sourceTree) {
        $snapshotRevision = $parentRevision
    }
}

if ([string]::IsNullOrWhiteSpace($snapshotRevision)) {
    $message = @(
        "AMC $Version - publiczny snapshot zrodel",
        "",
        "Snapshot przygotowany z roboczej rewizji $sourceRevision.",
        "Nie zawiera roboczej historii poprzedzajacej publiczna linie wydan."
    ) -join "`n"
    $parentArguments = @()
    if (-not [string]::IsNullOrWhiteSpace($parentRevision)) {
        $parentArguments = @("-p", $parentRevision)
    }
    $snapshotRevision = [string]($message | & git -C $root commit-tree $sourceTree @parentArguments)
    if ($LASTEXITCODE -ne 0 -or $snapshotRevision -notmatch '^[0-9a-f]{40}$') {
        throw "Nie udało się utworzyć lokalnego commitu snapshotu."
    }
    if ([string]::IsNullOrWhiteSpace($parentRevision)) {
        & git -C $root update-ref $branchRef $snapshotRevision ("0" * 40)
    } else {
        & git -C $root update-ref $branchRef $snapshotRevision $parentRevision
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Nie udało się bezpiecznie zaktualizować lokalnej gałęzi snapshotu."
    }
}

$verifiedTree = [string](Invoke-Git rev-parse "$snapshotRevision^{tree}")
if ($verifiedTree -ne $sourceTree) {
    throw "Drzewo snapshotu nie jest identyczne ze źródłami roboczymi."
}

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $root ".test-output\public-source"
}
$output = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($output) | Out-Null
$manifestPath = Join-Path $output "source-ready-$Version.json"
$manifest = [ordered]@{
    schemaVersion = 1
    version = $Version
    branch = $BranchName
    sourceRevision = $sourceRevision
    snapshotRevision = $snapshotRevision
    tree = $sourceTree
    published = $false
}
$manifest | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding utf8

Write-Output "Lokalny snapshot źródeł jest gotowy. Niczego nie wypchnięto."
Write-Output "Gałąź: $BranchName"
Write-Output "Rewizja snapshotu: $snapshotRevision"
Write-Output "Manifest: $manifestPath"
