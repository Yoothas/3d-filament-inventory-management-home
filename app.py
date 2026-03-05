import hmac
import json
import os
import tempfile
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration
PORT = int(os.environ.get('PORT', 5000))  # Default to 5000 (3000 may be restricted on Windows)
API_KEY = os.environ.get('FILAMENT_API_KEY', '')  # Optional API key for mutation endpoints
DATA_DIR = Path(__file__).parent / 'data'
DATA_FILE = DATA_DIR / 'filaments.json'

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Initialize data file if it doesn't exist
if not DATA_FILE.exists():
    with open(DATA_FILE, 'w') as f:
        json.dump([], f, indent=2)


# Helper functions
def require_api_key(f):
    """Decorator that checks X-API-Key header when FILAMENT_API_KEY is set."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if API_KEY:
            provided = request.headers.get('X-API-Key', '')
            if not hmac.compare_digest(provided, API_KEY):
                return jsonify({'error': 'Unauthorized – invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated


def safe_float(value, default=0.0):
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_filaments():
    """Read filaments from JSON file"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f'Error reading filaments: {e}')
        return []


def write_filaments(filaments):
    """Write filaments to JSON file atomically (temp file + rename)."""
    try:
        fd, tmp = tempfile.mkstemp(dir=str(DATA_DIR), suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(filaments, f, indent=2)
            os.replace(tmp, str(DATA_FILE))
        except BaseException:
            os.unlink(tmp)
            raise
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
@require_api_key
def add_filament():
    """Add a new filament"""
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    filaments = read_filaments()
    
    new_filament = {
        'id': uuid.uuid4().hex,
        'brand': data.get('brand'),
        'material': data.get('material'),
        'color': data.get('color'),
        'weight': safe_float(data.get('weight', 0)),
        'remainingWeight': safe_float(data.get('remainingWeight', data.get('weight', 0))),
        'diameter': safe_float(data.get('diameter', 1.75), 1.75),
        'purchaseDate': data.get('purchaseDate', ''),
        'cost': safe_float(data.get('cost', 0)),
        'notes': data.get('notes', ''),
        'createdAt': datetime.now().isoformat()
    }
    
    filaments.append(new_filament)
    
    if write_filaments(filaments):
        return jsonify(new_filament), 201
    else:
        return jsonify({'error': 'Failed to save filament'}), 500


@app.route('/api/filaments/<filament_id>', methods=['PUT'])
@require_api_key
def update_filament(filament_id):
    """Update an existing filament"""
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    filaments = read_filaments()
    
    filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
    
    if filament_index is None:
        return jsonify({'error': 'Filament not found'}), 404
    
    existing = filaments[filament_index]
    updated_filament = {**existing}
    
    # Only update fields that are present in the request body
    if 'brand' in data:
        updated_filament['brand'] = data['brand']
    if 'material' in data:
        updated_filament['material'] = data['material']
    if 'color' in data:
        updated_filament['color'] = data['color']
    if 'weight' in data:
        updated_filament['weight'] = safe_float(data['weight'])
    if 'remainingWeight' in data:
        updated_filament['remainingWeight'] = safe_float(data['remainingWeight'])
    if 'diameter' in data:
        updated_filament['diameter'] = safe_float(data['diameter'], 1.75)
    if 'purchaseDate' in data:
        updated_filament['purchaseDate'] = data['purchaseDate']
    if 'cost' in data:
        updated_filament['cost'] = safe_float(data['cost'])
    if 'notes' in data:
        updated_filament['notes'] = data['notes']
    updated_filament['updatedAt'] = datetime.now().isoformat()
    
    filaments[filament_index] = updated_filament
    
    if write_filaments(filaments):
        return jsonify(updated_filament)
    else:
        return jsonify({'error': 'Failed to update filament'}), 500


@app.route('/api/filaments/<filament_id>', methods=['DELETE'])
@require_api_key
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
@require_api_key
def use_filament(filament_id):
    """Reduce filament usage after print completion"""
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    filaments = read_filaments()
    
    filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
    
    if filament_index is None:
        return jsonify({'error': 'Filament not found'}), 404
    
    used_weight = safe_float(data.get('usedWeight', 0))
    print_job = data.get('printJob', 'Unknown')
    print_time = safe_float(data.get('printTime', 0))
    
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
    filtered = [f for f in filaments if f.get('remainingWeight', 0) > 0 and not f.get('archived', False)]
    
    if material:
        filtered = [f for f in filtered if material in (f.get('material') or '').lower()]
    
    if color:
        filtered = [f for f in filtered if color in (f.get('color') or '').lower()]
    
    if brand:
        filtered = [f for f in filtered if brand in (f.get('brand') or '').lower()]
    
    # Sort by remaining weight (most full first)
    filtered.sort(key=lambda x: x.get('remainingWeight', 0), reverse=True)
    
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
@require_api_key
def bulk_use_filaments():
    """Bulk usage for multi-material prints"""
    usage_data = request.get_json()
    if usage_data is None:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    filaments = read_filaments()
    results = []
    
    if not isinstance(usage_data, list):
        return jsonify({'error': 'Expected array of usage data'}), 400
    
    for usage in usage_data:
        if not isinstance(usage, dict):
            results.append({'error': 'Invalid usage entry'})
            continue
        filament_id = usage.get('id')
        filament_index = next((i for i, f in enumerate(filaments) if f['id'] == filament_id), None)
        
        if filament_index is None:
            results.append({'id': filament_id, 'error': 'Filament not found'})
            continue
        
        used_weight = safe_float(usage.get('usedWeight', 0))
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
        
        updated = {
            **filament,
            'remainingWeight': new_remaining_weight,
            'lastUsed': datetime.now().isoformat(),
            'printHistory': print_history,
            'updatedAt': datetime.now().isoformat()
        }
        
        # Auto-archive if empty
        if new_remaining_weight <= 0:
            updated['archived'] = True
            updated['archivedAt'] = datetime.now().isoformat()
        
        filaments[filament_index] = updated
        
        results.append({
            'id': filament_id,
            'success': True,
            'usedWeight': used_weight,
            'remainingWeight': new_remaining_weight,
            'auto_archived': new_remaining_weight <= 0,
            'filament': f"{filament['brand']} {filament['color']}"
        })
    
    if write_filaments(filaments):
        return jsonify({
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Failed to save filament updates'}), 500


# Archive/History Endpoints

@app.route('/api/filaments/<filament_id>/archive', methods=['POST'])
@require_api_key
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
@require_api_key
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


@app.route('/api/filaments/auto-archive', methods=['POST'])
@require_api_key
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
    debug_mode = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true')
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    print(f'3D Filament Inventory Server running on port {PORT}')
    print('Access the application at:')
    print(f'  Local: http://localhost:{PORT}')
    if host == '0.0.0.0':
        print(f'  Network: http://YOUR_IP_ADDRESS:{PORT}')
    print('\nSet FLASK_HOST=0.0.0.0 to allow network access.')
    app.run(host=host, port=PORT, debug=debug_mode)
