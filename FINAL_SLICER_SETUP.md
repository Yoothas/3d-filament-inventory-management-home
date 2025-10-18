# Complete Slicer Setup Guide

## Quick Setup (2 Steps)

### Step 1: Ensure Flask Server is Running

```bash
# Start the server
python app.py

# Or use the batch file
start-server.bat
```

Server must be accessible at http://localhost:5000

### Step 2: Configure Anycubic Slicer

1. Open **Anycubic Slicer**
2. Go to: **Machine Settings** → **Scripts** → **Post-print script**
3. Enter this command (NO file path needed):

```
C:\3DPrint\slicer-postprint.bat
```

4. **Save** the settings

That's it! The script will automatically find and process G-code files.

---

## How It Works

### Automatic G-code Detection

When you slice a model:

1. **Slicer generates G-code** → Saved to temp folder
2. **Slicer calls wrapper script** → `C:\3DPrint\slicer-postprint.bat`
3. **Script searches** → Finds most recent `.gcode` file (within last 5 minutes)
4. **Script parses G-code** → Extracts:
   - Material (PLA, PETG, etc.)
   - Color (from hex code like #212721 → Black)
   - Brand (Anycubic, etc.)
   - Weight used (126.84g, etc.)
5. **Script calls Flask API** → Searches for matching filament
6. **Script deducts weight** → Updates inventory and print history
7. **Auto-archive if empty** → Spools with 0g automatically archived

### Smart Filament Matching

The script uses a scoring system to find the best match:

| Criteria | Points | Example |
|----------|--------|---------|
| Exact color match | +100 | "Black" == "Black" |
| Partial color match | +50 | "Black" in "Black Red" |
| Brand substring | +30 | "Anycubic" in "Anycubic High Speed" |
| Recently used | +20 | Has `lastUsed` timestamp |
| High remaining weight | +10 | > 1000g remaining |

**Example:**
- G-code shows: PLA, Black, Anycubic
- Inventory has:
  - "Anycubic High Speed Black PLA" (4347g) ✅ **Best Match** (170 points)
  - "Anycubic Silk Dual Black Red PLA" (1000g) - Partial color (100 points)
  - "Anycubic Silk Dual Black Green PLA" (1000g) - Partial color (100 points)

Script selects the first one!

---

## Troubleshooting

### Error: "Post-processing script failed. Error code: 2"

**Cause:** Slicer can't find or execute the wrapper script

**Solutions:**

1. **Verify wrapper exists:**
   ```powershell
   Test-Path "C:\3DPrint\slicer-postprint.bat"
   ```
   Should return: `True`

2. **If not, create it:**
   ```powershell
   New-Item -Path "C:\3DPrint" -ItemType Directory -Force
   @"
   @echo off
   "D:\python 3.10\python.exe" "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py" %*
   "@ | Out-File -FilePath "C:\3DPrint\slicer-postprint.bat" -Encoding ASCII
   ```

3. **Update paths if needed:**
   - Python path: `D:\python 3.10\python.exe`
   - Project path: `D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py`

---

### Error: "No G-code file found"

**Cause:** Script can't find recent G-code files

**Solutions:**

1. **Check temp folder:**
   ```powershell
   explorer "$env:LOCALAPPDATA\Temp\anycubicslicer_model"
   ```

2. **File too old:**
   - Script only processes files modified in last 5 minutes
   - Try slicing again

3. **Manual test:**
   ```powershell
   # Find a recent G-code
   $gcode = Get-ChildItem "$env:LOCALAPPDATA\Temp\anycubicslicer_model" -Recurse -Filter "*.gcode" | Select-Object -First 1
   
   # Test the script
   & "C:\3DPrint\slicer-postprint.bat" $gcode.FullName
   ```

---

### Error: "No matching filament found"

**Cause:** Script found G-code but can't match to inventory

**Check:**

1. **Open inventory:** http://localhost:5000

2. **Verify you have a filament with:**
   - Material: PLA (or whatever you're printing)
   - Color: Black (or whatever color)
   - Brand: Anycubic (or whatever brand)

3. **Ensure filament is active:**
   - Not archived
   - Remaining weight > 0g

4. **Test search API:**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5000/api/filaments/search?material=PLA&color=Black&brand=Anycubic"
   ```

**Common issues:**
- Brand mismatch: "Anycubic" vs "Anycubic High Speed" → Script handles this!
- Color mismatch: Check if hex code mapping is correct
- Archived spool: Unarchive it first

---

### Flask Server Not Running

**Symptoms:**
- Script runs but no inventory update
- "Connection refused" errors

**Fix:**

1. **Check if running:**
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 5000 -InformationLevel Quiet
   ```

2. **Start the server:**
   ```powershell
   cd "D:\VSCode\Filament in python\3d-filament-inventory-management-home"
   python app.py
   ```

3. **Keep window open!**

4. **Verify in browser:** http://localhost:5000

---

## Testing

### Test 1: Wrapper Script Works

```powershell
& "C:\3DPrint\slicer-postprint.bat" --help
```

**Expected:** Help message showing script options

---

### Test 2: Flask Server Running

```powershell
Test-NetConnection -ComputerName localhost -Port 5000 -InformationLevel Quiet
```

**Expected:** `True`

---

### Test 3: Auto-Find G-code

```powershell
& "C:\3DPrint\slicer-postprint.bat"
```

**Expected output (if you recently sliced):**
```
[postprint] No G-code file provided, searching for recent files...
[postprint] Found recent G-code: ...\.34008.2.gcode (modified 106s ago)
[postprint] Found ACTUAL usage in footer: 126.84g
[postprint] Hex #212721 -> 'Black' (RGB: 33,39,33)
[postprint] Using filament: Anycubic High Speed Black (PLA)
[postprint] Updated: used 126.84g, remaining 3966.77g
```

---

### Test 4: Search API

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/filaments/search?material=PLA&color=Black&brand=Anycubic" | ConvertTo-Json -Depth 5
```

**Expected:** JSON with matching filaments

---

## Advanced Configuration

### Enable Logging

```powershell
$env:FILAMENT_POSTPRINT_LOG = "1"
& "C:\3DPrint\slicer-postprint.bat"
```

**Log location:** `%USERPROFILE%\.filament-inventory\postprint.log`

---

### Custom Flask Server URL

If Flask is on a different machine:

```powershell
$env:FILAMENT_SERVER_HOST = "http://192.168.1.18:5000"
& "C:\3DPrint\slicer-postprint.bat"
```

---

### Keep Flask Server Running

**Option 1: Dedicated Window**
```powershell
Start-Process powershell -ArgumentList "-NoExit","-Command","cd 'D:\VSCode\Filament in python\3d-filament-inventory-management-home'; python app.py"
```

**Option 2: Task Scheduler (Auto-start on boot)**
```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "app.py" -WorkingDirectory "D:\VSCode\Filament in python\3d-filament-inventory-management-home"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "FilamentInventoryServer" -Description "3D Filament Inventory Flask Server"
```

---

## Success Checklist

Before slicing your first print:

- [ ] Wrapper script exists: `C:\3DPrint\slicer-postprint.bat`
- [ ] Flask server running: http://localhost:5000 accessible
- [ ] Slicer configured: `C:\3DPrint\slicer-postprint.bat` (no arguments)
- [ ] Settings saved in slicer
- [ ] At least one filament in inventory (not archived, weight > 0)
- [ ] Tested manually: `& "C:\3DPrint\slicer-postprint.bat"`

After slicing a test print:

- [ ] No error messages in slicer
- [ ] Filament weight decreased in inventory
- [ ] Print history shows new entry
- [ ] Last used date updated

---

## Expected Behavior

### When Working Correctly:

1. **You slice a model** in Anycubic Slicer
2. **Slicer shows no errors**
3. **Check inventory at** http://localhost:5000
4. **Filament weight decreased** by the amount used
5. **Print history updated** with new entry
6. **If 0g remaining** → Automatically archived! 📦

### Terminal Output (Flask):

```
3D Filament Inventory Server running on port 5000
Access the application at:
  Local: http://localhost:5000
  
127.0.0.1 - - [18/Oct/2025 15:20:08] "GET /api/filaments/search?material=PLA&color=Black&brand=Anycubic HTTP/1.1" 200 -
127.0.0.1 - - [18/Oct/2025 15:20:08] "POST /api/filaments/1760220208055/use HTTP/1.1" 200 -
```

---

## Tips

1. **Keep Flask running** in a dedicated window during printing sessions
2. **Check inventory** before and after prints to verify auto-deduction
3. **Enable logging** if you encounter issues
4. **Backup data** regularly: `data/filaments.json`
5. **Auto-archive empty spools** to keep inventory clean

---

## Related Documentation

- **README.md** - Main documentation
- **QUICK_START.md** - Quick start guide
- **TROUBLESHOOTING.md** - Detailed troubleshooting

---

**Last Updated:** October 18, 2025  
**Status:** ✅ Tested and Working  
**Test Results:** Successfully deducted 126.84g from Anycubic High Speed Black PLA
