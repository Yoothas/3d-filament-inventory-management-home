param(
    [Parameter(Mandatory=$true)][double]$used_g,
    [Parameter(Mandatory=$false)][string]$material,
    [Parameter(Mandatory=$false)][string]$color,
    [Parameter(Mandatory=$false)][string]$brand,
    [Parameter(Mandatory=$false)][string]$job
)

# Allow TLS 1.2 for Invoke-RestMethod
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ErrorActionPreference = 'Stop'

# Resolve server base URL (local and network fallback)
$Port = $env:FILAMENT_SERVER_PORT
if (-not $Port -or $Port -eq '') { $Port = 3000 }
$HostLocal = "http://localhost:$Port"
$HostLAN = $env:FILAMENT_SERVER_HOST
if (-not $HostLAN -or $HostLAN -eq '') { $HostLAN = $HostLocal }

function Find-Filament {
    param([string]$mat, [string]$col, [string]$br)
    $query = @{}
    if ($mat) { $query.material = $mat }
    if ($col) { $query.color = $col }
    if ($br)  { $query.brand = $br }

    $q = ($query.GetEnumerator() | ForEach-Object { "{0}={1}" -f [uri]::EscapeDataString($_.Key), [uri]::EscapeDataString($_.Value) }) -join '&'

    $url = "$HostLAN/api/filaments/search?$q"
    try {
        return Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 5
    } catch {
        # Fallback to localhost if LAN URL fails
        $url = "$HostLocal/api/filaments/search?$q"
        return Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 5
    }
}

function Use-Filament {
    param([string]$id, [double]$grams, [string]$jobName)
    $body = @{ usedWeight = $grams; printJob = $jobName } | ConvertTo-Json
    $url = "$HostLAN/api/filaments/$id/use"
    try {
        return Invoke-RestMethod -Method POST -Uri $url -Body $body -ContentType 'application/json' -TimeoutSec 5
    } catch {
        # Fallback to localhost
        $url = "$HostLocal/api/filaments/$id/use"
        return Invoke-RestMethod -Method POST -Uri $url -Body $body -ContentType 'application/json' -TimeoutSec 5
    }
}

Write-Host "[postprint] Looking up filament for material='$material' color='$color' brand='$brand' used_g=$used_g"

$response = Find-Filament -mat $material -col $color -br $brand
if (-not $response -or -not $response.matches -or $response.count -eq 0) {
    Write-Warning "No matching filament found. Ensure inventory contains this material/color/brand."
    exit 0
}

$filament = $response.matches[0]
Write-Host "[postprint] Using filament: $($filament.brand) $($filament.color) ($($filament.material)) -> id=$($filament.id)"

$result = Use-Filament -id $filament.id -grams $used_g -jobName $job
Write-Host ("[postprint] Updated: used {0}g, remaining {1}g" -f $used_g, $result.filament.remainingWeight)
