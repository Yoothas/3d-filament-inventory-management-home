# Quick Start Guide - Filament Auto-Deduct

## ✅ What You Need Running

For the post-print script to work, you need:

1. **Flask Server** - Running on port 5000
2. **Wrapper Script** - Created at `C:\3DPrint\slicer-postprint.bat`
3. **Slicer Configuration** - Set to use the wrapper script

## 🚀 Step-by-Step Setup

### Step 1: Start the Flask Server

**Option A: Double-Click** (Easiest)
```
Double-click: start-server.bat
```

**Option B: PowerShell**
```powershell
cd "D:\VSCode\Filament in python\3d-filament-inventory-management-home"
python app.py
```

**Option C: New Window**
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\VSCode\Filament in python\3d-filament-inventory-management-home'; python app.py"
```

**✅ You should see:**
```
3D Filament Inventory Server running on port 5000
Access the application at:
  Local: http://localhost:5000
```

**🌐 Test it:** Open http://localhost:5000 in your browser

---

### Step 2: Verify Wrapper Script Exists

```powershell
Test-Path "C:\3DPrint\slicer-postprint.bat"
```

**Should return:** `True`

**If False, create it:**
```powershell
New-Item -Path "C:\3DPrint" -ItemType Directory -Force
@"
@echo off
"D:\python 3.10\python.exe" "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py" %*
"@ | Out-File -FilePath "C:\3DPrint\slicer-postprint.bat" -Encoding ASCII
```

---

### Step 3: Configure Anycubic Slicer

1. **Open Anycubic Slicer**

2. **Find Post-Processing Settings:**
   - Look in: **Settings** → **Post-processing Scripts**
   - Or: **Preferences** → **Scripts**
   - Or: **Machine Settings** → **Post-print Command**

3. **Enter this EXACT command:**
   ```
   C:\3DPrint\slicer-postprint.bat "{output_filepath}"
   ```

4. **Save** the settings

---

### Step 4: Test with a Print

1. **Slice a small test model** (a cube or benchy)

2. **Watch the slicer output** for any errors

3. **Check your inventory:**
   - Open: http://localhost:5000
   - Find the filament you used
   - Check if weight was deducted
   - Look at the print history section

---

## 🧪 Manual Testing

### Test 1: Verify Wrapper Works

```powershell
& "C:\3DPrint\slicer-postprint.bat" --help
```

**Expected:** Help message showing script options

---

### Test 2: Check Flask Server

```powershell
Test-NetConnection -ComputerName localhost -Port 5000 -InformationLevel Quiet
```

**Expected:** `True`

**If False:**
- Flask server is not running
- Start it using Step 1 above

---

### Test 3: Search API Test

```powershell
# Test if Flask can find your filaments
Invoke-WebRequest -Uri "http://localhost:5000/api/filaments/search?material=PLA&color=Black&brand=Anycubic" | Select-Object -ExpandProperty Content
```

**Expected:** JSON with matching filaments

---

## 🐛 Troubleshooting

### Error: "Post-processing script failed. Error code: 2"

**Cause:** One of these issues:
1. Wrapper script doesn't exist
2. Python path is wrong
3. Post-print script path is wrong
4. Flask server not running

**Fix:**

```powershell
# 1. Verify wrapper exists
Test-Path "C:\3DPrint\slicer-postprint.bat"

# 2. Verify Python exists
Test-Path "D:\python 3.10\python.exe"

# 3. Verify post-print script exists
Test-Path "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py"

# 4. Check Flask server
Test-NetConnection -ComputerName localhost -Port 5000 -InformationLevel Quiet
```

---

### Error: "No matching filament found"

**Cause:** Script can't find a filament matching the print

**What the script looks for:**
- Material: PLA (from G-code)
- Color: Black (from hex #212721)
- Brand: Anycubic (from G-code)

**Your inventory has:**
- **Anycubic High Speed Black PLA** ✅ Should match!

**Fix:** The script uses partial matching, so "Anycubic" should match "Anycubic High Speed"

**Check your inventory:**
```powershell
# Open in browser
start http://localhost:5000

# Or list via API
Invoke-WebRequest -Uri "http://localhost:5000/api/filaments" | Select-Object -ExpandProperty Content
```

---

### Flask Server Keeps Stopping

**Solution:** Use the startup batch file

1. **Double-click:** `start-server.bat`
2. **Keep the window open** (don't close it)
3. The server will run until you close the window

---

### Wrapper Script Says "Python not found"

**Fix: Update wrapper with full Python path**

Edit `C:\3DPrint\slicer-postprint.bat`:
```batch
@echo off
"D:\python 3.10\python.exe" "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py" %*
```

---

## 📝 Expected Workflow

### When Everything Works:

1. **You slice a model in Anycubic Slicer**
   - Slicer generates G-code
   - Slicer calls: `C:\3DPrint\slicer-postprint.bat "{gcode_file}"`

2. **Wrapper script runs**
   - Calls Python with the post-print script
   - Script parses G-code file
   - Finds: Material, Color, Brand, Weight used

3. **Script calls Flask API**
   - Searches for matching filament
   - Deducts the weight
   - Updates print history

4. **Result in inventory:**
   - Filament weight reduced
   - Print history updated
   - If 0g remaining → Auto-archived!

---

## 🎯 Current Setup Checklist

- [✅] Wrapper script created: `C:\3DPrint\slicer-postprint.bat`
- [✅] Post-print script exists: `tools/postprint_usage.py`
- [✅] Python installed: `D:\python 3.10\python.exe`
- [ ] Flask server running on port 5000
- [ ] Slicer configured with wrapper command
- [ ] Tested with a print

---

## 📚 Next Steps

1. **Keep Flask server running** in a dedicated window
2. **Try printing something small**
3. **Watch the slicer output** for any errors
4. **Check your inventory** after the print

---

## 🔗 Related Documentation

- [README.md](README.md) - Main documentation
- [FIXING_SLICER_PATH.md](FIXING_SLICER_PATH.md) - Detailed path fix guide
- [ARCHIVE_FEATURE.md](ARCHIVE_FEATURE.md) - Auto-archive feature
- [TROUBLESHOOTING_SLICER.md](TROUBLESHOOTING_SLICER.md) - Slicer issues

---

## 💡 Pro Tips

### Keep Server Running Automatically

**Create a Windows scheduled task:**
```powershell
# Run at startup
$action = New-ScheduledTaskAction -Execute "python" -Argument "app.py" -WorkingDirectory "D:\VSCode\Filament in python\3d-filament-inventory-management-home"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "FilamentInventoryServer" -Description "3D Filament Inventory Flask Server"
```

### Quick Restart Script

Create `restart-server.bat`:
```batch
@echo off
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *app.py*"
timeout /t 2
start python app.py
```

### Enable Logging

```powershell
$env:FILAMENT_POSTPRINT_LOG = "1"
& "C:\3DPrint\slicer-postprint.bat" "{gcode_file}"
```

Check log: `%USERPROFILE%\.filament-inventory\postprint.log`

---

**Ready to test?** Slice a small model and watch the magic happen! ✨
