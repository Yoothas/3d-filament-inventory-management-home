#!/usr/bin/env python3
"""
Post-print filament usage tracker for 3D Filament Inventory Management
This script automatically updates filament inventory after a print job completes.
Can be called from slicer post-processing scripts or manually.
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("ERROR: requests module not found. Install with: pip install requests")
    sys.exit(1)


# Configuration
DEFAULT_PORT = 5000  # Updated to match Flask server default
LOG_PATH = None


def setup_logging():
    """Initialize logging if enabled via environment variable"""
    global LOG_PATH
    log_env = os.environ.get('FILAMENT_POSTPRINT_LOG', '')
    
    if log_env:
        if log_env == '1':
            # Default log location
            base = Path.home() / '.filament-inventory'
            base.mkdir(exist_ok=True)
            log_path_temp = base / 'postprint.log'
        else:
            # Custom log path
            log_path_temp = Path(log_env)
            log_path_temp.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH = log_path_temp  # type: ignore[misc]


def write_log(message: str):
    """Write log message to console and optionally to log file"""
    print(message)
    if LOG_PATH:
        try:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            with open(LOG_PATH, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass


def get_server_urls() -> Tuple[str, str]:
    """Get local and network server URLs"""
    port = os.environ.get('FILAMENT_SERVER_PORT', DEFAULT_PORT)
    host_local = f"http://localhost:{port}"
    host_lan = os.environ.get('FILAMENT_SERVER_HOST', host_local)
    return host_local, host_lan


def get_auth_headers() -> Dict[str, str]:
    """Build auth headers if FILAMENT_API_KEY is set."""
    api_key = os.environ.get('FILAMENT_API_KEY', '')
    if api_key:
        return {'X-API-Key': api_key}
    return {}


def map_brand_name(slicer_brand: Optional[str]) -> Optional[str]:
    """Map common slicer/printer brand names to inventory brand names"""
    if not slicer_brand:
        return slicer_brand
    
    lower = slicer_brand.lower()
    
    if 'generic' in lower or lower == 'default':
        write_log(f"[postprint] Ignoring generic brand '{slicer_brand}' - will use material+color matching")
        return None
    
    return slicer_brand


def map_color_name(slicer_color: Optional[str]) -> Optional[str]:
    """Map common slicer color names to inventory color names"""
    if not slicer_color:
        return slicer_color
    
    lower = slicer_color.lower()
    
    # Handle hex color codes - convert to common color names
    if re.match(r'^#[0-9a-f]{6}$', lower):
        hex_code = lower
        write_log(f"[postprint] Detected hex color code: {hex_code}")
        
        # Parse RGB values
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)
        
        # Calculate how close to grayscale this is
        rgb_values = [r, g, b]
        max_diff = max(rgb_values) - min(rgb_values)
        is_grayscale = max_diff < 30  # RGB values are very similar
        
        write_log(f"[postprint] Hex {hex_code} RGB analysis: R={r} G={g} B={b}, max_diff={max_diff}, is_grayscale={is_grayscale}")
        
        # If NOT grayscale, it's likely a multi-color filament - don't try to name it
        if not is_grayscale:
            write_log(f"[postprint] Hex {hex_code} is NOT pure grayscale - likely multi-color filament, will use material-only matching")
            return None
        
        # For grayscale colors, determine brightness
        brightness = (r + g + b) / 3  # Average brightness 0-255
        
        # Map grayscale to color names (check specific colors BEFORE generic dark threshold)
        # Pure Black: very dark grayscale (RGB < 60 each)
        if brightness < 60:
            write_log(f"[postprint] Hex {hex_code} -> 'Black' (RGB: {r},{g},{b}, brightness={brightness:.0f})")
            return 'Black'
        
        # White: high RGB values
        if r > 200 and g > 200 and b > 200:
            write_log(f"[postprint] Hex {hex_code} -> 'White' (RGB: {r},{g},{b})")
            return 'White'
        
        # Red: high R, low G and B
        if r > 200 and g < 100 and b < 100:
            write_log(f"[postprint] Hex {hex_code} -> 'Red' (RGB: {r},{g},{b})")
            return 'Red'
        
        # Green: low R, high G, low B
        if r < 100 and g > 200 and b < 100:
            write_log(f"[postprint] Hex {hex_code} -> 'Green' (RGB: {r},{g},{b})")
            return 'Green'
        
        # Blue: low R and G, high B
        if r < 100 and g < 100 and b > 200:
            write_log(f"[postprint] Hex {hex_code} -> 'Blue' (RGB: {r},{g},{b})")
            return 'Blue'
        
        # Gray: similar RGB values and mid brightness
        if is_grayscale:
            if brightness < 100:
                write_log(f"[postprint] Hex {hex_code} -> 'Dark Gray' (RGB: {r},{g},{b}), brightness={brightness:.0f}")
                return 'Dark Gray'
            elif brightness < 180:
                write_log(f"[postprint] Hex {hex_code} -> 'Gray' (RGB: {r},{g},{b}), brightness={brightness:.0f}")
                return 'Gray'
        
        # If we can't determine the color, return None to use material-only matching
        write_log(f"[postprint] Hex {hex_code} -> Unknown color (RGB: {r},{g},{b}), will use material-only matching")
        return None
    
    # Direct mappings
    if lower in ['clear', 'transparent', 'natural']:
        write_log(f"[postprint] Mapped slicer color '{slicer_color}' -> 'Translucent'")
        return 'Translucent'
    
    # Pattern-based mappings
    if re.match(r'^light.?gr[ae]y', lower):
        write_log(f"[postprint] Mapped slicer color '{slicer_color}' -> 'Translucent' (light gray variant)")
        return 'Translucent'
    
    if re.match(r'^gr[ae]y', lower):
        write_log(f"[postprint] Mapped slicer color '{slicer_color}' might be translucent - trying exact match first")
        return slicer_color
    
    if re.match(r'^white', lower) and not re.search(r'snow|pure|bright', lower):
        write_log(f"[postprint] Mapped slicer color '{slicer_color}' might be translucent - trying exact match first")
        return slicer_color
    
    return slicer_color


def find_filament(material: Optional[str], color: Optional[str], brand: Optional[str]) -> Optional[Dict]:
    """Search for matching filament in inventory with fuzzy matching fallback"""
    host_local, host_lan = get_server_urls()
    
    def try_search(url: str) -> Optional[Dict]:
        try:
            response = requests.get(url, timeout=5, headers=get_auth_headers())
            response.raise_for_status()
            data = response.json()
            if data and data.get('matches') and data.get('count', 0) > 0:
                return data
        except Exception:
            pass
        return None
    
    # Build query parameters
    params = {}
    if material:
        params['material'] = material
    if color:
        params['color'] = color
    if brand:
        params['brand'] = brand
    
    # Try exact match first
    query_string = urlencode(params)
    
    result = None
    for base_url in [host_lan, host_local]:
        url = f"{base_url}/api/filaments/search?{query_string}"
        result = try_search(url)
        if result:
            break
    
    # If we got results but multiple matches, pick the best one
    if result and result.get('count', 0) > 1:
        matches = result.get('matches', [])
        write_log(f"[postprint] Found {len(matches)} matches, selecting best match")
        
        # Scoring system: exact color match > multi-color detection > recent usage > remaining weight
        best_match = None
        best_score = -1
        
        for match in matches:
            score = 0
            
            # Exact color match (including multi-color like "Black Red")
            match_color = match.get('color', '').lower()
            if color and color.lower() == match_color:
                score += 100
                write_log(f"[postprint] Exact color match: '{match_color}' (+100 points)")
            
            # Multi-color detection: if searching for multi-color, prefer multi-color matches
            if color and ' ' in color.lower() and ' ' in match_color:
                # Both are multi-color - check how many words match
                search_words = set(color.lower().split())
                match_words = set(match_color.lower().split())
                matching_words = len(search_words & match_words)
                total_words = len(search_words | match_words)
                
                if matching_words > 0:
                    similarity = (matching_words / total_words) * 100
                    score += int(similarity)
                    write_log(f"[postprint] Multi-color similarity for '{match_color}': {matching_words}/{len(search_words)} words match ({similarity:.0f}%) (+{int(similarity)} points)")
            
            # Single-word color containing search term
            elif color and color.lower() in match_color and ' ' not in match_color:
                score += 50  # Single-word color containing search term
                write_log(f"[postprint] Partial color match: '{match_color}' (+50 points)")
            
            # Brand substring match bonus
            if brand and brand.lower() in match.get('brand', '').lower():
                score += 30
                write_log(f"[postprint] Brand substring match: '{brand}' in '{match['brand']}' (+30 points)")
            
            # Recently used bonus
            if match.get('lastUsed'):
                score += 20
                write_log("[postprint] Recently used filament (+20 points)")
            
            # Remaining weight bonus (prefer filaments with more material)
            remaining = match.get('remainingWeight', 0)
            if remaining > 1000:
                score += 10
                write_log(f"[postprint] High remaining weight: {remaining}g (+10 points)")
            
            write_log(f"[postprint] Filament '{match['brand']} {match['color']}' scored {score} points")
            
            if score > best_score:
                best_score = score
                best_match = match
        
        if best_match:
            write_log(f"[postprint] Selected: '{best_match['brand']} {best_match['color']} {best_match['material']}' with {best_match.get('remainingWeight')}g remaining")
            return {'matches': [best_match], 'count': 1}
    
    # Single match - return as-is
    if result and result.get('count', 0) == 1:
        match = result['matches'][0]
        write_log(f"[postprint] Single match found: '{match['brand']} {match['color']} {match['material']}'")
        return result
    
    # Fuzzy matching: try without brand
    if (material or color) and brand:
        write_log(f"[postprint] Exact match failed, trying material+color only (ignoring brand '{brand}')")
        fuzzy_params = {}
        if material:
            fuzzy_params['material'] = material
        if color:
            fuzzy_params['color'] = color
        
        query_string = urlencode(fuzzy_params)
        
        for base_url in [host_lan, host_local]:
            url = f"{base_url}/api/filaments/search?{query_string}"
            result = try_search(url)
            if result:
                # Check if any match has the brand as a substring (e.g., "Anycubic" in "Anycubic High Speed")
                for match in result.get('matches', []):
                    if brand.lower() in match.get('brand', '').lower():
                        write_log(f"[postprint] Found partial brand match: '{brand}' found in '{match['brand']}'")
                        return {'matches': [match], 'count': 1}
                
                write_log("[postprint] Found fuzzy match: ignoring brand mismatch")
                return result
    
    # Try color variants (translucent)
    if color and re.search(r'gr[ae]y|silver|clear|transparent|natural|white', color, re.IGNORECASE):
        if 'translucent' not in color.lower():
            write_log(f"[postprint] Trying color variant: '{color}' -> 'Translucent' for material '{material}'")
            alt_params = {}
            if material:
                alt_params['material'] = material
            alt_params['color'] = 'Translucent'
            
            query_string = urlencode(alt_params)
            
            for base_url in [host_lan, host_local]:
                url = f"{base_url}/api/filaments/search?{query_string}"
                result = try_search(url)
                if result:
                    write_log(f"[postprint] Found color variant match: '{color}' matched as 'Translucent'")
                    return result
    
    # Special case: PLA with missing/generic color
    if material and material.upper() == 'PLA':
        if not color or re.match(r'^(|PLA|Generic|Basic|Default|Standard)$', color, re.IGNORECASE):
            write_log(f"[postprint] Trying PLA with missing/generic color -> 'Translucent' (material '{material}', color '{color}')")
            
            for base_url in [host_lan, host_local]:
                url = f"{base_url}/api/filaments/search?material=PLA&color=Translucent"
                result = try_search(url)
                if result:
                    write_log("[postprint] Found generic PLA match: assumed 'Translucent'")
                    return result
    
    # Material-only as last resort
    if material:
        write_log(f"[postprint] Material+color match failed, trying material-only ('{material}')")
        
        for base_url in [host_lan, host_local]:
            url = f"{base_url}/api/filaments/search?material={material}"
            result = try_search(url)
            if result:
                write_log(f"[postprint] Found material-only match (first available {material} spool)")
                return result
    
    return None


def use_filament(filament_id: str, grams: float, job_name: str) -> Optional[Dict]:
    """Update filament usage in inventory"""
    host_local, host_lan = get_server_urls()
    
    payload = {
        'usedWeight': grams,
        'printJob': job_name
    }
    
    for base_url in [host_lan, host_local]:
        try:
            url = f"{base_url}/api/filaments/{filament_id}/use"
            response = requests.post(url, json=payload, timeout=5, headers=get_auth_headers())
            response.raise_for_status()
            return response.json()
        except Exception:
            continue
    
    return None


def parse_gcode(gcode_path: Path) -> Dict[str, Any]:
    """
    Parse G-code file for usage information and metadata.
    IMPORTANT: Prioritizes FOOTER data (actual usage) over HEADER data (estimates).
    This ensures we only deduct what was actually printed, not what was estimated.
    """
    info: Dict[str, Any] = {
        'used_g': None,
        'used_mm3': None,
        'material': None,
        'color': None,
        'brand': None,
        'job': None
    }
    
    if not gcode_path.exists():
        return info
    
    try:
        # Read header (first 500 lines) and footer (last 1000 lines) separately
        header_lines = []
        footer_lines = []
        
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first 500 lines (header with estimates)
            for i, line in enumerate(f):
                if i >= 500:
                    break
                header_lines.append(line.strip())
            
            # Seek to end and read last 2000 lines (footer with actual usage)
            try:
                f.seek(0, 2)  # End of file
                file_size = f.tell()
                
                # Estimate position for last 2000 lines (assume ~100 chars per line)
                seek_pos = max(0, file_size - 2000 * 100)
                f.seek(seek_pos)
                f.readline()  # Skip partial line
                
                tail_lines = f.readlines()
                footer_lines = [line.strip() for line in tail_lines[-2000:]]
            except Exception:
                pass
        
        # PRIORITY 1: Parse FOOTER for actual usage (what was really printed)
        # Look in the LAST 1000 lines for actual usage
        write_log("[postprint] Parsing footer for actual usage data...")
        actual_footer_lines = footer_lines[-1000:] if len(footer_lines) > 1000 else footer_lines
        
        for line in reversed(actual_footer_lines):  # Start from end (most recent data)
            # Anycubic Slicer: ; filament used [g] = 123.45
            if not info['used_g'] and re.match(r'^\s*;\s*filament used \[g\]\s*=', line, re.IGNORECASE):
                numbers = re.findall(r'(\d+(?:\.\d+)?)', line)
                if numbers:
                    info['used_g'] = sum(float(n) for n in numbers)
                    write_log(f"[postprint] Found ACTUAL usage in footer: {info['used_g']}g")
            
            # Anycubic Slicer: ; filament used [cm3] = 12.34
            if not info['used_mm3'] and not info['used_g'] and re.match(r'^\s*;\s*filament used \[cm3\]\s*=', line, re.IGNORECASE):
                numbers = re.findall(r'(\d+(?:\.\d+)?)', line)
                if numbers:
                    cm3 = sum(float(n) for n in numbers)
                    info['used_mm3'] = cm3 * 1000.0
                    write_log(f"[postprint] Found ACTUAL usage in footer: {cm3}cm³ ({info['used_mm3']}mm³)")
        
        # If no usage found in footer, check header (but warn about estimates)
        if not info['used_g'] and not info['used_mm3']:
            write_log("[postprint] No actual usage in footer, checking header for estimates...")
            for line in header_lines:
                # Anycubic Slicer: ; filament used [g] = 123.45
                if not info['used_g'] and re.match(r'^\s*;\s*filament used \[g\]\s*=', line, re.IGNORECASE):
                    numbers = re.findall(r'(\d+(?:\.\d+)?)', line)
                    if numbers:
                        info['used_g'] = sum(float(n) for n in numbers)
                        write_log(f"[postprint] WARNING: Using ESTIMATED usage from header: {info['used_g']}g")
                        write_log("[postprint] This assumes the print completed successfully!")
                
                # Bambu Studio: ; total filament weight [g] : 923.38
                if not info['used_g'] and re.match(r'^\s*;\s*total filament weight \[g\]\s*:', line, re.IGNORECASE):
                    match = re.search(r':\s*(\d+(?:\.\d+)?)', line)
                    if match:
                        info['used_g'] = float(match.group(1))
                        write_log(f"[postprint] Found Bambu Studio total weight: {info['used_g']}g")
                        write_log("[postprint] This assumes the print completed successfully!")
                
                # Anycubic Slicer: ; filament used [cm3] = 12.34
                if not info['used_mm3'] and not info['used_g'] and re.match(r'^\s*;\s*filament used \[cm3\]\s*=', line, re.IGNORECASE):
                    numbers = re.findall(r'(\d+(?:\.\d+)?)', line)
                    if numbers:
                        cm3 = sum(float(n) for n in numbers)
                        info['used_mm3'] = cm3 * 1000.0
                        write_log(f"[postprint] WARNING: Using ESTIMATED usage from header: {cm3}cm³")
                        write_log("[postprint] This assumes the print completed successfully!")
        
        # PRIORITY 2: Parse metadata (material/color/brand) - check both header and footer
        all_lines = footer_lines + header_lines  # Footer first (more recent data)
        
        for line in all_lines:
            # Material/filament type
            if not info['material']:
                match = re.match(r'^\s*;\s*filament_type\s*=\s*(.+)$', line, re.IGNORECASE)
                if match:
                    material = match.group(1).strip(' "\'"')
                    # Handle both comma and semicolon separators (multi-material)
                    if ',' in material:
                        material = material.split(',')[0].strip()
                    elif ';' in material:
                        material = material.split(';')[0].strip()
                    info['material'] = material
            
            # Color
            if not info['color']:
                match = re.match(r'^\s*;\s*filament_colou?r\s*=\s*(.+)$', line, re.IGNORECASE)
                if match:
                    color = match.group(1).strip(' "\'"')
                    # Handle both comma and semicolon separators (multi-material)
                    if ',' in color:
                        color = color.split(',')[0].strip()
                    elif ';' in color:
                        color = color.split(';')[0].strip()
                    info['color'] = color
            
            # Brand/vendor
            if not info['brand']:
                match = re.match(r'^\s*;\s*filament_vendor\s*=\s*(.+)$', line, re.IGNORECASE)
                if match:
                    brand = match.group(1).strip(' "\'"')
                    # Handle both comma and semicolon separators (multi-material)
                    if ',' in brand:
                        brand = brand.split(',')[0].strip()
                    elif ';' in brand:
                        brand = brand.split(';')[0].strip()
                    info['brand'] = brand
            
            # Job name patterns
            if not info['job']:
                job_patterns = [
                    r'^\s*;\s*generated by .+ for (.+)$',
                    r'^\s*;\s*print job\s*[:=]\s*(.+)$',
                    r'^\s*;\s*job\s*[:=]\s*(.+)$',
                    r'^\s*;\s*model\s*[:=]\s*(.+)$',
                    r'^\s*;\s*filename\s*[:=]\s*(.+)$'
                ]
                
                for pattern in job_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        job = match.group(1).strip(' "\'"')
                        job = Path(job).stem  # Remove extension
                        info['job'] = job
                        write_log(f"[postprint] Parsed job name: '{job}'")
                        break
        
        # Fallback: use filename as job name
        if not info['job']:
            info['job'] = gcode_path.stem
            write_log(f"[postprint] Using filename as job name: '{info['job']}'")
    
    except Exception as e:
        write_log(f"[postprint] Warning: Failed to parse G-code: {e}")
    
    return info


def resolve_grams(used_g: Optional[float], used_mm3: Optional[float], 
                  density: Optional[float], material: Optional[str]) -> float:
    """Calculate grams from volume and density if needed"""
    if used_g and used_g > 0:
        return round(used_g, 2)
    
    if used_mm3 and used_mm3 > 0:
        # Default densities by material (g/cm³)
        density_map = {
            'pla': 1.24,
            'petg': 1.27,
            'abs': 1.04,
            'tpu': 1.20,
            'asa': 1.07,
            'nylon': 1.15
        }
        
        resolved_density = density
        if not resolved_density or resolved_density <= 0:
            if material:
                resolved_density = density_map.get(material.lower(), 1.24)
            else:
                resolved_density = 1.24  # Default to PLA
        
        # mm³ -> cm³: divide by 1000, then grams = density × volume_cm³
        return round((used_mm3 / 1000.0) * resolved_density, 2)
    
    raise ValueError("Either used_g or used_mm3 must be provided")


def find_actual_gcode(metadata_path: Path) -> Optional[Path]:
    """
    Try to find the actual G-code file when slicer passes a metadata file.
    Anycubic Slicer may pass .gcode.pp metadata instead of .gcode file.
    """
    write_log(f"[postprint] Searching for actual G-code file near: {metadata_path}")
    
    # Try removing .pp extension
    if str(metadata_path).endswith('.gcode.pp'):
        actual_gcode = Path(str(metadata_path)[:-3])  # Remove '.pp'
        if actual_gcode.exists():
            write_log(f"[postprint] Found actual G-code: {actual_gcode}")
            return actual_gcode
    
    # Try parent directory for .gcode files
    parent = metadata_path.parent
    if parent.exists():
        for gcode in parent.glob('*.gcode'):
            if gcode != metadata_path:
                write_log(f"[postprint] Found G-code in parent dir: {gcode}")
                return gcode
    
    # Try grandparent (go up from Metadata folder)
    if parent.name == 'Metadata' and parent.parent.exists():
        for gcode in parent.parent.glob('*.gcode'):
            write_log(f"[postprint] Found G-code in grandparent dir: {gcode}")
            return gcode
    
    write_log("[postprint] Could not find actual G-code file")
    return None


def find_recent_gcode() -> Optional[Path]:
    """Find the most recently modified G-code file in common slicer temp directories"""
    search_paths = [
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Temp' / 'anycubicslicer_model',
        Path(os.environ.get('TEMP', '')) / 'anycubicslicer_model',
        Path(os.environ.get('TMP', '')) / 'anycubicslicer_model',
    ]
    
    recent_gcode = None
    recent_time = 0
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        write_log(f"[postprint] Searching for G-code in: {search_path}")
        
        # Find all .gcode files (not .gcode.pp metadata files)
        try:
            for gcode_file in search_path.rglob('*.gcode'):
                # Skip metadata files
                if str(gcode_file).endswith('.gcode.pp'):
                    continue
                
                mtime = gcode_file.stat().st_mtime
                if mtime > recent_time:
                    recent_time = mtime
                    recent_gcode = gcode_file
        except Exception as e:
            write_log(f"[postprint] Warning: Error searching {search_path}: {e}")
            continue
    
    if recent_gcode:
        age_seconds = time.time() - recent_time
        write_log(f"[postprint] Found recent G-code: {recent_gcode} (modified {age_seconds:.0f}s ago)")
        
        # Only use files modified in the last 5 minutes
        if age_seconds > 300:
            write_log(f"[postprint] WARNING: File is too old ({age_seconds:.0f}s), ignoring")
            return None
    
    return recent_gcode


def main():
    """Main entry point"""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description='Post-print filament usage tracker for 3D Filament Inventory Management'
    )
    parser.add_argument('gcode', nargs='?', help='Path to G-code file')
    parser.add_argument('--used-g', type=float, help='Grams of filament used')
    parser.add_argument('--used-mm3', type=float, help='Cubic millimeters of filament used')
    parser.add_argument('--density', type=float, help='Filament density in g/cm³')
    parser.add_argument('--material', help='Filament material type (PLA, PETG, etc.)')
    parser.add_argument('--color', help='Filament color')
    parser.add_argument('--brand', help='Filament brand/vendor')
    parser.add_argument('--job', help='Print job name')
    
    args = parser.parse_args()
    
    # Parse G-code if provided or find recent one
    gcode_info = {}
    gcode_path = None
    
    if args.gcode:
        gcode_path = Path(args.gcode)
        
        # If the file doesn't exist or is a metadata file, try to find actual G-code
        if not gcode_path.exists() or str(gcode_path).endswith('.gcode.pp'):
            write_log(f"[postprint] Received metadata/missing file: {gcode_path}")
            actual_gcode = find_actual_gcode(gcode_path)
            if actual_gcode:
                gcode_path = actual_gcode
            else:
                write_log("[postprint] WARNING: Could not find actual G-code file")
                gcode_path = None
    else:
        # No G-code provided, try to find recent one
        write_log("[postprint] No G-code file provided, searching for recent files...")
        gcode_path = find_recent_gcode()
        if not gcode_path:
            write_log("[postprint] ERROR: No G-code file found")
            write_log("[postprint] Either provide a G-code file path or use command-line arguments")
            sys.exit(1)
    
    if gcode_path and gcode_path.exists():
        gcode_info = parse_gcode(gcode_path)
    
    # Merge command-line args with G-code info (args take precedence)
    used_g = args.used_g or gcode_info.get('used_g')
    used_mm3 = args.used_mm3 or gcode_info.get('used_mm3')
    material = args.material or gcode_info.get('material')
    color = args.color or gcode_info.get('color')
    brand = args.brand or gcode_info.get('brand')
    job = args.job or gcode_info.get('job') or 'Unknown Print'
    density = args.density
    
    # Calculate grams
    try:
        grams = resolve_grams(used_g, used_mm3, density, material)
    except ValueError as e:
        write_log(f"[postprint] ERROR: {e}")
        sys.exit(1)
    
    # Store originals for logging
    original_brand = brand
    original_color = color
    original_material = material
    
    # Map names
    brand = map_brand_name(brand)
    color = map_color_name(color)
    
    # Map PLA variants
    if material and re.match(r'^PLA\s+(Basic|Plus|Hyper\s*Speed|Pro|Standard|Premium)', material, re.IGNORECASE):
        match = re.match(r'^PLA\s+(.+)', material, re.IGNORECASE)
        variant = match.group(1) if match else ''
        write_log(f"[postprint] Mapped material '{material}' -> 'PLA' (variant: {variant})")
        material = 'PLA'
    
    write_log(f"[postprint] Looking up filament for material='{material}' color='{color}' brand='{brand}' grams={grams}")
    write_log(f"[postprint] Original values: material='{original_material}' brand='{original_brand}' color='{original_color}'")
    write_log(f"[postprint] From: used_g={used_g}, used_mm3={used_mm3}, density={density}")
    
    # Find matching filament
    response = find_filament(material, color, brand)
    if not response or not response.get('matches'):
        write_log("[postprint] WARNING: No matching filament found in inventory.")
        write_log(f"[postprint] Tried: exact match, fuzzy (material+color), and material-only for '{material}'")
        write_log(f"[postprint] Suggestion: Check your inventory has filaments with material '{material}'")
        sys.exit(0)
    
    filament = response['matches'][0]
    write_log(f"[postprint] Using filament: {filament['brand']} {filament['color']} ({filament['material']}) -> id={filament['id']}")
    
    # Update usage
    result = use_filament(filament['id'], grams, job)
    if result and result.get('filament'):
        write_log(f"[postprint] Updated: used {grams}g, remaining {result['filament']['remainingWeight']}g")
    else:
        write_log(f"[postprint] Updated: used {grams}g")


if __name__ == '__main__':
    main()
