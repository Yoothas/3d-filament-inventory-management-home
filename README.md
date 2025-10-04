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
- **Escape**: Close modal dialogs

## Technical Details

### File Structure
```
3d-filament-inventory/
├── package.json          # Project dependencies
├── server.js             # Express server
├── data/                 # Data storage
│   └── filaments.json   # Filament inventory data
└── public/              # Web interface
    ├── index.html       # Main page
    ├── styles.css       # Styling
    └── script.js        # Frontend logic
```

### API Endpoints

- `GET /api/filaments` - Get all filaments
- `POST /api/filaments` - Add new filament
- `PUT /api/filaments/:id` - Update filament
- `DELETE /api/filaments/:id` - Delete filament

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

## Contributing

Feel free to customize this application for your specific needs. The code is well-commented and modular for easy modification.

## License

MIT License - Feel free to modify and distribute as needed.