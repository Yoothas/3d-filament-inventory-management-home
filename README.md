# 3D Filament Inventory System# 3D Filament Inventory System



A local-first, **100% Python** inventory manager for 3D printing filament spools.Note: This project is now Python-only. The legacy JavaScript frontend under `public/` has been removed. Use the Streamlit dashboard as the UI and the Flask API for integrations.



- **Flask API** — JSON-only REST endpoints for integrations and post-print auto-deductionQuick Start (Windows PowerShell)

- **Streamlit Dashboard** — Primary user interface with charts, filtering, and CRUD operations

- **Single datastore** — `data/filaments.json` shared between both interfaces1) Install dependencies

- **Zero JavaScript** — Pure Python stack (Flask + Streamlit + pandas + plotly)

```powershell

## Quick Start (Windows PowerShell)pip install -r requirements.txt

```

### Prerequisites

- Python 3.10+2) Start the Flask API (port 5000)

- pip

```powershell

### 1) Install dependenciespython app.py

```

```powershell

pip install -r requirements.txt3) Start the Streamlit dashboard (port 8501)

```

```powershell

### 2) Start the Flask API (port 5000)streamlit run dashboard.py

```

```powershell

python app.pyBoth share the same datastore at `data/filaments.json`.

```



Access health check: http://localhost:5000/

A Python Flask-based inventory management system for tracking 3D printing filament spools with automatic deduction from slicer integration.A local web-based inventory management system for tracking 3D printing filament spools. Built with Python Flask, designed to run locally and be accessible to multiple users on the same network.

### 3) Start the Streamlit dashboard (port 8501)



```powershell

streamlit run dashboard.py## Features## 🎯 Two Interface Options

```



Access UI: http://localhost:8501/

### Core FeaturesThis system provides **two ways** to manage your filament inventory:

Both interfaces share the same datastore at `data/filaments.json`.

- 📊 **Comprehensive Tracking**: Track brand, material, color, weight, cost, and usage

## Features

- 🎯 **Visual Progress**: See remaining filament with progress bars1. **Flask Web App** (Classic) - Multi-user web interface with API endpoints

- 📊 **Comprehensive Tracking** — Brand, material, color, weight, cost, and usage

- 🎯 **Visual Progress** — Progress bars and progress indicators  - 🔍 **Smart Search**: Filter by material type or search across all fields   - Best for: Network sharing, mobile access, API automation

- 🔍 **Smart Search** — Filter by material type, brand, color, or custom queries

- 📈 **13+ Sort Options** — Usage, stock levels, purchase date, brand, color, cost, and more- 📈 **Advanced Sorting**: 13+ sort options including usage, stock levels, purchase date, brand, color, and cost   - Port: 5000

- 💾 **Local Storage** — All data persists in JSON files locally

- 🤖 **Slicer Integration** — Automatic filament deduction from Anycubic Slicer post-processing- 💾 **Local Storage**: All data stored locally in JSON files

- 📊 **Print History** — Track recent print jobs and filament consumption per spool- 🤖 **Slicer Integration**: Automatic filament deduction after prints (Anycubic Slicer)

- 📦 **Archive System** — Auto-archive empty spools (0g) while preserving full history- 📈 **Print History**: Track recent print jobs and filament consumption

- 🔄 **Bulk Operations** — Multi-filament usage tracking for complex multi-material prints- 📦 **Archive System**: Auto-archive empty spools while preserving history

- 🌙 **Dark Mode**: Toggle between light and dark themes

## Slicer Post-Print Integration- Tech: **100% Python** (no JavaScript whatsoever)



Configure Anycubic Slicer to auto-deduct filament after each print:### Two Interface Options



1. Start the Flask API (step 2 above)**Both interfaces share the same data!** Use one, or run both simultaneously.

2. In Anycubic Slicer: **Machine Settings** → **Scripts** → **Post-print script**

3. Set the command to: `C:\3DPrint\slicer-postprint.bat`1. **Flask Web App** (Port 5000) - Multi-user web interface

   - Use `tools/setup-slicer-wrapper.ps1` to install the wrapper automatically

4. The script will:   - Best for: Network sharing, mobile access📚 **See [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md) for the pure Python option.**

   - Parse the latest G-code for material, color, brand, and weight used

   - Call the Flask API to match and deduct filament   - Tech: Python Flask + JavaScript

   - Auto-archive spools when they reach 0g remaining

## Features

## API Endpoints (Flask)

2. **Streamlit Dashboard** (Port 8501) - 100% Python analytical dashboard

### Filaments

- `GET /api/filaments` — List all active filaments (add `?include_archived=true` for all)   - Best for: Personal use, data visualization### Core Features (Both Interfaces)

- `GET /api/filaments/:id` — Get a single filament

- `POST /api/filaments` — Create a new filament   - Tech: 100% Python with interactive charts- 📊 **Comprehensive Tracking**: Track brand, material, color, weight, cost, and usage

- `PUT /api/filaments/:id` — Update a filament

- `DELETE /api/filaments/:id` — Delete a filament- 🎯 **Visual Progress**: See remaining filament with progress bars



### Usage & Search**Both interfaces share the same data!**- 🔍 **Smart Search**: Filter by material type or search across all fields

- `POST /api/filaments/:id/use` — Deduct filament after print (auto-archives at 0g)

- `POST /api/filaments/bulk-use` — Multi-filament usage for complex prints- 📈 **Advanced Sorting**: 13+ sort options including usage, stock levels, purchase date, brand, color, and cost

- `GET /api/filaments/search?material=PLA&color=Black` — Find matching filaments

---- 💾 **Local Storage**: All data stored locally in JSON files

### Archive

- `POST /api/filaments/:id/archive` — Archive a spool- 🤖 **Slicer Integration**: Automatic filament deduction after prints (Anycubic Slicer)

- `POST /api/filaments/:id/unarchive` — Restore an archived spool

- `GET /api/filaments/archived` — List all archived spools## Quick Start- 📈 **Print History**: Track recent print jobs and filament consumption

- `POST /api/filaments/auto-archive` — Archive all empty spools at once

- 🔄 **Bulk Operations**: Multi-filament usage tracking for complex prints

## Project Structure

### 1. Install Dependencies- 📦 **Archive System**: Auto-archive empty spools while preserving history (NEW!)

```

3d-filament-inventory-management-home/

├── app.py                      # Flask API (JSON only, no static serving)

├── dashboard.py                # Streamlit UI (primary interface)```bash### Flask Web App Features

├── data/

│   └── filaments.json          # JSON datastore (single source of truth)pip install -r requirements.txt- �📱 **Responsive Design**: Works on desktop, tablet, and mobile devices

├── tools/

│   ├── postprint_usage.py      # Post-print auto-deduction logic```- 🌐 **Network Access**: Share with roommates or others on your local network

│   ├── postprint-wrapper.bat   # Windows batch wrapper for slicers

│   ├── setup-slicer-wrapper.ps1 # Helper to install wrapper at C:\3DPrint- ⚡ **Real-time Updates**: Instant updates across all connected browsers

│   └── test_postprint.py       # Regression tests for G-code parsing

├── requirements.txt            # Python dependencies (Flask, Streamlit, pandas, plotly)### 2. Start the Server- 🌙 **Dark Mode**: Toggle between light and dark themes

├── start-server.bat/.ps1       # Flask API launcher (Windows)

└── start-dashboard.bat/.ps1    # Streamlit launcher (Windows)- 🔌 **REST API**: Full API for automation and integrations

```

**Option A: Flask Web App**

## Configuration

```bash### Streamlit Dashboard Features  

### Changing the Flask API port

# Windows- 📊 **Interactive Charts**: Pie charts, bar graphs, live metrics

```powershell

$env:PORT=8080; python app.pystart-server.bat- � **100% Python**: No JavaScript knowledge required

```

- 🔄 **Auto-refresh**: Live data updates

### Adding new material types

# Or manually- 🎨 **Built-in Theming**: Light/dark mode with customizable colors

Edit `dashboard.py` and find the line:

```pythonpython app.py- 📥 **Export Ready**: Easy CSV/Excel export additions

new_material = st.selectbox("Material *", ["PLA", "ABS", "PETG", "TPU", "ASA", "Other"])

``````



Add your material to the list.## Quick Start



## TroubleshootingAccess at: http://localhost:5000



### Flask API won't start### Option 1: Flask Web App (Multi-user)

- Ensure Python 3.10+ is installed: `python --version`

- Run `pip install -r requirements.txt`**Option B: Streamlit Dashboard**

- Check for error messages in the terminal

- Verify port 5000 is not in use (or set `PORT` environment variable)```bash#### Prerequisites



### Streamlit won't launch# Windows

- Ensure Streamlit is installed: `pip install streamlit`

- Try running: `streamlit run dashboard.py --logger.level=debug`start-dashboard.bat- Python 3.8 or higher



### Can't access from other devices- pip (Python package installer)

- Allow inbound firewall on ports 5000 (Flask) and 8501 (Streamlit)

- Ensure all devices are on the same network# Or manually

- Find your IP with `ipconfig` on Windows

streamlit run dashboard.py#### Installation & Setup

### Data not saving

- Verify write permissions for the `data/` folder```

- Ensure the directory is not open in another process

1. **Install Dependencies**

## Requirements

Access at: http://localhost:8501   ```bash

- Python 3.10+

- Flask 3.0+   pip install -r requirements.txt

- Streamlit 1.28+

- pandas 2.0+---   ```

- plotly 5.17+

- requests 2.31+



All managed in `requirements.txt`.## Slicer Integration (Auto-Deduct)2. **Start the Server**



## Tips & Best Practices   



### Keeping the Flask server running### Quick Setup   **Easy way (Windows):**

- **Option 1: Dedicated Terminal** — Keep a PowerShell window open running `python app.py`

- **Option 2: Background Process** — Use `start-server.bat` to run in a separate window   - Double-click `start-server.bat` or run `start-server.ps1`

- **Option 3: Task Scheduler** — Set up Windows Task Scheduler to auto-start on boot

**Step 1: Start Flask Server**   

### Network sharing

1. Start Flask: `python app.py` or `start-server.bat````bash   **Manual way:**

2. Find your IP: `ipconfig` (look for IPv4 Address)

3. Share the URL: `http://YOUR_IP_ADDRESS:5000` (for API) or `http://YOUR_IP_ADDRESS:8501` (for dashboard)python app.py   ```bash

4. Others can access directly in their browsers

```   python app.py

### Data management

- All data persists in `data/filaments.json`   ```

- Regular backups: `copy data\filaments.json data\filaments.backup.json`

- Data survives between server restarts**Step 2: Configure Anycubic Slicer**   



## Technology Stack   Or with Flask's development mode:



| Component | Technology | Why |Go to: **Machine Settings** → **Scripts** → **Post-print script**   ```bash

|-----------|-----------|-----|

| **Backend API** | Flask (Python) | Lightweight, simple REST endpoints |   flask --app app run --host=0.0.0.0 --port=5000

| **Frontend UI** | Streamlit (Python) | Interactive charts, no JavaScript needed |

| **Data Layer** | JSON file | Simple, portable, no database setup |Enter:   ```

| **Charts** | Plotly (Python) | Interactive visualizations in Streamlit |

| **Data Processing** | pandas (Python) | Filtering, sorting, aggregation |```



## LicenseC:\3DPrint\slicer-postprint.bat3. **Access the Application**



MIT License — Feel free to modify and distribute as needed.```   - Local access: http://localhost:5000



## Support   - Network access: http://YOUR_IP_ADDRESS:5000



For issues or questions, see the documentation files:That's it! The script automatically finds and processes G-code files.

- `FINAL_SLICER_SETUP.md` — Detailed slicer integration guide

- `TROUBLESHOOTING.md` — Extended troubleshootingNote: The Flask API defaults to port 5000. You can change it by setting the `PORT` environment variable.

- `QUICK_START.md` — Additional getting-started guide

### How It Works

---

### Option 2: Streamlit Dashboard (Pure Python)

**Last Updated:** October 18, 2025  

**Status:** ✅ Production Ready  1. Slicer generates G-code and saves to temp folder

**Version:** 2.0 (Python Flask + Streamlit, 100% Pure Python)

2. Slicer calls the post-print script#### Prerequisites

3. Script finds the most recent G-code file (< 5 minutes old)

4. Script parses material, color, brand, and weight from G-code- Python 3.8 or higher

5. Script calls Flask API to match and deduct filament- pip (Python package installer)

6. Inventory updates automatically!

#### Installation & Setup

### Troubleshooting

1. **Install Dependencies**

**Error: "Post-processing script failed. Error code: 2"**   ```bash

- Solution: Use the command with NO file path arguments   pip install streamlit pandas plotly

- The script auto-finds files, no variables needed   ```

   

**No inventory update**   Or use requirements.txt:

- Ensure Flask server is running on port 5000   ```bash

- Check: http://localhost:5000   pip install -r requirements.txt

   ```

**No matching filament found**

- Verify you have a filament in inventory matching:2. **Start the Dashboard**

  - Material: PLA, PETG, etc.   

  - Color: Black, White, etc.   **Easy way (Windows):**

  - Brand: Anycubic, etc.   - Double-click `start-dashboard.bat` or run `start-dashboard.ps1`

- Ensure filament is not archived   

- Check remaining weight > 0g   **Manual way:**

   ```bash

---   streamlit run dashboard.py

   ```

## Usage

3. **Access the Dashboard**

### Flask Web Interface   - Local access: http://localhost:8501

   - Network access: http://YOUR_IP_ADDRESS:8501

#### Adding Filaments

1. Click "**+ Add Filament**" button📚 **Full Streamlit documentation:** [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md)

2. Fill in: Brand, Material, Color, Weight, Cost, etc.

3. Click "**Save**"### Running Both Simultaneously



#### Editing FilamentsYou can run **both** interfaces at the same time!

1. Click the **✏️ Edit** button on any filament card

2. Modify the fields```bash

3. Click "**Update Filament**"# Terminal 1: Flask Web App (port 5000)

python app.py

#### Using Filament

1. Click "**Use Material**" button on filament card# Terminal 2: Streamlit Dashboard (port 8501)

2. Enter amount used in gramsstreamlit run dashboard.py

3. Optionally add print job name```

4. Click "**Deduct**"

Both share the same `data/filaments.json` file, so changes in one appear in the other.

#### Archiving

- **Manual Archive**: Click "📦 Archive" button on empty spools (0g)### Finding Your IP Address

- **Auto-Archive**: Click "🗄️ Auto-Archive Empty Spools" in header

- **Restore**: Click "↻ Restore" on archived spools**Windows:**

- **View Archived**: Click "📦 Archived (X)" in stats bar```bash

ipconfig

#### Sorting```

Use the dropdown in the header to sort by:Look for "IPv4 Address" under your active network connection.

- Recently Used

- Most/Least Used**macOS/Linux:**

- Low/High Stock```bash

- Newest/Oldest Purchaseifconfig

- Brand (A-Z or Z-A)```

- Material, Color, Costor

```bash

#### Search & Filterip addr show

- Use search box to find filaments by brand, material, or color```

- Click material type badges (PLA, PETG, etc.) to filter

- Click "🔍 All Materials" to clear filters## Anycubic Slicer Integration (Auto-deduct filament)



---You can have Anycubic Slicer call back into this app after a print to auto-reduce the filament remaining.



### Streamlit Dashboard### 🚀 Quick Setup (2 Steps)



#### Features**Step 1: Start Flask Server**

- 📊 **Interactive Charts**: Pie charts, bar graphs, live metrics```bash

- 📈 **Real-time Stats**: Total spools, weight, value, low stock# Double-click: start-server.bat

- 🔄 **Auto-refresh**: Live data updates# Or run: python app.py

- 🎨 **Built-in Theming**: Light/dark mode```

Server must be running at http://localhost:5000

#### View Modes

- **Active Spools**: Show only active filaments (default)**Step 2: Configure Anycubic Slicer**

- **Archived Spools**: Show archived/used spools

- **All Spools**: Show everythingGo to: **Machine Settings** → **Scripts** → **Post-print script**



#### Editing FilamentsEnter this **EXACT** command (no file path needed):

1. Find the filament card```

2. Click "✏️ Edit" buttonC:\3DPrint\slicer-postprint.bat

3. Form appears with current values```

4. Modify fields as needed

5. Click "💾 Save" or "❌ Cancel"That's it! The script will automatically find and process your G-code files.



#### Adding Filaments---

1. Scroll to bottom: "➕ Add New Filament"

2. Fill in all required fields (marked with *)### 📚 Complete Guide

3. Click "➕ Add Filament"

See **[FINAL_SLICER_SETUP.md](FINAL_SLICER_SETUP.md)** for:

---- Detailed setup instructions

- Troubleshooting guide

## API Endpoints- How to verify it's working

- Pro tips and automation

### Filaments

- `GET /api/filaments` - Get all active filaments**Other helpful docs:**

- `GET /api/filaments/:id` - Get specific filament- **FIX_ERROR_CODE_2.md** - If you get error code 2

- `POST /api/filaments` - Add new filament- **SLICER_CONFIG.md** - Alternative configurations

- `PUT /api/filaments/:id` - Update filament- **QUICK_START.md** - Complete startup guide

- `DELETE /api/filaments/:id` - Delete filament

---

### Usage Tracking

- `POST /api/filaments/:id/use` - Deduct filament weight### ⚙️ Advanced Configuration (Optional)

- `GET /api/filaments/search` - Search filaments by material/color/brand

If you want to manually specify values, you can still use command-line arguments:

### Archive System

- `POST /api/filaments/:id/archive` - Archive a filamentThe script will scan both the first ~500 lines and the last ~500 lines of the G-code to extract material/color/brand and filament used (grams or cm³), then call the API. You can still override values explicitly with flags if needed.

- `POST /api/filaments/:id/unarchive` - Restore archived filament

- `GET /api/filaments/archived` - Get archived filaments**Command Line Options:**

- `GET /api/filaments/active` - Get active filaments only- `--used-g` - Grams of filament used

- `POST /api/filaments/auto-archive` - Auto-archive all empty spools- `--used-mm3` - Cubic millimeters of filament used  

- `--density` - Filament density in g/cm³ (for mm³ to grams conversion)

---- `--material` - Material type (PLA, PETG, etc.)

- `--color` - Filament color

## Project Structure

```
3d-filament-inventory-management-home/
├── app.py                # Flask API backing the slicer/post-print tooling
├── dashboard.py          # Streamlit UI (filters, charts, CRUD, archive management)
├── data/
│   └── filaments.json   # JSON datastore for private setups
├── tools/
│   ├── postprint_usage.py        # Main post-print Python script (auto-deduct logic)
│   ├── postprint-wrapper.bat     # Wrapper for slicers that dislike spaces in paths
│   ├── setup-slicer-wrapper.ps1  # Helper to install the wrapper at C:\3DPrint
│   └── test_postprint.py         # Regression tests for G-code parsing logic
├── requirements.txt       # Python dependencies (Flask, Streamlit, Plotly, requests)
├── start-dashboard.*      # Convenience launchers for Streamlit
└── start-server.*         # Convenience launchers for Flask API
```

## Smart Filament Matching

- **Brand mapping:** generic brands like “Anycubic” can match richer inventory entries such as “Anycubic High Speed”.
- **Color mapping:** hex codes and variants like `Clear`, `Transparent`, or `Light Gray` are normalized to `Translucent`.
- **Fallback order:** exact match → material+color → color variants → material-only, ensuring reliable auto-selection even with sparse slicer metadata.

├── start-server.bat/ps1       # Flask launcher

└── start-dashboard.bat/ps1    # Streamlit launcherOptional environment overrides:

```- `FILAMENT_SERVER_HOST` (e.g., `http://192.168.1.18:5000`) if the slicer is on a different machine

- `FILAMENT_SERVER_PORT` (default 5000)

---- `FILAMENT_POSTPRINT_LOG` set to `1` to write a log to `~/.filament-inventory/postprint.log`, or set to a full file path for a custom log location. Helpful for troubleshooting.



## ConfigurationTroubleshooting:

- Ensure Python 3 is installed and in your PATH

### Environment Variables (Optional)- Check that your filament inventory contains matching Material/Color/Brand

- Watch the command line output in Slicer's post-processing log for details

- `FILAMENT_SERVER_HOST` - Server URL (default: http://localhost:5000)- Enable logging by setting `FILAMENT_POSTPRINT_LOG=1` and review the log for parsed values and API responses

- `FILAMENT_SERVER_PORT` - Server port (default: 5000)

- `FILAMENT_POSTPRINT_LOG` - Enable logging (set to `1`)## Usage



---### Adding Filaments



## Data Format1. Click the "**+ Add Filament**" button

2. Fill in the filament details:

Filaments are stored in `data/filaments.json`:   - **Brand**: Manufacturer name (e.g., Hatchbox, SUNLU)

   - **Material**: Filament type (PLA, ABS, PETG, etc.)

```json   - **Color**: Color description

{   - **Weight**: Original spool weight in grams

  "id": "1760220208055",   - **Remaining Weight**: Current remaining weight (defaults to original weight)

  "brand": "Anycubic High Speed",   - **Diameter**: 1.75mm, 2.85mm, or 3.0mm

  "material": "PLA",   - **Cost**: Purchase price (optional)

  "color": "Black",   - **Purchase Date**: When you bought it (optional)

  "weight": 5000.0,   - **Notes**: Any additional information (optional)

  "remainingWeight": 3966.77,

  "diameter": 1.75,### Managing Inventory

  "cost": 59.82,

  "purchaseDate": "2025-10-12",- **Edit**: Click the "Edit" button on any filament card to update details

  "notes": "",- **Delete**: Click the "Delete" button to remove a filament (with confirmation)

  "archived": false,- **Search**: Use the search bar to find specific filaments by brand, material, or color

  "createdAt": "2025-10-11T22:03:28.055Z",- **Filter by Material**: Use the material dropdown to show only specific filament types

  "updatedAt": "2025-10-18T15:20:08.184758",- **Sort**: Use the sort dropdown to organize your inventory (13+ options available)

  "lastUsed": "2025-10-18T15:20:08.184758",

  "printHistory": [### Sorting Your Inventory

    {

      "date": "2025-10-18T15:20:08.184758",The inventory supports multiple sorting options to help you organize and find filaments:

      "printJob": ".34008.2",

      "usedWeight": 126.84,**Usage-Based:**

      "remainingAfter": 3966.77,- **Recently Used**: Shows most recently used filaments first

      "printTime": 0- **Most Used**: Sorts by total weight consumed

    }- **Least Used**: Shows unused or rarely used spools

  ]

}**Stock Management:**

```- **Low Stock First**: Prioritizes spools running low (great for reorder planning)

- **High Stock First**: Shows fullest spools first

---

**Purchase History:**

## Technical Details- **Newest Purchase**: Most recently bought filaments

- **Oldest Purchase**: Implement FIFO inventory rotation

### Smart Filament Matching

**Organization:**

The post-print script uses intelligent matching:- **Brand (A-Z / Z-A)**: Alphabetical by manufacturer

- **Material**: Groups by type (PLA, PETG, etc.)

1. **Exact Match**: Material + Color + Brand- **Color (A-Z)**: Alphabetical by color name

2. **Partial Brand**: "Anycubic" matches "Anycubic High Speed"- **Cost (High-Low / Low-High)**: Sort by purchase price

3. **Color Detection**: Hex codes (#212721 → Black via RGB analysis)

4. **Best Match Scoring**:For detailed sorting documentation, see [SORTING_FEATURES.md](SORTING_FEATURES.md).

   - Exact color match: +100 points

   - Brand substring match: +30 points### Tracking Usage

   - Recently used: +20 points

   - High remaining weight: +10 points- Update the "Remaining Weight" field when editing a filament

- The progress bar shows how much filament is left

### Auto-Archive Logic- Cards with less than 20% remaining are highlighted in red

- View total statistics at the top of the page

- Spools automatically archived when `remainingWeight ≤ 0`- Use "Recently Used" sort to see your active spools

- Archives preserve full print history

- Archived spools excluded from search by default### Archive & History

- Can be restored at any time

**NEW:** Keep your inventory clean without losing data!

---

**Automatic Archiving:**

## Requirements- Spools with 0g remaining are automatically archived

- Happens when post-print script deducts final grams

- Python 3.10+- Or when you manually set remaining weight to 0g

- Flask 3.0+

- Streamlit 1.28+**Manual Operations:**

- pandas 2.0+- **View Archive**: Click "📦 Archive" button to see all archived spools

- plotly 5.17+- **Auto-Archive**: Click "🗄️ Auto-Archive" to archive all empty spools at once

- requests 2.31+- **Restore**: Unarchive any spool to return it to active inventory

- **Delete**: Permanently remove archived spools (irreversible!)

---

**Benefits:**

## Tips & Best Practices- Active inventory only shows usable spools

- No more false "low stock" warnings on empty spools

### Keeping Flask Server Running- Complete historical record of all purchases

- Track total filament consumption over time

**Option 1: Dedicated Terminal**- Make data-driven reorder decisions

```bash

python app.py📚 **Full documentation:** [ARCHIVE_FEATURE.md](ARCHIVE_FEATURE.md)

# Keep window open

```## Network Sharing



**Option 2: Background Process**To share with roommates or others on your network:

```powershell 

Start-Process powershell -ArgumentList "-NoExit","-Command","cd 'D:\your\path'; python app.py"1. Start the server: `python app.py` (or double-click `start-server.bat`)

```2. Find your computer's IP address (`ipconfig` on Windows, `ifconfig` on macOS/Linux)

3. Share the URL: `http://YOUR_IP_ADDRESS:5000`

**Option 3: Windows Task Scheduler** (Auto-start on boot)4. Others can access it directly in their browsers

```powershell

$action = New-ScheduledTaskAction -Execute "python" -Argument "app.py" -WorkingDirectory "D:\your\path"**Example:**

$trigger = New-ScheduledTaskTrigger -AtStartupIf your IP is `192.168.1.100`, share: `http://192.168.1.100:5000`

Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "FilamentServer"

```## Data Storage



### Managing Inventory- All data is stored in `data/filaments.json`

- Data persists between server restarts

- **Low Stock Threshold**: 20% or less shows warning- Automatic backup on each change

- **Archive Empty Spools**: Keeps inventory clean- No database setup required

- **Print History**: Tracks all usage for analytics

- **Regular Backups**: Copy `data/filaments.json` periodically## Keyboard Shortcuts



---- **Ctrl/Cmd + N**: Add new filament

- **Ctrl/Cmd + D**: Toggle dark mode

## License- **Escape**: Close modal dialogs



MIT License## AMS Integration (Anycubic Kobra 2 Pro Ready)



---### Automatic Filament Tracking

The system includes API endpoints for automatic integration with your 3D printer and AMS:

## Support

**Slicer Post-Processing Integration:**

For issues or questions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or [QUICK_START.md](QUICK_START.md)- Automatically track filament usage after each print

- Smart filament matching by material and color

---- Multi-material print support



**Last Updated:** October 18, 2025  **Print History Tracking:**

**Status:** ✅ Production Ready  - See recent print jobs on each filament card

**Version:** 2.0 (Python Flask + Streamlit)- Track usage patterns and consumption rates

- Automatic weight updates after prints

### API Integration Examples

**Reduce filament usage (post-print):**
```bash
POST /api/filaments/:id/use
{
  "usedWeight": 25.5,
  "printJob": "phone_case.gcode",
  "printTime": 180
}
```

**Find matching filament for AMS:**
```bash
GET /api/filaments/search?material=PLA&color=Red
```

**Multi-material usage tracking:**
```bash
POST /api/filaments/bulk-use
[
  {"id": "123", "usedWeight": 15.2},
  {"id": "456", "usedWeight": 8.7}
]
```

## Technical Details

### File Structure
```
3d-filament-inventory/
├── requirements.txt      # Python dependencies
├── app.py               # Flask server and API
├── dashboard.py         # Streamlit dashboard (primary UI)
├── data/                # Data storage
│   └── filaments.json  # Filament inventory data
└── tools/              # Integration scripts
   ├── postprint_usage.py      # Python post-print script
   ├── postprint-wrapper.bat   # Slicer-friendly wrapper
   └── setup-slicer-wrapper.ps1 # Helper to install wrapper
```

### API Endpoints

**Core Inventory:**
- `GET /api/filaments` - Get all filaments
- `POST /api/filaments` - Add new filament
- `PUT /api/filaments/:id` - Update filament
- `DELETE /api/filaments/:id` - Delete filament

**AMS Integration:**
- `POST /api/filaments/:id/use` - Track filament usage
- `GET /api/filaments/search` - Find filaments by criteria
- `POST /api/filaments/bulk-use` - Multi-filament usage
- `GET /api/ams/status` - AMS slot mapping

## Troubleshooting

### Server Won't Start
- Ensure Python 3.8+ is installed: `python --version`
- Check if port 5000 is available (or your custom PORT)
- Run `pip install -r requirements.txt` to install dependencies
- Check for error messages in the console

### Can't Access from Other Devices
- Verify your computer's firewall allows connections on port 5000 (Flask) and 8501 (Streamlit)
- Ensure all devices are on the same network
- Double-check the IP address

### Data Not Saving
- Check file permissions in the `data/` directory
- Ensure the server has write access to the project folder

## Customization

### Changing the Port
Edit `app.py` and modify the `PORT` variable, or set the `PORT` environment variable:
```bash
# Windows PowerShell
$env:PORT=8080; python app.py

# Linux/macOS
PORT=8080 python app.py
```

### Extending the System

To add new material types, edit the options in `dashboard.py`:

Find the `st.selectbox("Material *", [...])` line and add your new material name to the list.

## Future Printer Integration

### Anycubic Kobra S1 Pro + AMS 

**Slicer Setup (Anycubic Slicer):**
1. Enable post-processing scripts in slicer settings
2. Add PowerShell script to call usage APIs after prints
3. Configure material/color variables for automatic matching

**Klipper Integration (If Upgrading Firmware):**
1. Add custom macros for print completion
2. Configure HTTP calls to inventory APIs  
3. Enable automatic spool detection and tracking

**AMS Hardware Integration (Future):**
- Direct communication with AMS slots
- Automatic spool identification
- Real-time weight monitoring

The system is designed to grow with your setup - start simple and add automation as needed!

## Contributing

Feel free to customize this application for your specific needs. The code is well-commented and modular for easy modification.

## License

MIT License - Feel free to modify and distribute as needed.