[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$BundleRoot,
    [ValidateRange(10, 120)] [int]$TimeoutSeconds = 35
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$bundle = [IO.Path]::GetFullPath($BundleRoot)
$launcher = Join-Path $bundle "AMC.exe"
$manifestPath = Join-Path $bundle "bundle-manifest.json"
$temporaryParent = [IO.Path]::GetFullPath((Join-Path $repositoryRoot ".test-tmp"))
$operationRoot = Join-Path $temporaryParent ("startup-smoke-" + [guid]::NewGuid().ToString("N"))
$resultPath = Join-Path $operationRoot "result.txt"

if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "Brak AMC.exe w testowanej paczce: $bundle"
}
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Brak bundle-manifest.json w testowanej paczce: $bundle"
}

New-Item -ItemType Directory -Path $operationRoot -Force | Out-Null
$previousResultPath = $env:AMC_STARTUP_SMOKE_RESULT
$process = $null
try {
    $env:AMC_STARTUP_SMOKE_RESULT = $resultPath
    $process = Start-Process -FilePath $launcher `
        -ArgumentList @("--sprawdz-start-cicho") `
        -WorkingDirectory $bundle `
        -PassThru -WindowStyle Hidden

    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        try {
            $process.Kill($true)
        }
        catch {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        throw "Kontrolowany start paczki przekroczył $TimeoutSeconds sekund."
    }
    if ($process.ExitCode -ne 0) {
        $failure = if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
            (Get-Content -LiteralPath $resultPath -Raw).Trim()
        }
        else {
            "brak szczegółów z interfejsu"
        }
        throw ("Kontrolowany start paczki zakończył się kodem {0}: {1}" -f `
            $process.ExitCode, $failure)
    }
    if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
        throw "Kontrolowany start nie zapisał potwierdzenia gotowości."
    }
    $result = (Get-Content -LiteralPath $resultPath -Raw).Trim()
    if ($result -ne "READY") {
        throw "Kontrolowany start nie potwierdził gotowości: $result"
    }

    Start-Sleep -Milliseconds 300
    $leftovers = @(
        Get-Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Path -and
                $_.Path.StartsWith(
                    $bundle + [IO.Path]::DirectorySeparatorChar,
                    [StringComparison]::OrdinalIgnoreCase)
            }
    )
    if ($leftovers.Count -gt 0) {
        throw "Kontrolowany start pozostawił procesy testowanej paczki."
    }

    Write-Output "Kontrolowany start interfejsu i hosta: OK ($bundle)"
}
finally {
    if ($null -ne $process) {
        $process.Dispose()
    }
    if ($null -eq $previousResultPath) {
        Remove-Item Env:AMC_STARTUP_SMOKE_RESULT -ErrorAction SilentlyContinue
    }
    else {
        $env:AMC_STARTUP_SMOKE_RESULT = $previousResultPath
    }
    if (Test-Path -LiteralPath $operationRoot) {
        Remove-Item -LiteralPath $operationRoot -Recurse -Force
    }
}
