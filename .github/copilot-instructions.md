# GitHub Copilot Instructions - 3D Filament Inventory Management

## Project Overview
**Stack**: Pure Python (Flask API + Streamlit Dashboard)
- Flask REST API on port 5000
- Streamlit Dashboard on port 8501
- JSON file persistence (data/filaments.json)
- Post-print auto-deduction script with G-code parsing
- No Node.js/Express - ALL PYTHON

## Architecture

### Core Files
- `app.py` - Flask REST API (9+ endpoints for filament CRUD)
- `dashboard.py` - Streamlit interactive UI (13+ sort options, filtering)
- `tools/postprint_usage.py` - Auto-deduction after 3D print (751 lines, G-code parser)
- `tools/test_postprint.py` - Unit tests for post-print script
- `data/filaments.json` - Inventory data store (15+ filament records)

### Data Model
```python
{
  "id": "timestamp_ms",
  "brand": "string",
  "material": "PLA|ABS|PETG|etc",
  "color": "string",
  "weight": 1000,
  "remainingWeight": 850,
  "diameter": 1.75,
  "cost": 19.95,
  "purchaseDate": "2025-10-18",
  "lastUsed": "2025-10-18T12:34:56",
  "printHistory": [{date, usage_g, job_name}],
  "archived": false
}
```

## API Endpoints
- `GET /api/filaments` - List all active filaments
- `POST /api/filaments` - Add new filament
- `PUT /api/filaments/<id>` - Update filament
- `DELETE /api/filaments/<id>` - Remove filament
- `POST /api/filaments/<id>/use` - Deduct usage (weight in grams)
- `GET /api/filaments/search?material=PLA&brand=Anycubic&color=Black` - Search
- All endpoints return JSON, persist to data/filaments.json

## Key Features Implemented

### Hex Color Detection (ENHANCED)
- G-code sends hex color codes from slicer
- Algorithm detects: grayscale check → brightness analysis → multi-color fallback
- Prevents wrong filament matching on multi-color prints
- Conservative thresholds: brightness < 50 = skip naming

### Post-Print Auto-Deduction
- Parses G-code file (prioritizes FOOTER for actual usage)
- Extracts: material, color, brand, weight used
- Matches to inventory with fuzzy scoring (exact +100, multi-color similarity %, brand +30)
- Auto-archives when weight <= 0
- Logging available via `FILAMENT_POSTPRINT_LOG=1` env var

### Dashboard Features
- 13 sort options (recently used, most used, low stock first, by brand, cost, etc.)
- Filtering by material, brand, color, search term
- Low-stock alerts (< 20%)
- Material distribution pie chart
- Stock level bar chart
- CRUD operations for filaments
- Archive/restore/delete buttons
- Add new filament form with validation

## Code Standards

### Type Hints (40+ added)
```python
# Always use type hints
from typing import Any, Dict, List, Optional, Tuple

def load_filaments() -> List[Dict[str, Any]]:
    """Load filaments from JSON file"""

def filter_filaments(
    all_filaments: List[Dict[str, Any]],
    search_query: str
) -> List[Dict[str, Any]]:
    """Filter filaments based on criteria"""
```

### Docstrings
```python
def remaining_ratio(filament: Dict[str, Any]) -> float:
    """Return remaining weight ratio between 0 and 1."""
```

### Configuration Files
- `pyrightconfig.json` - Type checking (exclude test/doc files)
- `.vscode/settings.json` - Editor settings (rulers 88, 100)
- `.vscode/launch.json` - 3 debug configs (Flask, Streamlit, Tests)
- `.vscode/extensions.json` - Recommended: Python, Pylance, Ruff, Copilot

## Common Tasks

### Run Flask API
```bash
python app.py
# http://localhost:5000/api/filaments
```

### Run Streamlit Dashboard
```bash
streamlit run dashboard.py
# http://localhost:8501
```

### Run Tests
```bash
python -m pytest tools/test_postprint.py -v
# Expected: 18/18 passing
```

### Test Post-Print Script
```bash
# Enable logging
export FILAMENT_POSTPRINT_LOG=1

# Run with G-code file
python tools/postprint_usage.py /path/to/print.gcode http://localhost:5000

# View logs
cat ~/.filament-inventory/postprint.log
```

## Git Workflow
- Main branch: production-ready code
- All changes: typed, tested, documented
- Commits include: 6 recent improvements (cleanup, type checking, config)
- GitHub: https://github.com/Yoothas/3d-filament-inventory-management-home

## Important Notes

### Hex Color Algorithm
Don't modify without testing! Multi-color filament matching depends on this.
- Location: `tools/postprint_usage.py` lines 102-165
- Test with: `python HEX_COLOR_DETECTION_TEST.py`

### JSON Persistence
- No database; all data in `data/filaments.json`
- Auto-creates if missing
- Keep backups before major changes
- Print history limited to last 10 per spool

### Environment Variables
- `FILAMENT_POSTPRINT_LOG=1` - Enable post-print logging
- `FILAMENT_POSTPRINT_LOG=/custom/path.log` - Custom log path
- Logs show: hex detection, color matching, API calls, deductions

## When Adding Features

1. **Add API endpoint**: Create function in `app.py`, test with curl
2. **Add dashboard feature**: Create Streamlit widget in `dashboard.py`
3. **Modify data model**: Update docstring in `app.py` for schema
4. **Add type hints**: Always use `Dict[str, Any]`, `List[...]`, `Optional[...]`
5. **Test thoroughly**: Run tests, manual testing, check logs
6. **Document changes**: Update this file and create/update .md docs

## Debugging

### Flask API issues
```bash
# Check if running
curl http://localhost:5000/api/filaments

# Check logs
tail -f ~/.filament-inventory/postprint.log
```

### Streamlit issues
```bash
# Restart with --logger.level=debug
streamlit run dashboard.py --logger.level=debug
```

### Type checking errors
```bash
# Check errors
python -m pylance check .

# All errors should be 0 in production files
```

## Project Status
✅ **Production Ready**
- 18/18 tests passing
- 0 type checking errors (in production code)
- All features working
- Comprehensive documentation
- GitHub synced (latest commit 5f22c7c)
