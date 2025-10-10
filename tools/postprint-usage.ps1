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

# Optional logging to help troubleshoot slicer integration
$Global:LogPath = $null
try {
    $logEnv = $env:FILAMENT_POSTPRINT_LOG
    if ($null -ne $logEnv -and $logEnv -ne '') {
        if ($logEnv -eq '1') {
            $base = Join-Path -Path $env:LOCALAPPDATA -ChildPath 'FilamentInventory'
            if (-not (Test-Path -LiteralPath $base)) { New-Item -ItemType Directory -Path $base -Force | Out-Null }
            $Global:LogPath = Join-Path -Path $base -ChildPath 'postprint.log'
        } else {
            $Global:LogPath = $logEnv
            $dir = Split-Path -Parent $Global:LogPath
            if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        }
    }
} catch { }

function Write-Log {
    param([string]$message)
    try {
        Write-Host $message
        if ($Global:LogPath) {
            $ts = (Get-Date -Format s)
            Add-Content -LiteralPath $Global:LogPath -Value ("[$ts] $message")
        }
    } catch { }
}

# Resolve server base URL (local and network fallback)
$Port = $env:FILAMENT_SERVER_PORT
if (-not $Port -or $Port -eq '') { $Port = 3000 }
$HostLocal = "http://localhost:$Port"
$HostLAN = $env:FILAMENT_SERVER_HOST
if (-not $HostLAN -or $HostLAN -eq '') { $HostLAN = $HostLocal }

# Map common slicer/printer brand names to actual inventory brands
function Map-BrandName {
    param([string]$slicerBrand)
    if (-not $slicerBrand) { return $slicerBrand }
    
    # Case-insensitive mapping
    $lower = $slicerBrand.ToLower()
    switch ($lower) {
        'anycubic' { 
            Write-Log "[postprint] Mapped slicer brand '$slicerBrand' -> 'ATA'"
            return 'ATA' 
        }
        { $_ -match '^generic' } { 
            Write-Log "[postprint] Mapped generic brand '$slicerBrand' to empty (will use fuzzy matching)"
            return '' 
        }
        'default' { 
            Write-Log "[postprint] Mapped generic brand '$slicerBrand' to empty (will use fuzzy matching)"
            return '' 
        }
    }
    
    return $slicerBrand
}

# Map common slicer color names to actual inventory colors
function Map-ColorName {
    param([string]$slicerColor)
    if (-not $slicerColor) { return $slicerColor }
    
    # Case-insensitive mapping
    $lower = $slicerColor.ToLower()
    switch ($lower) {
        'clear' { 
            Write-Log "[postprint] Mapped slicer color '$slicerColor' -> 'Translucent'"
            return 'Translucent' 
        }
        'transparent' { 
            Write-Log "[postprint] Mapped slicer color '$slicerColor' -> 'Translucent'"
            return 'Translucent' 
        }
        'natural' { 
            Write-Log "[postprint] Mapped slicer color '$slicerColor' -> 'Translucent'"
            return 'Translucent' 
        }
        { $_ -match '^light.?gr[ae]y' } { 
            Write-Log "[postprint] Mapped slicer color '$slicerColor' -> 'Translucent' (light gray variant)"
            return 'Translucent' 
        }
        { $_ -match '^gr[ae]y' } { 
            Write-Log "[postprint] Mapped slicer color '$slicerColor' might be translucent - trying exact match first"
            return $slicerColor  # Try exact first, fuzzy matching will handle fallback
        }
    }
    
    return $slicerColor
}

function Find-Filament {
    param([string]$mat, [string]$col, [string]$br)
    
    # Try exact match first
    $query = @{}
    if ($mat) { $query.material = $mat }
    if ($col) { $query.color = $col }
    if ($br)  { $query.brand = $br }

    $q = ($query.GetEnumerator() | ForEach-Object { "{0}={1}" -f [uri]::EscapeDataString($_.Key), [uri]::EscapeDataString($_.Value) }) -join '&'

    $url = "$HostLAN/api/filaments/search?$q"
    try {
        $res = Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 5
        if ($res -and $res.matches -and $res.count -gt 0) { return $res }
    } catch {
        # Fallback to localhost if LAN URL fails
        try {
            $url = "$HostLocal/api/filaments/search?$q"
            $resLocal = Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 5
            if ($resLocal -and $resLocal.matches -and $resLocal.count -gt 0) { return $resLocal }
        } catch { }
    }

    # If exact match failed, try fuzzy matching by removing brand and searching by material+color only
    if ($mat -or $col) {
        Write-Log "[postprint] Exact match failed, trying material+color only (ignoring brand '$br')"
        $fuzzyQuery = @{}
        if ($mat) { $fuzzyQuery.material = $mat }
        if ($col) { $fuzzyQuery.color = $col }
        
        $fq = ($fuzzyQuery.GetEnumerator() | ForEach-Object { "{0}={1}" -f [uri]::EscapeDataString($_.Key), [uri]::EscapeDataString($_.Value) }) -join '&'
        
        $furl = "$HostLAN/api/filaments/search?$fq"
        try {
            $fres = Invoke-RestMethod -Method GET -Uri $furl -TimeoutSec 5
            if ($fres -and $fres.matches -and $fres.count -gt 0) { 
                Write-Log "[postprint] Found fuzzy match: ignoring brand mismatch"
                return $fres 
            }
        } catch {
            try {
                $furl = "$HostLocal/api/filaments/search?$fq"
                $fresLocal = Invoke-RestMethod -Method GET -Uri $furl -TimeoutSec 5
                if ($fresLocal -and $fresLocal.matches -and $fresLocal.count -gt 0) { 
                    Write-Log "[postprint] Found fuzzy match (localhost): ignoring brand mismatch"
                    return $fresLocal 
                }
            } catch { }
        }

        # If material+color failed and color looks like it might be translucent/clear variants, try with "Translucent"
        if ($col -and ($col -match '^gr[ae]y|silver|clear|transparent|natural|white' -and $col -notmatch 'translucent')) {
            Write-Log "[postprint] Trying color variant: '$col' -> 'Translucent' for material '$mat'"
            $altQuery = @{}
            if ($mat) { $altQuery.material = $mat }
            $altQuery.color = 'Translucent'
            
            $aq = ($altQuery.GetEnumerator() | ForEach-Object { "{0}={1}" -f [uri]::EscapeDataString($_.Key), [uri]::EscapeDataString($_.Value) }) -join '&'
            
            $aurl = "$HostLAN/api/filaments/search?$aq"
            try {
                $ares = Invoke-RestMethod -Method GET -Uri $aurl -TimeoutSec 5
                if ($ares -and $ares.matches -and $ares.count -gt 0) { 
                    Write-Log "[postprint] Found color variant match: '$col' matched as 'Translucent'"
                    return $ares 
                }
            } catch {
                try {
                    $aurl = "$HostLocal/api/filaments/search?$aq"
                    $aresLocal = Invoke-RestMethod -Method GET -Uri $aurl -TimeoutSec 5
                    if ($aresLocal -and $aresLocal.matches -and $aresLocal.count -gt 0) { 
                        Write-Log "[postprint] Found color variant match (localhost): '$col' matched as 'Translucent'"
                        return $aresLocal 
                    }
                } catch { }
            }
        }
    }

    # If still no match, try material-only as last resort
    if ($mat) {
        Write-Log "[postprint] Material+color match failed, trying material-only ('$mat')"
        $matUrl = "$HostLAN/api/filaments/search?material=" + [uri]::EscapeDataString($mat)
        try {
            $matRes = Invoke-RestMethod -Method GET -Uri $matUrl -TimeoutSec 5
            if ($matRes -and $matRes.matches -and $matRes.count -gt 0) { 
                Write-Log "[postprint] Found material-only match (first available $mat spool)"
                return $matRes 
            }
        } catch {
            try {
                $matUrl = "$HostLocal/api/filaments/search?material=" + [uri]::EscapeDataString($mat)
                $matResLocal = Invoke-RestMethod -Method GET -Uri $matUrl -TimeoutSec 5
                if ($matResLocal -and $matResLocal.matches -and $matResLocal.count -gt 0) { 
                    Write-Log "[postprint] Found material-only match (localhost, first available $mat spool)"
                    return $matResLocal 
                }
            } catch { }
        }
    }

    return $null
}

function Use-Filament {
    param([string]$id, [double]$grams, [string]$jobName)
    $body = @{ usedWeight = $grams; printJob = $jobName } | ConvertTo-Json
    $url = "$HostLAN/api/filaments/$id/use"
    try {
        $res = Invoke-RestMethod -Method POST -Uri $url -Body $body -ContentType 'application/json' -TimeoutSec 5
        return $res
    } catch {
        # Fallback to localhost
        $url = "$HostLocal/api/filaments/$id/use"
        $resLocal = Invoke-RestMethod -Method POST -Uri $url -Body $body -ContentType 'application/json' -TimeoutSec 5
        return $resLocal
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

# If grams/mm3/material are not provided, attempt to parse from G-code (Prusa/Anycubic style)
function Get-GcodeWindow {
    param([string]$path, [int]$headCount = 500, [int]$tailCount = 500)
    $lines = @()
    try { $h = Get-Content -LiteralPath $path -TotalCount $headCount -ErrorAction Stop } catch { $h = @() }
    try { $t = Get-Content -LiteralPath $path -Tail $tailCount -ErrorAction Stop } catch { $t = @() }
    # Merge, avoiding duplicate concatenation when file has fewer lines than headCount+tailCount
    $lines = @($h + $t)
    return $lines
}

if ($gcode -and (Test-Path -LiteralPath $gcode)) {
    try {
        $window = Get-GcodeWindow -path $gcode -headCount 500 -tailCount 500
        if (-not $window -or $window.Count -eq 0) { $window = Get-Content -LiteralPath $gcode -TotalCount 1000 }

        # Parse grams from lines like: "; filament used [g] = 12.34" (may include multiple values for multi-extruder)
        $gSum = $null
        foreach ($line in $window) {
            if ($line -match '^;\s*filament used \[g\]\s*=') {
                $nums = [regex]::Matches($line, '(\d+(?:\.\d+)?)') | ForEach-Object { [double]$_.Value }
                if ($nums.Count -gt 0) { $gSum = ($nums | Measure-Object -Sum).Sum }
                break
            }
        }

        # If not found in window, try a fast full-file search
        if ($gSum -eq $null) {
            try {
                $match = Select-String -Path $gcode -Pattern '^;\s*filament used \[g\]\s*=' -SimpleMatch:$false -CaseSensitive:$false | Select-Object -First 1
                if ($match) {
                    $nums = [regex]::Matches($match.Line, '(\d+(?:\.\d+)?)') | ForEach-Object { [double]$_.Value }
                    if ($nums.Count -gt 0) { $gSum = ($nums | Measure-Object -Sum).Sum }
                }
            } catch { }
        }
        if (-not $used_g -and $gSum -ne $null) { $used_g = [Math]::Round($gSum,2) }

        # Parse cm3 if needed
        if (-not $used_g -and -not $used_mm3) {
            $cm3Sum = $null
            foreach ($line in $window) {
                if ($line -match '^;\s*filament used \[cm3\]\s*=') {
                    $nums = [regex]::Matches($line, '(\d+(?:\.\d+)?)') | ForEach-Object { [double]$_.Value }
                    if ($nums.Count -gt 0) { $cm3Sum = ($nums | Measure-Object -Sum).Sum }
                    break
                }
            }
            if ($cm3Sum -eq $null) {
                try {
                    $match2 = Select-String -Path $gcode -Pattern '^;\s*filament used \[cm3\]\s*=' -SimpleMatch:$false -CaseSensitive:$false | Select-Object -First 1
                    if ($match2) {
                        $nums = [regex]::Matches($match2.Line, '(\d+(?:\.\d+)?)') | ForEach-Object { [double]$_.Value }
                        if ($nums.Count -gt 0) { $cm3Sum = ($nums | Measure-Object -Sum).Sum }
                    }
                } catch { }
            }
            if ($cm3Sum -ne $null) { $used_mm3 = $cm3Sum * 1000.0 }
        }

        # Parse material/color/brand lines
        if (-not $material) {
            $matLine = $window | Where-Object { $_ -match '^;\s*filament_type\s*=\s*(.+)$' } | Select-Object -First 1
            if (-not $matLine) {
                try {
                    $m = Select-String -Path $gcode -Pattern '^;\s*filament_type\s*=\s*(.+)$' -CaseSensitive:$false | Select-Object -First 1
                    if ($m) { $matLine = $m.Line }
                } catch { }
            }
            if ($matLine) {
                $material = ($matLine -replace '^;\s*filament_type\s*=\s*', '').Trim(' "''')
                if ($material -match ',') { $material = $material.Split(',')[0].Trim() }
            }
        }
        if (-not $color) {
            $colLine = $window | Where-Object { $_ -match '^;\s*filament_colou?r\s*=\s*(.+)$' } | Select-Object -First 1
            if (-not $colLine) {
                try {
                    $c = Select-String -Path $gcode -Pattern '^;\s*filament_colou?r\s*=\s*(.+)$' -CaseSensitive:$false | Select-Object -First 1
                    if ($c) { $colLine = $c.Line }
                } catch { }
            }
            if ($colLine) {
                $color = ($colLine -replace '^;\s*filament_colou?r\s*=\s*', '').Trim(' "''')
                if ($color -match ',') { $color = $color.Split(',')[0].Trim() }
            }
        }
        if (-not $brand) {
            $brandLine = $window | Where-Object { $_ -match '^;\s*filament_vendor\s*=\s*(.+)$' } | Select-Object -First 1
            if (-not $brandLine) {
                try {
                    $b = Select-String -Path $gcode -Pattern '^;\s*filament_vendor\s*=\s*(.+)$' -CaseSensitive:$false | Select-Object -First 1
                    if ($b) { $brandLine = $b.Line }
                } catch { }
            }
            if ($brandLine) {
                $brand = ($brandLine -replace '^;\s*filament_vendor\s*=\s*', '').Trim(' "''')
                if ($brand -match ',') { $brand = $brand.Split(',')[0].Trim() }
            }
        }
        
        # Parse job name from G-code headers if not provided
        if (-not $job) { 
            # Try common job name patterns in G-code headers
            $jobPatterns = @(
                '^;\s*generated by .+ for (.+)$',           # "generated by Slicer for filename"
                '^;\s*print job\s*[:=]\s*(.+)$',            # "print job: filename" or "print job = filename"
                '^;\s*job\s*[:=]\s*(.+)$',                  # "job: filename"
                '^;\s*model\s*[:=]\s*(.+)$',                # "model: filename"
                '^;\s*filename\s*[:=]\s*(.+)$'              # "filename: filename"
            )
            
            foreach ($pattern in $jobPatterns) {
                $jobLine = $window | Where-Object { $_ -match $pattern } | Select-Object -First 1
                if (-not $jobLine) {
                    try {
                        $j = Select-String -Path $gcode -Pattern $pattern -CaseSensitive:$false | Select-Object -First 1
                        if ($j) { $jobLine = $j.Line }
                    } catch { }
                }
                if ($jobLine) {
                    if ($jobLine -match $pattern) {
                        $job = $matches[1].Trim(' "''')
                        # Clean up common extensions and paths
                        $job = [IO.Path]::GetFileNameWithoutExtension($job)
                        Write-Log "[postprint] Parsed job name from header: '$job'"
                        break
                    }
                }
            }
            
            # Fallback: use filename if no header found
            if (-not $job) { 
                $job = [IO.Path]::GetFileNameWithoutExtension($gcode)
                Write-Log "[postprint] Using filename as job name: '$job'"
            }
        }
    } catch {
        Write-Warning "Failed to parse G-code: $($_.Exception.Message)"
    }
}

$grams = Resolve-Grams -g $used_g -mm3 $used_mm3 -dens $density -mat $material

# Map slicer names to inventory names
$originalBrand = $brand
$originalColor = $color
$brand = Map-BrandName -slicerBrand $brand
$color = Map-ColorName -slicerColor $color

Write-Log "[postprint] Looking up filament for material='$material' color='$color' brand='$brand' grams=$grams (original: brand='$originalBrand' color='$originalColor', from used_g=$used_g, used_mm3=$used_mm3, density=$density)"

$response = Find-Filament -mat $material -col $color -br $brand
if (-not $response -or -not $response.matches -or $response.count -eq 0) {
    Write-Warning "No matching filament found in inventory."
    Write-Log "[postprint] No matches found for material='$material' color='$color' brand='$brand' (tried exact, fuzzy material+color, and material-only)"
    Write-Log "[postprint] Suggestion: Check your inventory has filaments with material '$material'. Brand names from slicer ('$brand') may not match inventory."
    exit 0
}

$filament = $response.matches[0]
Write-Log "[postprint] Using filament: $($filament.brand) $($filament.color) ($($filament.material)) -> id=$($filament.id)"

$result = Use-Filament -id $filament.id -grams $grams -jobName $job
if ($result -and $result.filament) {
    Write-Log ("[postprint] Updated: used {0}g, remaining {1}g" -f $grams, $result.filament.remainingWeight)
} else {
    Write-Log ("[postprint] Updated: used {0}g" -f $grams)
}
