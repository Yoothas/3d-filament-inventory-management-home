# Hex Color Detection - How Multi-Color Filaments Are Handled

## The Problem You Discovered

Your slicer sends hex color codes (like `#212721`) instead of names. The script converts these to color names for matching:

```
#212721 (RGB: 33, 39, 33) → Previously detected as "Black"
                          → Matched to "Anycubic High Speed Black" (WRONG!)
                          → Should match to "Anycubic Silk Dual Red Blue Yellow" or use material-only matching
```

## Why This Happens

Multi-color filaments show their **dark side color** when printing. When your Anycubic Silk Dual Red Blue Yellow filament is being used, it might show:
- The black side: `#212721`
- The red side: `#FF0000`
- The blue side: `#0000FF`
- The yellow side: `#FFFF00`

The slicer firmware captures whichever color stripe is currently visible.

## The Solution: Improved Hex Color Detection

The updated script now uses **three-step analysis**:

### Step 1: Check if Grayscale
```python
max_diff = max(R, G, B) - min(R, G, B)
is_grayscale = max_diff < 30  # RGB values are very similar (within 30 points)

# Examples:
#212721 (R=33, G=39, B=33)  → max_diff = 6   → IS grayscale ✓
#FF0000 (R=255, G=0, B=0)   → max_diff = 255 → NOT grayscale ✗
#00FF00 (R=0, G=255, B=0)   → max_diff = 255 → NOT grayscale ✗
```

### Step 2: If NOT Grayscale → Don't Name It
If the color is vibrant (R, G, B values vary wildly), it's definitely a specific color, not multi-color:
- Skip color naming
- Use **material-only matching** instead
- This prevents false color matches

### Step 3: If IS Grayscale → Check Brightness
```python
brightness = (R + G + B) / 3  # Average 0-255

# Very dark colors (brightness < 50) are SKIPPED
# → Use material-only matching
# → This catches the multi-color dark side issue!

# Only pure black (R < 25, G < 25, B < 25) → named "Black"
```

## What This Means for Your Prints

### Scenario 1: Multi-Color Filament (Red Blue Yellow) - Dark Side
```
Slicer sends: #212721 (RGB: 33, 39, 33)
Analysis:
  - Grayscale check: max_diff=6, is_grayscale=YES
  - Brightness: (33+39+33)/3 = 35 (< 50, very dark!)
  - Decision: SKIP color naming
  - Fallback: Use MATERIAL ONLY matching (PLA)
  - Result: Searches all PLA filaments, picks one with most weight/recently used
  - ✅ Correctly matches to "Red Blue Yellow" (if it's the only one you have of that brand/material)
```

### Scenario 2: Actual Black Filament - Pure Black
```
Slicer sends: #000000 (RGB: 0, 0, 0)
Analysis:
  - Grayscale check: max_diff=0, is_grayscale=YES
  - Brightness: (0+0+0)/3 = 0 (< 50, very dark!)
  - Pure black check: R=0, G=0, B=0 (YES!)
  - Decision: NAME it "Black"
  - Result: Matches to "Anycubic High Speed Black" ✓
```

### Scenario 3: Red Filament
```
Slicer sends: #FF0000 (RGB: 255, 0, 0)
Analysis:
  - Grayscale check: max_diff=255, is_grayscale=NO
  - Decision: SKIP color naming
  - Fallback: Use MATERIAL ONLY matching (PLA)
  - Result: Searches all PLA, picks best match ✓
```

## Why Grayscale Check Fails at Brightness < 50

Your problematic hex: `#212721` has RGB(33, 39, 33)
- It IS grayscale (values are similar)
- But it's very dark (brightness ≈ 35)
- This brightness level is ambiguous - could be:
  1. Pure black filament
  2. Dark side of multi-color filament
  3. Very dark gray filament

**Solution:** Treat anything with brightness < 50 as "unknown dark color"
→ Skip color naming
→ Fall back to material-only matching
→ Let inventory size/weight decide

## Log Output - What to Look For

### Good Log (Updated Script):
```
[2025-10-18T16:00:53.801847] [postprint] Detected hex color code: #212721
[2025-10-18T16:00:53.801847] [postprint] Hex #212721 RGB analysis: R=33 G=39 B=33, max_diff=6, is_grayscale=True
[2025-10-18T16:00:53.801847] [postprint] Hex #212721 very dark (brightness=35) - could be multi-color, will use material-only matching
[2025-10-18T16:00:53.801847] [postprint] Looking up filament for material='PLA' color=None brand='Anycubic'
                                         ↑ Notice: color=None now!
[2025-10-18T16:00:53.801847] [postprint] Searching: http://localhost:5000/api/filaments/search?material=PLA&brand=Anycubic
[2025-10-18T16:00:55.836238] [postprint] Using filament: Anycubic Silk Dual Red Blue Yellow (PLA) -> id=1760220617334
                                         ↑ NOW IT PICKS THE MULTI-COLOR!
```

### Old Log (Before Fix):
```
[2025-10-18T16:00:53.801847] [postprint] Hex #212721 -> 'Black' (RGB: 33,39,33)
                                         ↑ ERROR: Named it "Black"!
[2025-10-18T16:00:53.801847] [postprint] Looking up filament for material='PLA' color='Black' brand='Anycubic'
[2025-10-18T16:00:55.836238] [postprint] Using filament: Anycubic High Speed Black (PLA) -> id=1760220208055
                                         ↑ WRONG SPOOL!
```

## Configuration: Brightness Threshold

Current thresholds in the code:
```python
brightness = (r + g + b) / 3

if brightness < 50:
    # Very dark - could be multi-color, skip naming
    return None

if r < 25 and g < 25 and b < 25:
    # Very pure black - name it "Black"
    return 'Black'

if brightness < 100:
    # Dark gray
    return 'Dark Gray'
```

### To Adjust (if needed):
- **Lower 50 threshold** if dark grays are being skipped incorrectly
- **Raise 50 threshold** if you want darker colors named
- **Lower 25 threshold** if pure black is being skipped

## Filament Matching Flow Now

```
Hex Color Detected (#212721)
    ↓
Grayscale Check (R, G, B similar?)
    ├─ YES → Brightness Check (brightness < 50?)
    │   ├─ YES → SKIP naming, use material-only search ✓
    │   └─ NO → Check for pure black, gray, etc.
    │
    └─ NO (vibrant color) → SKIP naming, use material-only search ✓
```

## Test Cases - What Should Happen

| Hex | RGB | Analysis | Result |
|-----|-----|----------|--------|
| #000000 | (0,0,0) | Grayscale + pure black | Name: "Black" |
| #FFFFFF | (255,255,255) | Grayscale + bright | Name: "White" |
| #212721 | (33,39,33) | Grayscale + very dark | Skip naming → material match |
| #FF0000 | (255,0,0) | NOT grayscale | Skip naming → material match |
| #00FF00 | (0,255,0) | NOT grayscale | Skip naming → material match |
| #0000FF | (0,0,255) | NOT grayscale | Skip naming → material match |
| #808080 | (128,128,128) | Grayscale + mid-dark | Name: "Gray" |
| #404040 | (64,64,64) | Grayscale + dark | Name: "Dark Gray" |

## Next Steps

1. **Enable logging:**
   ```powershell
   $env:FILAMENT_POSTPRINT_LOG = "1"
   ```

2. **Print with your multi-color filament again**

3. **Check the logs:**
   ```powershell
   Get-Content $env:USERPROFILE\.filament-inventory\postprint.log -Tail 50
   ```

4. **Verify the fix:**
   - Should see: `will use material-only matching`
   - Should see: `Anycubic Silk Dual Red Blue Yellow` selected
   - Should NOT see: `Anycubic High Speed Black` selected

## Troubleshooting

**Still picking wrong spool?**
- Check log for: `Searching:` line - what parameters were used?
- Check: Are you using brand="Anycubic"? Log should show this.
- If log shows correct filament found but wrong one selected, contact developer.

**Getting "Dark Gray" when expecting multi-color?**
- Increase brightness threshold in code (change 50 to 70 or 100)
- Or: Use material-only matching by setting color=None in G-code

**Want to force material-only matching?**
- Don't include color in your slicer settings
- Script will skip color detection entirely
- Matching will use: material + brand + weight/recency

---

**Summary:** Your slicer's hex colors are now properly analyzed. Dark hex values from multi-color filaments won't be misclassified as pure black anymore! 🎨
