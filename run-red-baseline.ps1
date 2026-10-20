# POMIAR RED: te same testy na KODZIE BAZOWYM (bb4c917), zeby pokazac, ze luki
# byly prawdziwe. Zrodla Protocol/ bierzemy z git show HEAD bazowego, a testy z
# katalogu roboczego. Osobny staging, zeby nie tknac wynikow GREEN.
$ErrorActionPreference = 'Stop'
$buildTools = if ($env:AMC_BUILD_TOOLS_ROOT) {
    $env:AMC_BUILD_TOOLS_ROOT
} else {
    Join-Path $env:USERPROFILE 'amc-build-tools'
}
$preferredDotnet = Join-Path $buildTools 'dotnet-8.0.425\dotnet.exe'
$dotnet = if (Test-Path -LiteralPath $preferredDotnet) {
    $preferredDotnet
} else {
    (Get-Command dotnet -ErrorAction Stop).Source
}
$env:NUGET_PACKAGES = if ($env:NUGET_PACKAGES) {
    $env:NUGET_PACKAGES
} else {
    Join-Path $buildTools 'nuget-packages'
}
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'

$stage = Join-Path ([IO.Path]::GetTempPath()) 'amc-wx-queue-transport-final-RED'
$src = Join-Path $stage 'src-tests'
if (Test-Path $src) { Remove-Item $src -Recurse -Force }
New-Item -ItemType Directory -Path $src -Force | Out-Null

$repo = $PSScriptRoot
Copy-Item (Join-Path $repo 'Directory.Build.props') $src -Force
foreach ($part in @(
    'src\AccessibleMediaController.Core',
    'src\AccessibleMediaController.LiteHost\Protocol',
    'tests\AccessibleMediaController.LiteHost.ProtocolTests')) {
    $dest = Join-Path $src $part
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item (Join-Path $repo "$part\*") $dest -Recurse -Force
}
Get-ChildItem $src -Recurse -Directory | Where-Object { $_.Name -in 'bin', 'obj' } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# PODMIANA na wersje BAZOWA koordynatora (wgrana wczesniej przez WSL) oraz
# usuniecie testow, ktore na bazie sie nie kompiluja (uzywaja nowego API).
$baseline = Join-Path $stage 'LiteQueueCoordinator.base.cs'
if (-not (Test-Path $baseline)) { Write-Output 'GUARD=brak pliku bazowego'; exit 3 }
Copy-Item $baseline (Join-Path $src 'src\AccessibleMediaController.LiteHost\Protocol\LiteQueueCoordinator.cs') -Force
Remove-Item (Join-Path $src 'tests\AccessibleMediaController.LiteHost.ProtocolTests\QueueTransportTests.cs') -Force
$prog = Join-Path $src 'tests\AccessibleMediaController.LiteHost.ProtocolTests\Program.cs'
(Get-Content $prog -Raw).Replace(
    '("--transport", QueueTransportTests.Run),',
    '("--red", QueueTransportRedWitness.Run),') | Set-Content $prog -NoNewline

$proj = Join-Path $src 'tests\AccessibleMediaController.LiteHost.ProtocolTests\AccessibleMediaController.LiteHost.ProtocolTests.csproj'
Set-Location $src
& $dotnet build $proj --nologo -v minimal
Write-Output "BUILD-EXIT=$LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $dotnet run --project $proj --no-build -- --red
Write-Output "RED-EXIT=$LASTEXITCODE"
exit 0
