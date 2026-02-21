param(
    [Parameter(Mandatory = $true)]
    [string]$Preset,
    [string]$InputDir = "in",
    [string]$Glob = "*.png",
    [string]$OutDir = "out",
    [string]$ReportsDir = "reports"
)

$ErrorActionPreference = "Stop"
python -m src.cli --preset $Preset --input-dir $InputDir --glob $Glob --outdir $OutDir --reports-dir $ReportsDir
