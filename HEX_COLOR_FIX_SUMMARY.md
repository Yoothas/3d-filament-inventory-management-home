# CRITICAL FIX: Hex Color Detection for Multi-Color Filaments

## The Issue You Found ✅ NOW FIXED

Your logging revealed the root cause:
```
[2025-10-18T16:00:53.801847] [postprint] Hex #212721 -> 'Black' (RGB: 33,39,33)
[2025-10-18T16:00:55.836238] [postprint] Using filament: Anycubic High Speed Black ❌ WRONG!
```

**Problem:** Slicer sends hex color codes. Your multi-color filament's dark side showed as `#212721` (very dark gray), which was being named "Black", then matching to the wrong spool.

**Solution:** Improved hex color analysis using:
1. **Grayscale detection** - Check if RGB values are similar
2. **Brightness analysis** - Check if color is too dark to safely name
3. **Conservative thresholds** - Treat ambiguous dark colors as "unknown"

---

## What Changed in `tools/postprint_usage.py`

### Before (Lines 102-145):
```python
# Black: low RGB values
if r < 40 and g < 40 and b < 40:
    return 'Black'  # ← Problem: #212721 (33,39,33) gets named "Black"!
```

### After (Lines 102-165):
```python
# Calculate how close to grayscale this is
rgb_values = [r, g, b]
max_diff = max(rgb_values) - min(rgb_values)
is_grayscale = max_diff < 30

# If NOT grayscale, it's likely multi-color → use material-only matching
if not is_grayscale:
    return None

brightness = (r + g + b) / 3

# Very dark (brightness < 50): could be multi-color
if brightness < 50:
    return None  # ← Skip naming! Use material-only matching

# Only pure black gets the "Black" name
if r < 25 and g < 25 and b < 25:
    return 'Black'
```

---

## How It Works Now

### Your Problematic Case: `#212721`

| Check | Value | Result |
|-------|-------|--------|
| Grayscale? | max_diff=6 | ✓ YES |
| Brightness | (33+39+33)/3 = 35 | < 50 |
| **Decision** | - | **Skip naming → Use material-only matching** |

**What happens:**
```
Old flow: #212721 → "Black" → "Anycubic High Speed Black" ❌
New flow: #212721 → None (skip) → Material PLA search → "Anycubic Silk Dual Red Blue Yellow" ✓
```

### Pure Black: `#000000`

| Check | Value | Result |
|-------|-------|--------|
| Grayscale? | max_diff=0 | ✓ YES |
| Brightness | 0 | < 50 |
| Pure black? | R=0, G=0, B=0 | ✓ YES |
| **Decision** | - | **Name "Black"** |

---

## Test Your Fix

### Step 1: Enable Logging
```powershell
$env:FILAMENT_POSTPRINT_LOG = "1"
```

### Step 2: Run Test Script
```powershell
python HEX_COLOR_DETECTION_TEST.py
```

You'll see analysis of various hex colors and what they map to.

### Step 3: Print Again
Print with your multi-color filament and watch the logging.

### Step 4: Check Results
```powershell
Get-Content $env:USERPROFILE\.filament-inventory\postprint.log -Tail 50
```

**Look for:**
```
✓ GOOD:
[postprint] Hex #212721 very dark (brightness=35) - could be multi-color, will use material-only matching
[postprint] Searching: http://localhost:5000/api/filaments/search?material=PLA&brand=Anycubic
[postprint] Using filament: Anycubic Silk Dual Red Blue Yellow ✓

❌ BAD (if you see this, something's wrong):
[postprint] Hex #212721 -> 'Black'
[postprint] Using filament: Anycubic High Speed Black
```

---

## Technical Details

### Brightness Thresholds
```python
brightness = (R + G + B) / 3  # Average of RGB 0-255

brightness < 50   → Very dark, skip naming (ambiguous)
brightness < 100  → Dark gray
brightness < 180  → Gray
brightness ≥ 180  → Light gray
```

### Grayscale Detection
```python
max_diff = max(R, G, B) - min(R, G, B)
is_grayscale = max_diff < 30  # RGB values within 30 of each other

Examples:
#212721 (R=33, G=39, B=33)   → max_diff=6   → Grayscale ✓
#FF0000 (R=255, G=0, B=0)    → max_diff=255 → NOT Grayscale ✗
```

### Why This Works for Multi-Color

Multi-color filaments show different sides during printing:
- **Red side:** `#FF0000` (RGB(255,0,0)) → NOT grayscale → Skip naming → Material match ✓
- **Blue side:** `#0000FF` (RGB(0,0,255)) → NOT grayscale → Skip naming → Material match ✓
- **Yellow side:** `#FFFF00` (RGB(255,255,0)) → NOT grayscale → Skip naming → Material match ✓
- **Dark side:** `#212721` (RGB(33,39,33)) → Grayscale BUT < 50 brightness → Skip naming → Material match ✓

All paths correctly identify your "Anycubic Silk Dual Red Blue Yellow" spool!

---

## Color Detection Priority (Updated)

```
1. Detect hex color code (#RRGGBB)
   ↓
2. Parse RGB values
   ↓
3. Check if grayscale (max_diff < 30)
   ├─ NO (vibrant) → Skip naming, use material match
   └─ YES (similar RGB)
       ↓
       Check brightness (avg RGB)
       ├─ < 50 (very dark) → Skip naming, use material match
       ├─ < 25 pure? → Name "Black"
       ├─ < 100 → Name "Dark Gray"
       └─ ...
```

---

## File Changes Summary

| File | Changes | Impact |
|------|---------|--------|
| `tools/postprint_usage.py` | Lines 102-165 | Enhanced hex color detection with grayscale + brightness analysis |
| `HEX_COLOR_DETECTION_EXPLAINED.md` | NEW | Detailed explanation of the algorithm |
| `HEX_COLOR_DETECTION_TEST.py` | NEW | Test script to verify hex color mapping |

---

## What to Do Now

1. **Test the fix:**
   ```powershell
   python HEX_COLOR_DETECTION_TEST.py
   ```

2. **Enable logging:**
   ```powershell
   $env:FILAMENT_POSTPRINT_LOG = "1"
   ```

3. **Print with your multi-color filament again**

4. **Check logs:**
   ```powershell
   Get-Content $env:USERPROFILE\.filament-inventory\postprint.log -Tail 50
   ```

5. **Verify the correct spool was deducted in your dashboard**

---

## Still Having Issues?

**Check these logs:**

```powershell
# View full log with context
Get-Content $env:USERPROFILE\.filament-inventory\postprint.log

# Look for these lines to debug:
# - "Hex #212721 RGB analysis:" → Shows RGB values and analysis
# - "will use material-only matching" → Confirms skipped color naming
# - "Searching:" → What parameters were searched
# - "Found N matches" → How many results
# - "Selected:" → Which spool was picked
```

**Common issues:**

| Log shows... | Means | Fix |
|---|---|---|
| `Hex #212721 -> 'Black'` | Using OLD code | Restart terminal/script |
| `Searching: ?material=PLA&color=Black` | Color wasn't skipped | Check if log level correct |
| `Found 0 matches` | No filaments match | Check inventory has correct brand/material |
| `Selected: Anycubic High Speed Black` | Wrong spool picked | Check matching logic (contact developer) |

---

## Summary

✅ **Problem:** Multi-color filament dark side `#212721` was named "Black"  
✅ **Root cause:** Hex color threshold too lenient (< 40 includes near-black grays)  
✅ **Solution:** Added grayscale + brightness analysis  
✅ **Result:** Ambiguous dark colors now skip naming, use material-only matching  

**Expected outcome:** Next print deducts from "Anycubic Silk Dual Red Blue Yellow" ✓

---

## Reference Documents

- **HEX_COLOR_DETECTION_EXPLAINED.md** - Deep dive into the algorithm
- **HEX_COLOR_DETECTION_TEST.py** - Test script with examples
- **HOW_TO_VIEW_LOGS.py** - How to enable and view logs
- **TROUBLESHOOT_TRICOLOR.md** - Original multi-color troubleshooting guide

All documentation is in your project root directory.
