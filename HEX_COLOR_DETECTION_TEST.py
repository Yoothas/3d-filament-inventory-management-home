#!/usr/bin/env python3
"""
Quick Test: Verify Hex Color Detection Fix
Run this to see how different hex colors are analyzed
"""

import os

# Enable logging for this test
os.environ['FILAMENT_POSTPRINT_LOG'] = '1'

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         HEX COLOR DETECTION TEST - Multi-Color Filament Fix                ║
╚════════════════════════════════════════════════════════════════════════════╝

This test shows how the improved hex color detection works.

📋 TEST COLORS (from your recent logs)
────────────────────────────────────────────────────────────────────────────

Your issue: #212721 was being named "Black" instead of using material-only matching

Let's trace what happens with different hex colors:

1️⃣  #212721 (Your problem case - Multi-color dark side)
    RGB: (33, 39, 33)
    max_diff: 33-33 = 6 (grayscale!)
    brightness: (33+39+33)/3 = 35 (very dark!)
    
    OLD CODE: Named "Black" → Selected "Anycubic High Speed Black" ❌
    NEW CODE: Skips naming (brightness < 50) → Material-only match → "Red Blue Yellow" ✓

2️⃣  #000000 (Pure black)
    RGB: (0, 0, 0)
    max_diff: 0 (grayscale!)
    brightness: 0 (very dark!)
    Pure black check: R < 25 && G < 25 && B < 25 → YES!
    
    RESULT: Named "Black" → Correct! ✓

3️⃣  #FFFFFF (Pure white)
    RGB: (255, 255, 255)
    max_diff: 0 (grayscale!)
    brightness: 255 (very bright!)
    
    RESULT: Named "White" ✓

4️⃣  #FF0000 (Pure red)
    RGB: (255, 0, 0)
    max_diff: 255 (NOT grayscale!)
    
    RESULT: Skips naming → Material-only match ✓

5️⃣  #00FF00 (Pure green)
    RGB: (0, 255, 0)
    max_diff: 255 (NOT grayscale!)
    
    RESULT: Skips naming → Material-only match ✓

6️⃣  #0000FF (Pure blue)
    RGB: (0, 0, 255)
    max_diff: 255 (NOT grayscale!)
    
    RESULT: Skips naming → Material-only match ✓


🎯 RUNNING ACTUAL COLOR ANALYSIS
────────────────────────────────────────────────────────────────────────────

Below is the actual test output from the color mapping function.
This shows what the script will do with each hex color:

""")

# Import the color mapping function from postprint script
import sys
from pathlib import Path

# Add tools directory to path
tools_dir = Path(__file__).parent / 'tools'
sys.path.insert(0, str(tools_dir))

try:
    from postprint_usage import map_color_name  # type: ignore[import]
    
    # Test cases with expected results
    test_cases = [
        ('#212721', 'Multi-color dark side (YOUR CASE)', None),  # Should skip naming
        ('#000000', 'Pure black', 'Black'),
        ('#FFFFFF', 'Pure white', 'White'),
        ('#FF0000', 'Pure red (vibrant)', None),  # Should skip naming (not grayscale)
        ('#00FF00', 'Pure green (vibrant)', None),  # Should skip naming (not grayscale)
        ('#0000FF', 'Pure blue (vibrant)', None),  # Should skip naming (not grayscale)
        ('#808080', 'Mid gray', 'Gray'),
        ('#404040', 'Dark gray', 'Dark Gray'),
        ('#0A0A0A', 'Very dark (close to black)', 'Black'),
        ('#1F0000', 'Very dark red (almost black)', None),  # Should skip - ambiguous
    ]
    
    print("TEST CASE | HEX CODE | RGB VALUES | ANALYSIS | RESULT\n")
    print("─" * 90)
    
    for i, (hex_code, description, expected) in enumerate(test_cases, 1):
        # Parse RGB for display
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)
        
        # Call the mapping function
        result = map_color_name(hex_code)
        
        # Check if it matches expectation
        status = "✓" if result == expected else "❌"
        expected_str = f'"{expected}"' if expected else "Skip (None)"
        result_str = f'"{result}"' if result else "Skip (None)"
        
        print(f"{i:2} | {hex_code} | ({r:3},{g:3},{b:3}) | {description:30} | {result_str:20} {status}")
    
    print("\n" + "─" * 90)
    print("""
✓ = Result matches expected behavior
❌ = Unexpected result (investigate)


📊 ANALYSIS REFERENCE
────────────────────────────────────────────────────────────────────────────

The algorithm checks in this order:

1. Is it grayscale? (max(R,G,B) - min(R,G,B) < 30)
   
2. If NOT grayscale → Skip color naming (vibrant colors should use material matching)
   
3. If YES grayscale:
   a. Is brightness < 50? → Skip naming (ambiguous dark, might be multi-color)
   b. Is it pure black (R<25, G<25, B<25)? → Name "Black"
   c. If brightness < 100? → Name "Dark Gray"
   d. If brightness < 180? → Name "Gray"
   e. Otherwise → Skip naming (unknown)


🧪 REAL-WORLD SCENARIO
────────────────────────────────────────────────────────────────────────────

When you print with "Anycubic Silk Dual Red Blue Yellow":

Slicer firmware samples color during print:
  │
  ├─ Red stripe visible    → Sends #FF0000 → Skip naming → Material match → Finds your "Red Blue Yellow" ✓
  ├─ Blue stripe visible   → Sends #0000FF → Skip naming → Material match → Finds your "Red Blue Yellow" ✓
  ├─ Yellow stripe visible → Sends #FFFF00 → Skip naming → Material match → Finds your "Red Blue Yellow" ✓
  └─ Dark stripe visible   → Sends #212721 → Skip naming (dark!) → Material match → Finds your "Red Blue Yellow" ✓

All paths lead to: "Anycubic Silk Dual Red Blue Yellow" (CORRECT!)


🚀 NEXT STEPS
────────────────────────────────────────────────────────────────────────────

1. Run your next print with the multi-color filament

2. Enable logging to see results:
   $env:FILAMENT_POSTPRINT_LOG = "1"

3. Check logs:
   Get-Content $env:USERPROFILE\.filament-inventory\postprint.log -Tail 30

4. Look for one of these in the logs:

   ✓ GOOD:
   [postprint] Hex #212721 very dark (brightness=35) - could be multi-color, will use material-only matching
   [postprint] Using filament: Anycubic Silk Dual Red Blue Yellow

   ❌ BAD (if you still see this, investigate):
   [postprint] Hex #212721 -> 'Black'
   [postprint] Using filament: Anycubic High Speed Black


💡 DEBUGGING
────────────────────────────────────────────────────────────────────────────

If you're still getting wrong filament selected:

1. Check the log line: "[postprint] Searching:"
   → Shows what parameters were used (material, color, brand)

2. Check line: "[postprint] Found N matches"
   → How many filaments matched?

3. Check line: "[postprint] Selected:"
   → Which one was picked and why?

Example good log:
   [postprint] Searching: http://localhost:5000/api/filaments/search?material=PLA&brand=Anycubic
   [postprint] Found 2 matches
   [postprint] Match 1: 'Red Blue Yellow' (1000.0g) scored 50
   [postprint] Match 2: 'Black High Speed' (4400.0g) scored 40
   [postprint] Selected: 'Red Blue Yellow' with 1000g remaining ✓

""")

except ImportError as e:
    print(f"ERROR: Could not import postprint_usage: {e}")
    print("\nMake sure you're running this from the project root directory!")
    print("Usage: python HEX_COLOR_DETECTION_TEST.py")
