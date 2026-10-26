[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$')]
    [string]$Version,

    [Parameter(Mandatory)]
    [string]$ArtifactsDirectory,

    [string]$NotesPath = "",
    [string]$Repository = "michalkasperczak/AMC",
    [switch]$Publish
)

# Zgodność ze starszym wywołaniem REL-001. Nowe wydania obu profili korzystają
# ze wspólnej, profilowanej bramki Publish-AMCRelease.ps1.
$arguments = @{
    Profile = "public"
    Version = $Version
    ArtifactsDirectory = $ArtifactsDirectory
    NotesPath = $NotesPath
    Repository = $Repository
}
if ($Publish) {
    $arguments.Publish = $true
}
& (Join-Path $PSScriptRoot "Publish-AMCRelease.ps1") @arguments
if (-not $?) {
    throw "Wspólna bramka publikacji AMC zakończyła się niepowodzeniem."
}
