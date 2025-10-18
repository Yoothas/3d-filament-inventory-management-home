# Auto-Deduct Troubleshooting Guide

## Quick Diagnosis

The auto-deduct feature has been tested and is **working correctly**. If it's not working for you, follow these steps:

### Step 1: Verify Server is Running

1. Check that the Flask server is running
2. Server should be on port **5000** (not 3000)
3. You should see this in the terminal:
   ```
   Running on http://127.0.0.1:5000
   Running on http://192.168.1.18:5000
   ```

### Step 2: Test the Script Manually

Run this command to test:
```bash
cd "d:\VSCode\Filament in python\3d-filament-inventory-management-home\tools"
python test_postprint.py
```

**Expected output:**
```
✅ Test PASSED - Auto-deduct script executed successfully!
```

If this works, the problem is in your slicer configuration.

### Step 3: Check Your Inventory

1. Open http://localhost:5000
2. Make sure you have at least one filament with:
   - Material: **PLA** (or whatever you're using)
   - Remaining weight > 0
3. Note the exact brand and color names in your inventory

### Step 4: Slicer Configuration

#### Recommended Command (Simplest):

Use the wrapper script in your slicer's post-processing settings:

```
"D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint-wrapper.bat"
```

**Important:** 
- Use the **full absolute path**
- Use **backslashes** (\) not forward slashes (/)
- Include the **quotes**
- Don't add any slicer variables like `{output_filepath}` - the slicer passes it automatically

#### Alternative Command (Direct Python):

```
python "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py"
```

### Step 5: Enable Logging

Before running a print, enable logging:

**Windows PowerShell:**
```powershell
$env:FILAMENT_POSTPRINT_LOG = "1"
```

**Windows Command Prompt:**
```cmd
set FILAMENT_POSTPRINT_LOG=1
```

**Or** edit `postprint-wrapper.bat` which already has logging enabled.

Then check the log file at:
```
C:\Users\YOUR_USERNAME\.filament-inventory\postprint.log
```

## Common Issues & Solutions

### Issue 1: "No matching filament found in inventory"

**Cause:** Your inventory brand/color doesn't match what's in the G-code

**Solutions:**

1. **Check what the slicer is sending:**
   - Enable logging
   - Check log file for lines like:
     ```
     Looking up filament for material='PLA' color='Clear' brand='Anycubic'
     ```

2. **Update your inventory to match:**
   - If slicer says "Anycubic Clear PLA", add a filament with:
     - Brand: ATA (the script auto-maps "Anycubic" → "ATA")
     - Color: Translucent (the script auto-maps "Clear" → "Translucent")
     - Material: PLA

3. **Or use fuzzy matching:**
   - The script tries multiple fallback strategies
   - Make sure you have ANY PLA filament with remaining weight > 0

### Issue 2: Script doesn't run at all

**Possible causes:**

1. **Python not in PATH**
   - Test: Run `python --version` in command prompt
   - Fix: Reinstall Python and check "Add to PATH"

2. **Wrong port number**
   - Server is on port 5000
   - Script default is now 5000
   - If using custom port, set environment variable:
     ```cmd
     set FILAMENT_SERVER_PORT=5000
     ```

3. **Slicer configuration error**
   - Use the wrapper script (`postprint-wrapper.bat`)
   - Check slicer's post-processing log for errors

### Issue 3: "Connection refused" or timeout

**Cause:** Script can't reach the server

**Solutions:**

1. **Verify server is running:**
   ```bash
   curl http://localhost:5000/api/filaments
   ```
   Or open http://localhost:5000 in browser

2. **Check firewall:**
   - Windows Firewall might be blocking connections
   - Add exception for Python

3. **Set server URL explicitly:**
   ```cmd
   set FILAMENT_SERVER_HOST=http://localhost:5000
   ```

### Issue 4: Script runs but weight doesn't update

**Possible causes:**

1. **Server not receiving request**
   - Check Flask terminal for log of POST request
   - Should see: `POST /api/filaments/XXXXX/use`

2. **Wrong filament selected**
   - Script picks first match
   - Check log: "Using filament: BRAND COLOR (MATERIAL) -> id=XXXXX"
   - Verify this is the correct spool

3. **Data file locked**
   - Close any programs that might have `data/filaments.json` open

## Testing Procedure

### Manual Test

1. **Create a test G-code file** (test.gcode):
   ```gcode
   ; filament_type = PLA
   ; filament_colour = Translucent
   ; filament_vendor = ATA
   ; filament used [g] = 5.0
   
   G28
   ; ... print code ...
   M84
   ```

2. **Run the script manually:**
   ```bash
   python tools/postprint_usage.py test.gcode
   ```

3. **Expected output:**
   ```
   [postprint] Using filament: ATA Translucent (PLA) -> id=XXXXX
   [postprint] Updated: used 5.0g, remaining XXXg
   ```

4. **Verify in web interface:**
   - Refresh http://localhost:5000
   - Check that the filament's remaining weight decreased by 5g
   - Check print history shows the new entry

### Slicer Integration Test

1. **Slice a small test model** (like a calibration cube)

2. **Add post-processing command:**
   ```
   "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint-wrapper.bat"
   ```

3. **Watch for output** in slicer's console/log

4. **Check the log file:**
   ```
   type %USERPROFILE%\.filament-inventory\postprint.log
   ```

## Configuration Checklist

- [ ] Flask server running on port 5000
- [ ] At least one filament in inventory with weight > 0
- [ ] Python installed and in PATH
- [ ] `requests` module installed (`pip install requests`)
- [ ] Slicer post-processing command set to wrapper script
- [ ] Used **full absolute path** in slicer
- [ ] Logging enabled (`FILAMENT_POSTPRINT_LOG=1`)
- [ ] Server URL correct if on different machine

## Environment Variables

Set these if needed:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FILAMENT_SERVER_PORT` | 5000 | Server port |
| `FILAMENT_SERVER_HOST` | `http://localhost:5000` | Full server URL |
| `FILAMENT_POSTPRINT_LOG` | (none) | `1` for default log, or full path |

**Set in PowerShell:**
```powershell
$env:FILAMENT_SERVER_PORT = "5000"
$env:FILAMENT_POSTPRINT_LOG = "1"
```

**Set in Command Prompt:**
```cmd
set FILAMENT_SERVER_PORT=5000
set FILAMENT_POSTPRINT_LOG=1
```

## Still Not Working?

1. **Run the test script:**
   ```bash
   python tools/test_postprint.py
   ```

2. **Check all logs:**
   - Flask server console output
   - Post-print log file
   - Slicer's post-processing log

3. **Verify filament data:**
   - Check `data/filaments.json` directly
   - Ensure IDs are strings
   - Ensure remainingWeight is a number

4. **Try with explicit parameters:**
   ```bash
   python tools/postprint_usage.py --used-g 5.0 --material PLA --color Translucent --brand ATA
   ```

## Debug Mode

For maximum verbosity:

1. **Enable logging:**
   ```cmd
   set FILAMENT_POSTPRINT_LOG=D:\debug.log
   ```

2. **Run Flask in debug mode** (already enabled)

3. **Use wrapper script** which shows all variables

4. **Check both logs:**
   - `D:\debug.log` - Post-print script log
   - Flask console - Server requests

## Success Indicators

When working correctly, you should see:

1. **In Flask terminal:**
   ```
   POST /api/filaments/XXXXX/use - 200
   ```

2. **In post-print log:**
   ```
   [timestamp] Using filament: ATA Translucent (PLA) -> id=XXXXX
   [timestamp] Updated: used 15.45g, remaining 754.55g
   ```

3. **In web interface:**
   - Filament's remaining weight decreases
   - New entry in print history
   - Progress bar updates

---

## Quick Fix Checklist

Try these in order:

1. ✅ Server running on port 5000? → `python app.py`
2. ✅ Script port matches? → Check DEFAULT_PORT = 5000 in script
3. ✅ Inventory has matching filament? → Add one if needed
4. ✅ Using wrapper script? → Use `postprint-wrapper.bat`
5. ✅ Logging enabled? → Set FILAMENT_POSTPRINT_LOG=1
6. ✅ Test script passes? → Run `python tools/test_postprint.py`

If all checked and still failing, share:
- Flask console output
- Post-print log contents
- Slicer post-processing log
- One filament entry from your inventory
