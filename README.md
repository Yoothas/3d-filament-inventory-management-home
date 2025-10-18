# 3D Filament Inventory Management

A local-first, **100% Python** inventory system for tracking 3D printing filament spools with automatic post-print deduction.

**Status:** ✅ Production Ready | **Version:** 2.0 | **Last Updated:** October 18, 2025

## 🚀 Quick Start

**Prerequisites:**
- Python 3.10+
- pip (Python package installer)

**Installation:**

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Flask API (port 5000)
python app.py

# 3. Start Streamlit Dashboard (port 8501)
streamlit run dashboard.py
```

**Access:**
- API: http://localhost:5000
- Dashboard: http://localhost:8501

Both interfaces share the same datastore at `data/filaments.json`.

---

## ✨ Features

**Core Functionality:**
- 📊 **Comprehensive Tracking** — Brand, material, color, weight, cost, and usage
- 🎯 **Visual Progress Bars** — See remaining filament at a glance
- 🔍 **Smart Search & Filtering** — By material type, brand, color, or custom queries
- 📈 **13+ Sort Options** — Usage, stock levels, purchase date, brand, color, cost
- 💾 **Local Storage** — All data persists in JSON files (no database needed)
- 🤖 **Slicer Integration** — Automatic filament deduction from Anycubic Slicer
- 📊 **Print History** — Track recent print jobs and consumption per spool
- 📦 **Archive System** — Auto-archive empty spools while preserving full history
- 🔄 **Bulk Operations** — Multi-filament usage tracking for complex prints

**Smart Filament Matching:**
- Brand mapping: "Anycubic" matches "Anycubic High Speed"
- Color detection: Hex codes analyzed via RGB brightness
- Fallback order: Exact match → material+color → material-only
- Scoring system: Exact color +100pts, brand +30pts, recent use +20pts

---

## 🎯 Two Interface Options

**1. Flask Web API (Port 5000)**
- Multi-user web interface
- REST API for automation and integrations
- Network-accessible for roommates/team
- JSON-only responses

**2. Streamlit Dashboard (Port 8501)**
- 100% Python analytical interface
- Interactive charts (Plotly pie/bar graphs)
- Real-time stats and live data updates
- Built-in theming (light/dark mode)

**Both share the same data!** Run one or both simultaneously.

---

## 🔗 Slicer Integration (Auto-Deduct)

**Quick Setup (2 Steps):**

1. Start Flask Server: `python app.py` (must be running at http://localhost:5000)
2. Configure Anycubic Slicer: **Machine Settings** → **Scripts** → **Post-print script**
   - Enter: `C:\3DPrint\slicer-postprint.bat`

The script will automatically:
- Find the most recent G-code file
- Parse material, color, brand, and weight
- Call Flask API to match and deduct filament
- Auto-archive spools at 0g

**Install Wrapper:** Run `tools/setup-slicer-wrapper.ps1`

**Troubleshooting:**
- No inventory update: Ensure Flask server is running on port 5000
- No matching filament: Verify material/color/brand in inventory
- Error code 2: Use command with NO file path arguments
- Enable logging: Set `FILAMENT_POSTPRINT_LOG=1`

---

## 📡 API Endpoints

**Filament Management:**
- `GET /api/filaments` — List all active filaments
- `POST /api/filaments` — Create new filament
- `PUT /api/filaments/:id` — Update filament
- `DELETE /api/filaments/:id` — Delete filament

**Usage & Search:**
- `POST /api/filaments/:id/use` — Deduct filament (auto-archives at 0g)
- `POST /api/filaments/bulk-use` — Multi-filament usage
- `GET /api/filaments/search?material=PLA&color=Black` — Find filaments

**Archive System:**
- `POST /api/filaments/:id/archive` — Archive a spool
- `POST /api/filaments/:id/unarchive` — Restore archived spool
- `GET /api/filaments/archived` — List archived spools

---

## 📂 Project Structure

```
3d-filament-inventory-management-home/
├── app.py                      # Flask REST API
├── dashboard.py                # Streamlit UI
├── data/
│   └── filaments.json          # JSON datastore
├── tools/
│   ├── postprint_usage.py      # Auto-deduction logic
│   ├── postprint-wrapper.bat   # Windows wrapper
│   ├── setup-slicer-wrapper.ps1 # Setup helper
│   └── test_postprint.py       # Tests (18/18 passing)
└── requirements.txt            # Python dependencies
```

---

## 🌐 Network Sharing

To share with others on your local network:

1. Start the server: `python app.py`
2. Find your IP: `ipconfig` (Windows) or `ifconfig` (macOS/Linux)
3. Share the URL: `http://YOUR_IP_ADDRESS:5000` or `http://YOUR_IP_ADDRESS:8501`
4. Allow firewall access on ports 5000 and 8501

---

## ⚙️ Configuration

**Environment Variables:**
- `PORT` — Flask API port (default: 5000)
- `FILAMENT_SERVER_HOST` — Server URL
- `FILAMENT_POSTPRINT_LOG` — Enable logging

**Change Flask Port:**
```powershell
$env:PORT=8080; python app.py
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend API | Flask | REST endpoints |
| Frontend UI | Streamlit | Interactive dashboards |
| Data Layer | JSON file | No database needed |
| Charts | Plotly | Interactive visualizations |
| Processing | pandas | Filtering, sorting, aggregation |

**Dependencies:** Flask 3.0+, Streamlit 1.28+, pandas 2.0+, plotly 5.17+, requests 2.31+

---

## 🔍 Troubleshooting

**Flask API won't start:**
- Ensure Python 3.10+ is installed
- Run `pip install -r requirements.txt`
- Verify port 5000 is not in use

**Streamlit won't launch:**
- Ensure Streamlit is installed
- Try: `streamlit run dashboard.py --logger.level=debug`

**Can't access from other devices:**
- Allow firewall access on ports 5000 and 8501
- Ensure all devices are on the same network

---

## 💡 Tips & Best Practices

**Keeping Flask Server Running:**
- Keep PowerShell window open running `python app.py`
- Use Windows Task Scheduler to auto-start on boot
- Run in background with VS Code tasks

**Data Management:**
- All data persists in `data/filaments.json`
- Regular backups: `copy data\filaments.json data\filaments.backup.json`
- Data survives between server restarts

---

## 📚 Additional Documentation

- **QUICK_START.md** — Getting-started guide
- **.github/copilot-instructions.md** — Complete project context

---

## 📄 License

MIT License — Feel free to modify and distribute as needed.

---

**Built with ❤️ using 100% Pure Python** 🐍
