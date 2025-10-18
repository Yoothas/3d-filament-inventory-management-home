from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Configuration
PORT = int(os.environ.get('PORT', 5000))  # Default to 5000 (3000 may be restricted on Windows)
DATA_DIR = Path(__file__).parent / 'data'
DATA_FILE = DATA_DIR / 'filaments.json'

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Initialize data file if it doesn't exist
if not DATA_FILE.exists():
    with open(DATA_FILE, 'w') as f:
        json.dump([], f, indent=2)


# Helper functions
def read_filaments():
    """Read filaments from JSON file"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f'Error reading filaments: {e}')
        return []


def write_filaments(filaments):
    """Write filaments to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(filaments, f, indent=2)
        return True
    except Exception as e:
        print(f'Error writing filaments: {e}')
        return False


# Routes
@app.route('/')
def index():
    """Simple health endpoint for quick checks"""
    return jsonify({
        'status': 'ok',
        'message': '3D Filament Inventory API running',
        'endpoints': {
            'filaments': '/api/filaments',
            'search': '/api/filaments/search',
            'usage': '/api/filaments/<id>/use'
        }
    })


# API Routes
@app.route('/api/filaments', methods=['GET'])
def get_filaments():
    """Get all filaments (active by default, use ?include_archived=true to get all)"""
    filaments = read_filaments()
    
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    
    if not include_archived:
        filaments = [f for f in filaments if not f.get('archived', False)]
    
    return jsonify(filaments)


@app.route('/api/filaments', methods=['POST'])
def add_filament():
    """Add a new filament"""
    data = request.get_json()
    filaments = read_filaments()
    
    new_filament = {
        'id': str(int(datetime.now().timestamp() * 1000)),
        'brand': data.get('brand'),
        'material': data.get('material'),
        'color': data.get('color'),
        'weight': float(data.get('weight', 0)),
        'remainingWeight': float(data.get('remainingWeight', data.get('weight', 0))),
        'diameter': float(data.get('diameter', 1.75)),
        'purchaseDate': data.get('purchaseDate', ''),
        'cost': float(data.get('cost', 0)),
        'notes': data.get('notes', ''),
        'createdAt': datetime.now().isoformat()
    }
    
    filaments.append(new_filament)
    
    if write_filaments(filaments):
        return jsonify(new_filament), 201
    else:
        return jsonify({'error': 'Failed to save filament'}), 500


@app.route('/api/filaments/<filament_id>', methods=['PUT'])
def update_filament(filament_id):
    """Update an existing filament"""
    data = request.get_json()
    filaments = read_filaments()
    
    filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
    
    if filament_index is None:
        return jsonify({'error': 'Filament not found'}), 404
    
    updated_filament = {
        **filaments[filament_index],
        'brand': data.get('brand'),
        'material': data.get('material'),
        'color': data.get('color'),
        'weight': float(data.get('weight', 0)),
        'remainingWeight': float(data.get('remainingWeight', 0)),
        'diameter': float(data.get('diameter', 1.75)),
        'purchaseDate': data.get('purchaseDate', ''),
        'cost': float(data.get('cost', 0)),
        'notes': data.get('notes', ''),
        'updatedAt': datetime.now().isoformat()
    }
    
    filaments[filament_index] = updated_filament
    
    if write_filaments(filaments):
        return jsonify(updated_filament)
    else:
        return jsonify({'error': 'Failed to update filament'}), 500


@app.route('/api/filaments/<filament_id>', methods=['DELETE'])
def delete_filament(filament_id):
    """Delete a filament"""
    filaments = read_filaments()
    
    filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
    
    if filament_index is None:
        return jsonify({'error': 'Filament not found'}), 404
    
    filaments.pop(filament_index)
    
    if write_filaments(filaments):
        return jsonify({'message': 'Filament deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete filament'}), 500


# AMS Integration API Endpoints

@app.route('/api/filaments/<filament_id>/use', methods=['POST'])
def use_filament(filament_id):
    """Reduce filament usage after print completion"""
    data = request.get_json()
    filaments = read_filaments()
    
    filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
    
    if filament_index is None:
        return jsonify({'error': 'Filament not found'}), 404
    
    used_weight = float(data.get('usedWeight', 0))
    print_job = data.get('printJob', 'Unknown')
    print_time = data.get('printTime', 0)
    
    if used_weight <= 0:
        return jsonify({'error': 'Invalid used weight'}), 400
    
    filament = filaments[filament_index]
    new_remaining_weight = max(0, filament['remainingWeight'] - used_weight)
    
    # Get existing print history or initialize empty list
    print_history = filament.get('printHistory', [])
    
    # Add new print record
    print_history.append({
        'date': datetime.now().isoformat(),
        'usedWeight': used_weight,
        'printJob': print_job,
        'printTime': print_time,
        'remainingAfter': new_remaining_weight
    })
    
    # Keep last 10 print jobs
    print_history = print_history[-10:]
    
    # Update filament
    updated_filament = {
        **filament,
        'remainingWeight': new_remaining_weight,
        'lastUsed': datetime.now().isoformat(),
        'printHistory': print_history,
        'updatedAt': datetime.now().isoformat()
    }
    
    # Auto-archive if empty
    if new_remaining_weight <= 0:
        updated_filament['archived'] = True
        updated_filament['archivedAt'] = datetime.now().isoformat()
    
    filaments[filament_index] = updated_filament
    
    message = f"Used {used_weight}g of {filament['brand']} {filament['color']}. {new_remaining_weight}g remaining."
    if new_remaining_weight <= 0:
        message += " Spool empty - automatically archived."
    
    if write_filaments(filaments):
        return jsonify({
            'success': True,
            'filament': updated_filament,
            'message': message,
            'auto_archived': new_remaining_weight <= 0
        })
    else:
        return jsonify({'error': 'Failed to update filament usage'}), 500


@app.route('/api/filaments/search', methods=['GET'])
def search_filaments():
    """Search filaments for AMS auto-detection"""
    filaments = read_filaments()
    
    material = request.args.get('material', '').lower()
    color = request.args.get('color', '').lower()
    brand = request.args.get('brand', '').lower()
    ams_slot = request.args.get('ams_slot', '')
    
    # Only available spools (active and with remaining weight)
    filtered = [f for f in filaments if f['remainingWeight'] > 0 and not f.get('archived', False)]
    
    if material:
        filtered = [f for f in filtered if material in f['material'].lower()]
    
    if color:
        filtered = [f for f in filtered if color in f['color'].lower()]
    
    if brand:
        filtered = [f for f in filtered if brand in f['brand'].lower()]
    
    # Sort by remaining weight (most full first)
    filtered.sort(key=lambda x: x['remainingWeight'], reverse=True)
    
    return jsonify({
        'matches': filtered,
        'count': len(filtered),
        'query': {
            'material': material,
            'color': color,
            'brand': brand,
            'ams_slot': ams_slot
        }
    })


@app.route('/api/filaments/bulk-use', methods=['POST'])
def bulk_use_filaments():
    """Bulk usage for multi-material prints"""
    usage_data = request.get_json()
    filaments = read_filaments()
    results = []
    
    if not isinstance(usage_data, list):
        return jsonify({'error': 'Expected array of usage data'}), 400
    
    for usage in usage_data:
        filament_id = usage.get('id')
        filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
        
        if filament_index is None:
            results.append({'id': filament_id, 'error': 'Filament not found'})
            continue
        
        used_weight = float(usage.get('usedWeight', 0))
        if used_weight <= 0:
            results.append({'id': filament_id, 'error': 'Invalid used weight'})
            continue
        
        filament = filaments[filament_index]
        new_remaining_weight = max(0, filament['remainingWeight'] - used_weight)
        
        # Get existing print history or initialize empty list
        print_history = filament.get('printHistory', [])
        
        # Add new print record
        print_history.append({
            'date': datetime.now().isoformat(),
            'usedWeight': used_weight,
            'printJob': usage.get('printJob', 'Multi-material print'),
            'printTime': usage.get('printTime', 0),
            'remainingAfter': new_remaining_weight
        })
        
        # Keep last 10 print jobs
        print_history = print_history[-10:]
        
        filaments[filament_index] = {
            **filament,
            'remainingWeight': new_remaining_weight,
            'lastUsed': datetime.now().isoformat(),
            'printHistory': print_history
        }
        
        results.append({
            'id': filament_id,
            'success': True,
            'usedWeight': used_weight,
            'remainingWeight': new_remaining_weight,
            'filament': f"{filament['brand']} {filament['color']}"
        })
    
    if write_filaments(filaments):
        return jsonify({
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Failed to save filament updates'}), 500


@app.route('/api/ams/status', methods=['GET'])
def ams_status():
    """AMS status endpoint for mapping physical slots to inventory"""
    ams_slots = {
        'slot_1': {'filament_id': None, 'material': None, 'color': None},
        'slot_2': {'filament_id': None, 'material': None, 'color': None},
        'slot_3': {'filament_id': None, 'material': None, 'color': None},
        'slot_4': {'filament_id': None, 'material': None, 'color': None}
    }
    
    return jsonify({
        'ams_slots': ams_slots,
        'message': 'AMS integration ready - map filaments to slots in your slicer'
    })


# Archive/History Endpoints

@app.route('/api/filaments/<filament_id>/archive', methods=['POST'])
def archive_filament(filament_id):
    """Archive a filament spool (marks as used up, keeps history)"""
    filaments = read_filaments()
    
    filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
    
    if filament_index is None:
        return jsonify({'error': 'Filament not found'}), 404
    
    filament = filaments[filament_index]
    
    # Mark as archived
    updated_filament = {
        **filament,
        'archived': True,
        'archivedAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat()
    }
    
    filaments[filament_index] = updated_filament
    
    if write_filaments(filaments):
        return jsonify({
            'success': True,
            'filament': updated_filament,
            'message': f"Archived {filament['brand']} {filament['color']} {filament['material']}"
        })
    else:
        return jsonify({'error': 'Failed to archive filament'}), 500


@app.route('/api/filaments/<filament_id>/unarchive', methods=['POST'])
def unarchive_filament(filament_id):
    """Restore an archived filament"""
    filaments = read_filaments()
    
    filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
    
    if filament_index is None:
        return jsonify({'error': 'Filament not found'}), 404
    
    filament = filaments[filament_index]
    
    # Remove archive status
    updated_filament = {
        **filament,
        'archived': False,
        'updatedAt': datetime.now().isoformat()
    }
    
    # Remove archivedAt if it exists
    if 'archivedAt' in updated_filament:
        del updated_filament['archivedAt']
    
    filaments[filament_index] = updated_filament
    
    if write_filaments(filaments):
        return jsonify({
            'success': True,
            'filament': updated_filament,
            'message': f"Restored {filament['brand']} {filament['color']} {filament['material']}"
        })
    else:
        return jsonify({'error': 'Failed to unarchive filament'}), 500


@app.route('/api/filaments/archived', methods=['GET'])
def get_archived_filaments():
    """Get all archived filaments"""
    filaments = read_filaments()
    archived = [f for f in filaments if f.get('archived', False)]
    
    return jsonify({
        'filaments': archived,
        'count': len(archived)
    })


@app.route('/api/filaments/active', methods=['GET'])
def get_active_filaments():
    """Get all active (non-archived) filaments"""
    filaments = read_filaments()
    active = [f for f in filaments if not f.get('archived', False)]
    
    return jsonify({
        'filaments': active,
        'count': len(active)
    })


@app.route('/api/filaments/auto-archive', methods=['POST'])
def auto_archive_empty():
    """Automatically archive all empty spools (0g remaining)"""
    filaments = read_filaments()
    archived_count = 0
    archived_list = []
    
    for i, filament in enumerate(filaments):
        if filament['remainingWeight'] <= 0 and not filament.get('archived', False):
            filaments[i] = {
                **filament,
                'archived': True,
                'archivedAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            }
            archived_count += 1
            archived_list.append(f"{filament['brand']} {filament['color']}")
    
    if archived_count > 0:
        if write_filaments(filaments):
            return jsonify({
                'success': True,
                'archived_count': archived_count,
                'archived_spools': archived_list,
                'message': f"Archived {archived_count} empty spool(s)"
            })
        else:
            return jsonify({'error': 'Failed to archive empty spools'}), 500
    else:
        return jsonify({
            'success': True,
            'archived_count': 0,
            'message': 'No empty spools to archive'
        })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print(f'3D Filament Inventory Server running on port {PORT}')
    print(f'Access the application at:')
    print(f'  Local: http://localhost:{PORT}')
    print(f'  Network: http://YOUR_IP_ADDRESS:{PORT}')
    print(f'\nShare the Network URL to access from any browser!')
    
    app.run(host='0.0.0.0', port=PORT, debug=True)
