# 3D Filament Inventory System

A local web-based inventory management system for tracking 3D printing filament spools. Built with Node.js and Express, designed to run locally and be accessible to multiple users on the same network.

## Features

- 📊 **Comprehensive Tracking**: Track brand, material, color, weight, cost, and usage
- 🎯 **Visual Progress**: See remaining filament with progress bars
- 🔍 **Smart Search**: Filter by material type or search across all fields
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🌐 **Network Access**: Share with roommates or others on your local network
- 💾 **Local Storage**: All data stored locally in JSON files
- ⚡ **Real-time Updates**: Instant updates across all connected browsers
- 🌙 **Dark Mode**: Toggle between light and dark themes
- 🤖 **AMS Integration Ready**: API endpoints for automatic filament usage tracking
- 📈 **Print History**: Track recent print jobs and filament consumption
- 🔄 **Bulk Operations**: Multi-filament usage tracking for complex prints

## Quick Start

### Prerequisites

- Node.js (v14 or higher)
- npm (comes with Node.js)

### Installation & Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start the Server**
   ```bash
   npm start
   ```
   
   Or for development with auto-restart:
   ```bash
   npm run dev
   ```

3. **Access the Application**
   - Local access: http://localhost:3000
   - Network access: http://YOUR_IP_ADDRESS:3000

### Finding Your IP Address

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your active network connection.

**macOS/Linux:**
```bash
ifconfig
```
or
```bash
ip addr show
```

## Anycubic Slicer Integration (Auto-deduct filament)

You can have Anycubic Slicer call back into this app after a print to auto-reduce the filament remaining.

1) Make sure the server is running on the same PC as the slicer (or set FILAMENT_SERVER_HOST)

2) Save the helper script:
- File already included at `tools/postprint-usage.ps1`

3) In Anycubic Slicer, set a Post-processing command (after slicing or after print):

Windows PowerShell command to paste:

Option A — direct PowerShell (works when Slicer accepts commands):

```
powershell -ExecutionPolicy Bypass -File "${project_path}/tools/postprint-usage.ps1" -used_mm3 ${filament_used_mm3} -material "${filament_type[0]}" -color "${filament_color[0]}" -brand "${filament_vendor[0]}" -job "${filename}"
```

Option B — reference a script file (recommended if you see "configured post-processing script does not exist"):

```
"${project_path}/tools/postprint-usage.cmd" -used_mm3 ${filament_used_mm3} -material "${filament_type[0]}" -color "${filament_color[0]}" -brand "${filament_vendor[0]}" -job "${filename}"
```

Notes:
- If your slicer provides `${filament_used_mm3}`, the script will convert to grams. You can override density via `-density 1.24` (PLA default), e.g. PETG 1.27, ABS 1.04.
- If your slicer exposes `${filament_used_g}` directly, use that instead for `-used_g`
- For multi-material, duplicate the flags with index `[1]`, `[2]`, etc. and call the script multiple times, or switch to the bulk API.

Optional environment overrides:
- `FILAMENT_SERVER_HOST` (e.g., `http://192.168.1.18:3000`) if the slicer is on a different machine
- `FILAMENT_SERVER_PORT` (default 3000)

Troubleshooting:
- If PowerShell script execution is blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- Check that your filament inventory contains matching Material/Color/Brand
- Watch the command line output in Slicer’s post-processing log for details

## Usage

### Adding Filaments

1. Click the "**+ Add Filament**" button
2. Fill in the filament details:
   - **Brand**: Manufacturer name (e.g., Hatchbox, SUNLU)
   - **Material**: Filament type (PLA, ABS, PETG, etc.)
   - **Color**: Color description
   - **Weight**: Original spool weight in grams
   - **Remaining Weight**: Current remaining weight (defaults to original weight)
   - **Diameter**: 1.75mm, 2.85mm, or 3.0mm
   - **Cost**: Purchase price (optional)
   - **Purchase Date**: When you bought it (optional)
   - **Notes**: Any additional information (optional)

### Managing Inventory

- **Edit**: Click the "Edit" button on any filament card to update details
- **Delete**: Click the "Delete" button to remove a filament (with confirmation)
- **Search**: Use the search bar to find specific filaments
- **Filter**: Use the material dropdown to filter by filament type

### Tracking Usage

- Update the "Remaining Weight" field when editing a filament
- The progress bar shows how much filament is left
- Cards with less than 20% remaining are highlighted in red
- View total statistics at the top of the page

## Network Sharing

To share with roommates or others on your network:
Real 1. "$env:PATH += ";C:\Program Files\nodejs"; npm start"
1. Start the server (`npm start`)
2. Find your computer's IP address
3. Share the URL: `http://YOUR_IP_ADDRESS:3000`
4. Others can access it directly in their browsers

**Example:**
If your IP is `192.168.1.100`, share: `http://192.168.1.100:3000`

## Data Storage

- All data is stored in `data/filaments.json`
- Data persists between server restarts
- Automatic backup on each change
- No database setup required

## Keyboard Shortcuts

- **Ctrl/Cmd + N**: Add new filament
- **Ctrl/Cmd + D**: Toggle dark mode
- **Escape**: Close modal dialogs

## AMS Integration (Anycubic Kobra 2 Pro Ready)

### Automatic Filament Tracking
The system includes API endpoints for automatic integration with your 3D printer and AMS:

**Slicer Post-Processing Integration:**
- Automatically track filament usage after each print
- Smart filament matching by material and color
- Multi-material print support

**Print History Tracking:**
- See recent print jobs on each filament card
- Track usage patterns and consumption rates
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
├── package.json          # Project dependencies
├── server.js             # Express server with AMS APIs
├── data/                 # Data storage
│   └── filaments.json   # Filament inventory data
└── public/              # Web interface
    ├── index.html       # Main page with dark mode
    ├── styles.css       # Styling with theme support
    └── script.js        # Frontend logic + print history
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
- Ensure Node.js is installed: `node --version`
- Check if port 3000 is available
- Run `npm install` to install dependencies

### Can't Access from Other Devices
- Verify your computer's firewall allows connections on port 3000
- Ensure all devices are on the same network
- Double-check the IP address

### Data Not Saving
- Check file permissions in the `data/` directory
- Ensure the server has write access to the project folder

## Customization

### Changing the Port
Edit `server.js` and modify the `PORT` variable, or set the `PORT` environment variable:
```bash
PORT=8080 npm start
```

### Adding New Material Types
Edit the material options in both `index.html` and `script.js` to add custom filament types.

## Future Printer Integration

### When Your Kobra 2 Pro + AMS Arrives

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