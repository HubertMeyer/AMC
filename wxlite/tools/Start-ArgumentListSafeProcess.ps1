Set-StrictMode -Version Latest

function ConvertTo-WindowsCommandLineArgument {
    [CmdletBinding()]
    param([Parameter(Mandatory)] [AllowEmptyString()] [string]$Argument)

    # CommandLineToArgvW-compatible quoting: quote every argument so that an
    # empty value and a trailing backslash are preserved on .NET Framework.
    $builder = [Text.StringBuilder]::new()
    [void]$builder.Append('"')
    $backslashCount = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') {
            $backslashCount++
            continue
        }
        if ($character -eq '"') {
            [void]$builder.Append('\', ($backslashCount * 2) + 1)
            [void]$builder.Append('"')
            $backslashCount = 0
            continue
        }
        if ($backslashCount -gt 0) {
            [void]$builder.Append('\', $backslashCount)
            $backslashCount = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashCount -gt 0) {
        [void]$builder.Append('\', $backslashCount * 2)
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Start-ArgumentListSafeProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [AllowEmptyCollection()] [AllowEmptyString()] [string[]]$ArgumentList,
        [Parameter(Mandatory)] [string]$WorkingDirectory
    )

    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $FilePath
    $start.WorkingDirectory = $WorkingDirectory
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    if ($null -ne $start.PSObject.Properties['ArgumentList']) {
        foreach ($argument in $ArgumentList) {
            [void]$start.ArgumentList.Add($argument)
        }
    }
    else {
        $start.Arguments = (($ArgumentList | ForEach-Object {
            ConvertTo-WindowsCommandLineArgument -Argument $_
        }) -join ' ')
    }
    return [Diagnostics.Process]::Start($start)
}

function Invoke-ArgumentListSafeProcessWithEvidence {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [AllowEmptyCollection()] [AllowEmptyString()] [string[]]$ArgumentList,
        [Parameter(Mandatory)] [string]$WorkingDirectory,
        [Parameter(Mandatory)] [string]$SourcePath,
        [Parameter(Mandatory)] [string]$EvidencePath
    )

    $evidence = [ordered]@{
        schemaVersion = 1
        createdUtc = [DateTime]::UtcNow.ToString("o")
        state = "starting"
        filePath = [IO.Path]::GetFullPath($FilePath)
        workingDirectory = [IO.Path]::GetFullPath($WorkingDirectory)
        sourcePath = [IO.Path]::GetFullPath($SourcePath)
        argumentList = @($ArgumentList)
        exitCode = $null
    }
    $evidence | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $EvidencePath -Encoding utf8 -ErrorAction Stop

    try {
        $process = Start-ArgumentListSafeProcess `
            -FilePath $FilePath `
            -ArgumentList $ArgumentList `
            -WorkingDirectory $WorkingDirectory
    }
    catch {
        $evidence.state = "launch-failed"
        $evidence.error = $_.Exception.Message
        $evidence | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $EvidencePath -Encoding utf8 -ErrorAction Stop
        throw
    }
    if ($null -eq $process) {
        $evidence.state = "launch-failed"
        $evidence.error = "Process.Start returned null."
        $evidence | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $EvidencePath -Encoding utf8 -ErrorAction Stop
        throw "Nie udało się uruchomić procesu."
    }
    try {
        $process.WaitForExit()
        $evidence.state = "exited"
        $evidence.exitCode = $process.ExitCode
        $evidence | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $EvidencePath -Encoding utf8 -ErrorAction Stop
        return [pscustomobject]@{ ExitCode = $process.ExitCode }
    }
    finally {
        $process.Dispose()
    }
}
