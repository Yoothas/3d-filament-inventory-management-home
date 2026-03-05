# 3D Filament Inventory Management

A local-first, **100% Python** inventory system for tracking 3D printing filament spools with automatic post-print deduction and Bambu AMS sync support.

## Quick Start

**Prerequisites:** Python 3.10+, pip

```powershell
# Install dependencies
pip install -r requirements.txt

# Launch both Flask API + Streamlit Dashboard
python start.py

# (Optional) Launch with API key protection
$env:FILAMENT_API_KEY = 'your-secret-key'
python start.py
```

- **API:** http://localhost:5000
- **Dashboard:** http://localhost:8501

Press **Ctrl+C** to stop both services.

You can also start them individually:

```powershell
python start.py --api-only    # Flask API only
python start.py --dash-only   # Dashboard only
```

The dashboard talks to the Flask API — **start the API first** (or use `start.py` which handles the order automatically).

---

## Features

- **Filament Tracking** — Brand, material, color, weight, cost, purchase date, notes
- **Visual Dashboard** — Progress bars, Plotly pie/bar charts, 13+ sort options
- **Smart Search & Filtering** — By material, brand, color, or free-text
- **Slicer Integration** — Automatic filament deduction from G-code after prints
- **Multi-Spool Prints** — Detects multi-material G-code and deducts from each spool individually
- **Bambu AMS Sync** — Manual JSON import to sync AMS slot weights to inventory
- **Archive System** — Auto-archives empty spools, preserves full print history
- **API Key Auth** — Optional `FILAMENT_API_KEY` protects mutation endpoints
- **Smart Matching** — Fuzzy brand/color/material matching with scoring system

---

## Two Interfaces

| | Flask API (port 5000) | Streamlit Dashboard (port 8501) |
|---|---|---|
| **Use for** | Automation, REST clients, integrations | Visual management, charts, manual edits |
| **Access** | JSON responses | Interactive browser UI |
| **Network** | Multi-user accessible | Multi-user accessible |

Both read/write the same `data/filaments.json`.

---

## API Endpoints

**Filament CRUD:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/filaments` | List active filaments (`?include_archived=true` for all) |
| `POST` | `/api/filaments` | Add new filament |
| `PUT` | `/api/filaments/:id` | Update filament (partial merge) |
| `DELETE` | `/api/filaments/:id` | Delete filament |

**Usage & Search:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/filaments/:id/use` | Deduct usage (auto-archives at 0g) |
| `POST` | `/api/filaments/bulk-use` | Multi-filament usage in one call |
| `GET` | `/api/filaments/search` | Search by `?material=`, `?color=`, `?brand=` |

**Archive:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/filaments/:id/archive` | Archive a spool |
| `POST` | `/api/filaments/:id/unarchive` | Restore archived spool |
| `POST` | `/api/filaments/auto-archive` | Archive all empty spools |

**Authentication:** Set `FILAMENT_API_KEY` env var to require `X-API-Key` header on all mutation endpoints (POST/PUT/DELETE). GET endpoints remain open.

---

## Slicer Integration (Auto-Deduct)

The post-print script parses G-code metadata and automatically deducts filament usage from inventory.

### Setup

1. **Start Flask server:** `python app.py`
2. **Run the setup script:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\setup-slicer-wrapper.ps1
   ```
3. **Configure your slicer:** Add the wrapper path to your slicer's post-processing command:
   ```
   C:\3DPrint\slicer-postprint.bat "{output_filepath}"
   ```

### How It Works

1. Slicer finishes slicing → calls the wrapper script
2. Script parses the G-code footer for **actual** usage (falls back to header estimates)
3. Extracts material, color, brand, weight from G-code comments
4. Matches to inventory using fuzzy scoring (exact color +100, brand +30, recent use +20)
5. Deducts weight via Flask API, auto-archives at 0g

### Multi-Spool Prints

Multi-material prints are automatically detected from comma-separated G-code values:
```
; filament used [g] = 300.04, 14.22
; filament_colour = #212721, #FF0000
```
Each filament is matched and deducted individually.

### Troubleshooting

- **No inventory update:** Ensure Flask server is running on port 5000
- **No matching filament:** Verify material/color/brand exists in inventory
- **Enable logging:** `$env:FILAMENT_POSTPRINT_LOG=1` then check `~/.filament-inventory/postprint.log`

---

## Bambu AMS Sync

Manually sync AMS spool weights from your Bambu printer to inventory.

### Usage

```powershell
# 1. Create a sample JSON file
python tools\bambu_ams_sync.py --create-sample data\my_ams_data.json

# 2. Edit it with your actual AMS weights (check printer screen or Bambu Studio)

# 3. Test first (dry-run)
python tools\bambu_ams_sync.py --manual data\my_ams_data.json --dry-run

# 4. Apply
python tools\bambu_ams_sync.py --manual data\my_ams_data.json
```

### JSON Format

```json
{
  "ams_slots": [
    {
      "slot": 1,
      "material": "PLA",
      "color": "Black",
      "brand": "Anycubic",
      "remaining_weight": 850.5
    }
  ]
}
```

### Quick Sync Scripts

Use the helper scripts for convenience:
- **PowerShell:** `tools\bambu_quick_sync.ps1 [-DryRun]`
- **Batch:** `tools\bambu_quick_sync.bat`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Flask API port |
| `FLASK_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for network access) |
| `FLASK_DEBUG` | `0` | Enable Flask debug mode (`1` or `true`) |
| `FILAMENT_API_KEY` | *(none)* | API key for mutation endpoint auth |
| `FILAMENT_API_URL` | `http://localhost:5000` | Dashboard → API base URL |
| `FILAMENT_POSTPRINT_LOG` | *(none)* | `1` for default log, or path for custom log |
| `FILAMENT_SERVER_PORT` | `5000` | Post-print script server port |
| `FILAMENT_SERVER_HOST` | `http://localhost:5000` | Post-print script server URL |

---

## Project Structure

```
├── app.py                          # Flask REST API
├── dashboard.py                    # Streamlit Dashboard
├── start.py                        # Unified launcher (both services)
├── requirements.txt                # Python dependencies
├── pyrightconfig.json              # Type checking config
├── data/
│   ├── filaments.json              # Inventory datastore
│   └── ams_data_sample.json        # Sample AMS data
└── tools/
    ├── postprint_usage.py          # G-code parser & auto-deduction
    ├── postprint-wrapper.bat       # Slicer wrapper (Windows)
    ├── setup-slicer-wrapper.ps1    # Setup helper
    ├── bambu_ams_sync.py           # Bambu AMS manual sync
    ├── bambu_quick_sync.bat        # Quick sync helper (batch)
    ├── bambu_quick_sync.ps1        # Quick sync helper (PowerShell)
    └── test_postprint.py           # Post-print integration tests
```

---

## Network Sharing

1. Allow network binding: `$env:FLASK_HOST='0.0.0.0'`
2. Start the server: `python start.py`
3. Find your IP: `ipconfig`
4. Share: `http://YOUR_IP:5000` (API) or `http://YOUR_IP:8501` (Dashboard)
5. Allow firewall access on ports 5000 and 8501

> **Note:** By default Flask only listens on `127.0.0.1` (localhost). Set `FLASK_HOST=0.0.0.0` to expose to the network.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask 3.0+ |
| Dashboard | Streamlit 1.28+ |
| Charts | Plotly 5.17+ |
| Data | pandas 2.0+ |
| Storage | JSON file |
| HTTP Client | requests 2.31+ |

---

## Running Tests

```powershell
python tools\test_postprint.py
```

Tests cover complete prints (footer data) and failed prints (header-only estimates).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Flask won't start | Check Python 3.10+, run `pip install -r requirements.txt`, verify port 5000 free |
| Streamlit won't launch | `streamlit run dashboard.py --logger.level=debug` |
| Can't access from other devices | Allow firewall on ports 5000/8501, same network required |
| Post-print no update | Ensure Flask running, check `FILAMENT_POSTPRINT_LOG=1` |
| AMS sync "NO MATCH" | Verify color/material names match inventory exactly |
| 401 Unauthorized | Set `FILAMENT_API_KEY` env var or pass `X-API-Key` header |
- Data survives between server restarts

---

## Additional Documentation

- **.github/copilot-instructions.md** — Complete project context for AI assistants

---

## 📄 License

MIT License — Feel free to modify and distribute as needed.

---

**Built with ❤️ using 100% Pure Python** 🐍
