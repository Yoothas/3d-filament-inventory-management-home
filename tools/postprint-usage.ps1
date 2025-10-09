param(
    [Parameter(Mandatory=$false)][double]$used_g,
    [Parameter(Mandatory=$false)][double]$used_mm3,
    [Parameter(Mandatory=$false)][double]$density,
    [Parameter(Mandatory=$false)][string]$gcode,
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

# Resolve grams: prefer used_g, else compute from used_mm3 and density/material
function Resolve-Grams {
    param([double]$g, [double]$mm3, [double]$dens, [string]$mat)
    if ($g -gt 0) { return [Math]::Round($g, 2) }
    if ($mm3 -gt 0) {
        # default densities by material (g/cm^3)
        $map = @{
            'pla' = 1.24; 'petg' = 1.27; 'abs' = 1.04; 'tpu' = 1.20; 'asa' = 1.07; 'nylon' = 1.15
        }
        $resolved = $dens
        if (-not $resolved -or $resolved -le 0) {
            if ($mat) {
                $k = $mat.ToLower()
                if ($map.ContainsKey($k)) { $resolved = $map[$k] }
            }
            if (-not $resolved -or $resolved -le 0) { $resolved = 1.24 } # default to PLA
        }
        # mm3 -> cm3: divide by 1000, then grams = density * volume_cm3
        return [Math]::Round(($mm3 / 1000.0) * $resolved, 2)
    }
    throw "Either -used_g or -used_mm3 must be provided."
}

# Try detect G-code path if not explicitly provided
if (-not $gcode -and $args.Count -gt 0) {
    if (Test-Path -LiteralPath $args[0]) { $gcode = $args[0] }
}

# If grams/mm3/material are not provided, attempt to parse from G-code header (Prusa/Anycubic style)
if ($gcode -and (Test-Path -LiteralPath $gcode)) {
    try {
        $header = Get-Content -LiteralPath $gcode -TotalCount 300 -ErrorAction Stop
        # Parse grams from header lines like: "; filament used [g] = 12.34" (can contain multiple numbers for multi-extruder)
        $gSum = $null
        foreach ($line in $header) {
            if ($line -match '^;\s*filament used \[g\]\s*=') {
                $nums = [regex]::Matches($line, '(\d+(?:\.\d+)?)') | ForEach-Object { [double]$_.Value }
                if ($nums.Count -gt 0) {
                    $gSum = ($nums | Measure-Object -Sum).Sum
                }
                break
            }
        }
        if (-not $used_g -and $gSum -ne $null) { $used_g = [Math]::Round($gSum,2) }

        # Parse cm3 if needed
        if (-not $used_g -and -not $used_mm3) {
            foreach ($line in $header) {
                if ($line -match '^;\s*filament used \[cm3\]\s*=') {
                    $nums = [regex]::Matches($line, '(\d+(?:\.\d+)?)') | ForEach-Object { [double]$_.Value }
                    if ($nums.Count -gt 0) {
                        $cm3 = ($nums | Measure-Object -Sum).Sum
                        $used_mm3 = $cm3 * 1000.0
                    }
                    break
                }
            }
        }

        # Parse material/color/brand lines: e.g., "; filament_type = PLA" "; filament_colour = #FF0000" "; filament_vendor = HATCHBOX"
        if (-not $material) {
            $matLine = $header | Where-Object { $_ -match '^;\s*filament_type\s*=\s*(.+)$' } | Select-Object -First 1
            if ($matLine) {
                $material = ($matLine -replace '^;\s*filament_type\s*=\s*', '').Trim(' "\'')
                if ($material -match ',') { $material = $material.Split(',')[0].Trim() }
            }
        }
        if (-not $color) {
            $colLine = $header | Where-Object { $_ -match '^;\s*filament_colou?r\s*=\s*(.+)$' } | Select-Object -First 1
            if ($colLine) {
                $color = ($colLine -replace '^;\s*filament_colou?r\s*=\s*', '').Trim(' "\'')
                if ($color -match ',') { $color = $color.Split(',')[0].Trim() }
            }
        }
        if (-not $brand) {
            $brandLine = $header | Where-Object { $_ -match '^;\s*filament_vendor\s*=\s*(.+)$' } | Select-Object -First 1
            if ($brandLine) {
                $brand = ($brandLine -replace '^;\s*filament_vendor\s*=\s*', '').Trim(' "\'')
                if ($brand -match ',') { $brand = $brand.Split(',')[0].Trim() }
            }
        }
        if (-not $job) { $job = [IO.Path]::GetFileName($gcode) }
    } catch {
        Write-Warning "Failed to parse G-code header: $($_.Exception.Message)"
    }
}

$grams = Resolve-Grams -g $used_g -mm3 $used_mm3 -dens $density -mat $material
Write-Host "[postprint] Looking up filament for material='$material' color='$color' brand='$brand' grams=$grams (from used_g=$used_g, used_mm3=$used_mm3, density=$density)"

$response = Find-Filament -mat $material -col $color -br $brand
if (-not $response -or -not $response.matches -or $response.count -eq 0) {
    Write-Warning "No matching filament found. Ensure inventory contains this material/color/brand."
    exit 0
}

$filament = $response.matches[0]
Write-Host "[postprint] Using filament: $($filament.brand) $($filament.color) ($($filament.material)) -> id=$($filament.id)"

$result = Use-Filament -id $filament.id -grams $grams -jobName $job
if ($result -and $result.filament) {
    Write-Host ("[postprint] Updated: used {0}g, remaining {1}g" -f $grams, $result.filament.remainingWeight)
} else {
    Write-Host ("[postprint] Updated: used {0}g" -f $grams)
}
