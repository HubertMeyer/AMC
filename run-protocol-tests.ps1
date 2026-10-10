# Buduje i uruchamia testy protokolu LiteHost na SDK Windows (SDK nie ma w WSL).
# Pakiety z istniejacego RestorePackagesPath -- nie sciagamy cache od nowa.
$ErrorActionPreference = 'Stop'
$legacyDotnet = 'C:\Users\Michal\amc-build-tools\dotnet-8.0.425\dotnet.exe'
$dotnet = if (Test-Path -LiteralPath $legacyDotnet) {
    $legacyDotnet
} else {
    (Get-Command dotnet -ErrorAction Stop).Source
}
$legacyPackages = 'C:\Users\Michal\amc-build-tools\nuget-packages'
if (Test-Path -LiteralPath $legacyPackages) {
    $env:NUGET_PACKAGES = $legacyPackages
}
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'

Set-Location $PSScriptRoot
$proj = 'tests\AccessibleMediaController.LiteHost.ProtocolTests\AccessibleMediaController.LiteHost.ProtocolTests.csproj'

& $dotnet restore $proj -p:NuGetAudit=false --ignore-failed-sources --nologo -v minimal
if ($LASTEXITCODE -ne 0) { Write-Output "RESTORE-EXIT=$LASTEXITCODE"; exit $LASTEXITCODE }

& $dotnet build $proj --no-restore --nologo -v minimal
if ($LASTEXITCODE -ne 0) { Write-Output "BUILD-EXIT=$LASTEXITCODE"; exit $LASTEXITCODE }

& $dotnet run --project $proj --no-build -- @args
Write-Output "TESTS-EXIT=$LASTEXITCODE"
exit $LASTEXITCODE
