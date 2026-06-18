param(
  [int]$Port = 8080,
  [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Get-BeijingDate([int]$offsetDays = 0) {
  $utcNow = [DateTime]::UtcNow
  $beijingNow = $utcNow.AddHours(8)
  $target = $beijingNow.Date.AddDays($offsetDays)
  return $target.ToString('yyyy-MM-dd')
}

$yesterday = Get-BeijingDate -offsetDays -1
$dataFile = Join-Path $projectRoot ("data/{0}.json" -f $yesterday)
$siteFile = Join-Path $projectRoot "site/index.html"

Write-Host "[Local Run] Project root: $projectRoot"
Write-Host "[Local Run] Expected data: $dataFile"

if (-not (Test-Path $siteFile)) {
  Write-Error "Missing site entry: $siteFile"
}

if (-not (Test-Path $dataFile)) {
  Write-Warning "Yesterday data not found: $dataFile"
  Write-Warning "Page may fall back to mock data."
}

$base = "http://127.0.0.1:$Port"
Write-Host "[Local Run] Health checks:"

try {
  $r1 = Invoke-WebRequest -Uri "$base/site/index.html" -UseBasicParsing -TimeoutSec 2
  Write-Host "  /site/index.html => $($r1.StatusCode)"
} catch {
  Write-Host "  /site/index.html => not started yet"
}

if (-not $NoOpen) {
  Start-Process "$base/site/index.html"
}

Write-Host "[Local Run] Starting server on $base ..."
python -m http.server $Port
