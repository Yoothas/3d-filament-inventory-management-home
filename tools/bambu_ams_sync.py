#!/usr/bin/env python3
"""
Bambu AMS Filament Sync Script
Syncs filament data from Bambu Lab printer's AMS system to the local inventory.

Usage:
    python bambu_ams_sync.py <printer_ip> [--access-code CODE] [--port PORT]

Example:
    python bambu_ams_sync.py 192.168.1.100 --access-code 12345678
    
Features:
    - Reads AMS filament data from Bambu printer via local API
    - Matches AMS spools to inventory by material, color, and brand
    - Updates remaining weight in inventory
    - Logs all sync operations
    - Dry-run mode for testing without making changes
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests module not found. Install with: pip install requests")
    sys.exit(1)


# Configuration
DEFAULT_PORT = 5000  # Flask API port
_log_path: Optional[Path] = None


def setup_logging():
    """Initialize logging"""
    global _log_path
    base = Path.home() / '.filament-inventory'
    base.mkdir(exist_ok=True)
    _log_path = base / 'bambu_sync.log'


def write_log(message: str):
    """Write log message to console and file"""
    print(message)
    if _log_path:
        try:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            with open(_log_path, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass


def get_auth_headers() -> Dict[str, str]:
    """Build auth headers if FILAMENT_API_KEY is set."""
    api_key = os.environ.get('FILAMENT_API_KEY', '')
    if api_key:
        return {'X-API-Key': api_key}
    return {}


def fetch_inventory_filaments(flask_url: str) -> List[Dict[str, Any]]:
    """Fetch current inventory from Flask API"""
    try:
        response = requests.get(f"{flask_url}/api/filaments", timeout=5, headers=get_auth_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        write_log(f"[bambu_sync] ERROR: Failed to fetch inventory: {e}")
        return []


def match_ams_to_inventory(
    ams_spool: Dict[str, Any],
    inventory: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Match an AMS spool to inventory filament.
    
    Args:
        ams_spool: AMS spool data (material, color, brand, remaining_weight)
        inventory: List of inventory filaments
        
    Returns:
        Matching inventory filament or None
    """
    material = ams_spool.get('material', '').upper()
    color = ams_spool.get('color', '').lower()
    brand = ams_spool.get('brand', '').lower()
    
    write_log(f"[bambu_sync] Matching AMS spool: {brand} {color} {material}")
    
    # Try exact match first
    for filament in inventory:
        inv_material = filament.get('material', '').upper()
        inv_color = filament.get('color', '').lower()
        inv_brand = filament.get('brand', '').lower()
        
        if (inv_material == material and 
            inv_color == color and 
            brand in inv_brand):
            write_log(f"[bambu_sync] EXACT MATCH: {filament.get('brand')} {filament.get('color')} -> ID {filament.get('id')}")
            return filament
    
    # Try material + color match
    for filament in inventory:
        inv_material = filament.get('material', '').upper()
        inv_color = filament.get('color', '').lower()
        
        if inv_material == material and inv_color == color:
            write_log(f"[bambu_sync] PARTIAL MATCH (material+color): {filament.get('brand')} {filament.get('color')} -> ID {filament.get('id')}")
            return filament
    
    write_log(f"[bambu_sync] NO MATCH FOUND for {brand} {color} {material}")
    return None


def update_inventory_weight(
    flask_url: str,
    filament_id: str,
    new_weight: float,
    dry_run: bool = False
) -> bool:
    """
    Update inventory filament weight.
    
    Args:
        flask_url: Flask API base URL
        filament_id: Filament ID to update
        new_weight: New remaining weight in grams
        dry_run: If True, don't actually update, just log
        
    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        write_log(f"[bambu_sync] DRY-RUN: Would update filament {filament_id} to {new_weight}g")
        return True
    
    try:
        url = f"{flask_url}/api/filaments/{filament_id}"
        payload = {'remainingWeight': new_weight}
        response = requests.put(url, json=payload, timeout=5, headers=get_auth_headers())
        response.raise_for_status()
        write_log(f"[bambu_sync] ✓ Updated filament {filament_id} to {new_weight}g")
        return True
    except Exception as e:
        write_log(f"[bambu_sync] ERROR: Failed to update filament {filament_id}: {e}")
        return False


def manual_sync_from_json(json_file: Path, flask_url: str, dry_run: bool = False):
    """
    Sync from manually created JSON file with AMS data.
    
    Expected JSON format:
    {
        "ams_slots": [
            {
                "slot": 1,
                "material": "PLA",
                "color": "Black",
                "brand": "Bambu Lab",
                "remaining_weight": 850.5,
                "notes": "AMS Slot 1"
            },
            ...
        ]
    }
    """
    write_log(f"[bambu_sync] Loading manual AMS data from {json_file}...")
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        write_log(f"[bambu_sync] ERROR: Failed to read JSON file: {e}")
        return
    
    ams_slots = data.get('ams_slots', [])
    if not ams_slots:
        write_log("[bambu_sync] ERROR: No AMS slots found in JSON file")
        return
    
    write_log(f"[bambu_sync] Found {len(ams_slots)} AMS slots to sync")
    
    # Fetch current inventory
    inventory = fetch_inventory_filaments(flask_url)
    if not inventory:
        write_log("[bambu_sync] ERROR: Could not fetch inventory")
        return
    
    write_log(f"[bambu_sync] Current inventory has {len(inventory)} filaments")
    
    # Process each AMS slot
    success_count = 0
    for ams_spool in ams_slots:
        slot = ams_spool.get('slot', '?')
        remaining = ams_spool.get('remaining_weight', 0)
        
        write_log(f"\n[bambu_sync] ----- AMS Slot {slot} -----")
        
        # Match to inventory
        match = match_ams_to_inventory(ams_spool, inventory)
        
        if match:
            filament_id = match['id']
            current_weight = match.get('remainingWeight', 0)
            
            write_log(f"[bambu_sync] Current inventory weight: {current_weight}g")
            write_log(f"[bambu_sync] AMS reported weight: {remaining}g")
            write_log(f"[bambu_sync] Difference: {remaining - current_weight:+.2f}g")
            
            # Update inventory
            if update_inventory_weight(flask_url, filament_id, remaining, dry_run):
                success_count += 1
        else:
            write_log("[bambu_sync] ⚠ Skipping - no inventory match found")
    
    write_log("\n[bambu_sync] ===== SYNC COMPLETE =====")
    write_log(f"[bambu_sync] Successfully synced: {success_count}/{len(ams_slots)} spools")
    
    if dry_run:
        write_log("[bambu_sync] DRY-RUN MODE - No changes were made")
        write_log("[bambu_sync] Run without --dry-run to apply changes")


def create_sample_json(output_path: Path):
    """Create a sample JSON file for manual AMS data entry"""
    sample_data = {
        "ams_slots": [
            {
                "slot": 1,
                "material": "PLA",
                "color": "Black",
                "brand": "Bambu Lab",
                "remaining_weight": 850.5,
                "notes": "AMS Slot 1 - Bambu Lab Black PLA"
            },
            {
                "slot": 2,
                "material": "PLA",
                "color": "White",
                "brand": "Bambu Lab",
                "remaining_weight": 920.0,
                "notes": "AMS Slot 2 - Bambu Lab White PLA"
            },
            {
                "slot": 3,
                "material": "PLA",
                "color": "Red",
                "brand": "Anycubic",
                "remaining_weight": 500.0,
                "notes": "AMS Slot 3 - Anycubic Red PLA"
            },
            {
                "slot": 4,
                "material": "PLA",
                "color": "Blue",
                "brand": "Generic",
                "remaining_weight": 650.0,
                "notes": "AMS Slot 4 - Generic Blue PLA"
            }
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"✓ Created sample AMS data file: {output_path}")
    print("\nInstructions:")
    print(f"1. Edit {output_path} with your actual AMS spool data")
    print("2. Check your Bambu printer's AMS display for current weights")
    print("3. Update the JSON file with material, color, brand, and remaining_weight")
    print(f"4. Run sync: python bambu_ams_sync.py --manual {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Sync Bambu AMS filament data to local inventory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create sample JSON file for manual data entry
  python bambu_ams_sync.py --create-sample ams_data.json
  
  # Sync from manual JSON file (dry-run first)
  python bambu_ams_sync.py --manual ams_data.json --dry-run
  
  # Sync from manual JSON file (apply changes)
  python bambu_ams_sync.py --manual ams_data.json
  
  # Future: Auto-sync from printer (requires MQTT setup)
  # python bambu_ams_sync.py 192.168.1.100 --access-code 12345678
        """
    )
    
    parser.add_argument(
        'printer_ip',
        nargs='?',
        help='IP address of Bambu printer (for future auto-sync)'
    )
    parser.add_argument(
        '--access-code',
        help='8-digit access code from printer screen (for future auto-sync)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help=f'Flask API port (default: {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--manual',
        type=Path,
        help='Path to manual AMS data JSON file'
    )
    parser.add_argument(
        '--create-sample',
        type=Path,
        help='Create a sample AMS data JSON file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test sync without making changes'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Create sample file
    if args.create_sample:
        create_sample_json(args.create_sample)
        return
    
    # Manual sync mode
    if args.manual:
        if not args.manual.exists():
            print(f"ERROR: File not found: {args.manual}")
            print(f"Create a sample file with: python bambu_ams_sync.py --create-sample {args.manual}")
            sys.exit(1)
        
        flask_url = f"http://localhost:{args.port}"
        write_log("[bambu_sync] ===== BAMBU AMS SYNC START =====")
        write_log("[bambu_sync] Mode: Manual JSON import")
        write_log(f"[bambu_sync] Flask API: {flask_url}")
        
        if args.dry_run:
            write_log("[bambu_sync] DRY-RUN MODE - No changes will be made")
        
        manual_sync_from_json(args.manual, flask_url, args.dry_run)
        return
    
    # Auto-sync mode (future feature)
    if args.printer_ip:
        write_log("[bambu_sync] Auto-sync from printer is not yet implemented.")
        write_log("[bambu_sync] This requires MQTT client setup.")
        write_log("[bambu_sync] For now, use manual sync mode:")
        write_log("[bambu_sync]   1. python bambu_ams_sync.py --create-sample ams_data.json")
        write_log("[bambu_sync]   2. Edit ams_data.json with your AMS spool data")
        write_log("[bambu_sync]   3. python bambu_ams_sync.py --manual ams_data.json")
        sys.exit(1)
    
    # No arguments - show help
    parser.print_help()


if __name__ == '__main__':
    main()
