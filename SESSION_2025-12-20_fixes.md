# Golf Handicap System - Session Dec 20, 2025

## Overview
Critical bug fixes after discovering yesterday's round (Dec 19) wasn't being recorded. Multiple parsing issues identified and resolved, AI commentary restored after accidental removal.

---

## CRITICAL: File Confusion Issue

**Problem**: Two versions of lambda_function existed:
- `lambda_function.py` - FULL version with AI commentary, weather, all features (936 lines)
- `lambda_function_aws.py` - STRIPPED version without AI/weather (489 lines)

During debugging, I was editing `lambda_function_aws.py` and accidentally deployed it, removing AI commentary.

**Solution**: 
- Consolidated all fixes back into `lambda_function.py` (the authoritative version)
- `build_lambda_package.ps1` always uses `lambda_function.py`
- Going forward: ONLY edit `lambda_function.py`, ignore `lambda_function_aws.py`

---

## Issues Found and Fixed

### 1. Round Not Being Saved

**Issue**: Dec 19, 2025 round not recorded - Lambda returning last week's summary instead.

**Root Cause**: iOS Shortcut not sending `"action"` parameter, just `{"url": "..."}`. Lambda defaulted to `get_summary` instead of `add_round`.

**Solution**: Added auto-detection in `lambda_handler()`:
```python
# Auto-detect action if URL is provided without explicit action
action = body.get('action')
if not action and body.get('url'):
    action = 'add_round'
    print(f"Auto-detected action=add_round from URL")
```

**File**: `lambda_function.py` - `lambda_handler()` function

---

### 2. Date Parsing Failed

**Issue**: Tag Heuer Golf now includes timestamps in dates: "Friday December 19, 2025 20:20"

**Previous Parsing**: Only handled "Friday December 19, 2025"

**Solution**: Strip time suffix before parsing:
```python
# Remove time suffix if present (e.g., " 20:53")
date_str_clean = re.sub(r'\s+\d{2}:\d{2}$', '', date_str_clean)
```

**File**: `lambda_function.py` - `parse_tag_heuer_url()` function

---

### 3. Wrong Scores Extracted

**Issue**: Getting Putts values (3-5) instead of Stableford points (10 pts showing as 55).

**Root Cause**: Tag Heuer's 18-hole scorecard has 12 recap cells per player:
```
[Out_score, In_score, Total_score,      # indices 0-2
 Out_putts, In_putts, Total_putts,       # indices 3-5
 Out_hcp, In_hcp, Total_hcp,             # indices 6-8
 Out_stableford, In_stableford, Total_stableford]  # indices 9-11
```

**Previous Code**: Used indices [3,4,5] (putts)
**Fixed Code**: Use indices [9,10,11] (stableford)

```python
out_stableford = recap_values[9]
in_stableford = recap_values[10]
```

**File**: `lambda_function.py` - `parse_tag_heuer_url()` function

---

### 4. Player Name Extraction Failed

**Issue**: HTML structure changed - player names now in grandparent div, not directly in text.

**Solution**: Get full text from grandparent element:
```python
grandparent = player_section.parent.parent if player_section.parent else None
if grandparent:
    player_text = grandparent.get_text().strip()
```

**File**: `lambda_function.py` - `parse_tag_heuer_url()` function

---

### 5. 18-Hole Scorecard Detection

**Issue**: System was looking for specific hole number strings, which failed.

**Solution**: Check for "Out" and "In" column headers:
```python
has_out = 'Out' in page_text
has_in = 'In' in page_text
is_18_hole_card = has_out and has_in
```

**File**: `lambda_function.py` - `parse_tag_heuer_url()` function

---

### 6. Negative Handicaps

**Issue**: Warringah handicaps showing negative values (impossible).

**Root Cause**: Using `rating=33.5` with `par=70` in course handicap formula:
```
CH = Index × Slope/113 + (Rating - Par)
CH = 16.1 × 101/113 + (33.5 - 70) = 14.4 - 36.5 = -22  ❌
```

**Solution**: Separate `rating` for index calculation vs `rating_display` for course handicap:
```python
BACK_9_CONFIG = {
    'par': 35,
    'slope': 101,
    'rating': 33.5,           # Used for INDEX calculation
    'rating_display': 35.5,    # Used for COURSE HANDICAP display (≈ par)
}

FRONT_9_CONFIG = {
    'par': 34,
    'slope': 101,
    'rating': 33.5,
    'rating_display': 34.5,
}
```

**Updated Function**:
```python
def calculate_course_handicap(index, slope, rating_display, par):
    ch = round(float(index) * slope / 113 + (rating_display - par))
    return max(0, ch)
```

**Result**: Positive, stable course handicaps (Andy: 15, Fletcher: 14, Bruce: 17)

**File**: `lambda_function.py` - course configs and `calculate_course_handicap()` function

---

### 7. Handicap Change Tracking

**Request**: Show how handicaps changed from last week.

**Solution**: Calculate index WITHOUT today's round for comparison:
```python
# Calculate previous week's index (without today's round)
if len(player_stats[name]['rounds']) > 1:
    prev_index = calculate_player_handicap_index(
        player_stats[name]['rounds'][:-1],  # Exclude last round
        config['slope'],
        config['rating']
    )
    player_stats[name]['prev_index'] = prev_index
```

**Display Format**:
```
Index: 16.1 (-0.3), Warringah: 15 (-1)
```

**File**: `lambda_function.py` - `generate_whatsapp_summary()` function

---

### 8. Summary Format Updates

**Requested Changes**:
- Move handicaps below stableford average
- Add "Stableford avg" label
- Remove total points column
- Show handicap changes with +/- indicators

**Before**:
```
🥇 1. Andy Jakes
      15.73 avg (30 rounds, 472 pts)
      Index: 16.1, Warringah: 15
      PB: 21 pts / 39 gross
```

**After**:
```
🥇 1. Andy Jakes
      15.73 Stableford avg (30 rounds)
      Index: 16.1 (-0.3), Warringah: 15 (-1)
      PB: 21 pts / 39 gross
```

**File**: `lambda_function.py` - `generate_whatsapp_summary()` function

---

### 9. AI Commentary Disappeared

**Issue**: After deploying fixes, AI commentary stopped appearing.

**Root Cause #1**: I was editing `lambda_function_aws.py` (no AI code) instead of `lambda_function.py` (has AI code).

**Root Cause #2**: After restoring AI code, OpenAI library had platform mismatch:
```
ImportError: No module named 'pydantic_core._pydantic_core'
```

**Explanation**: 
- OpenAI depends on `pydantic` which has compiled C extensions
- When installing on Windows, pip downloads Windows `.pyd` files
- Lambda runs on Linux (Amazon Linux 2) which needs `.so` files
- Binary incompatibility caused import failure

**Solution**: Install with Linux-compatible binaries:
```powershell
pip install requests beautifulsoup4 openai \
    --platform manylinux2014_x86_64 \
    --target lambda_package \
    --only-binary=:all: \
    --python-version 3.13
```

**Flags Explained**:
- `--platform manylinux2014_x86_64`: Get Linux x86_64 binaries
- `--only-binary=:all:`: Don't try to compile from source
- `--python-version 3.13`: Match Lambda runtime

**Result**: AI commentary working again with weather integration! 🎉

**Files Modified**:
- Build process (manual commands, need to update script)
- `lambda_function.py` - improved error handling

---

## Test Results

### Dec 19, 2025 Round (Fixed)
Successfully parsed and saved:
- Fletcher Jakes: 20 points, 38 gross
- Andy Jakes: 19 points, 41 gross  
- Bruce Kennaway: 17 points, 43 gross
- Steve: 10 points, 55 gross

### Handicap Indexes (Stable)
- Andy Jakes: 16.1 (was 16.4, -0.3)
- Fletcher Jakes: 14.7 (was 18.3, -3.6)
- Bruce Kennaway: 18.8 (was 19.1, -0.3)
- Hamish McNee: 26.6 (no change)
- Steve: 32.0 (no change)

### Course Handicaps (All Positive)
- Andy: 15 (was 16, -1)
- Fletcher: 14 (was 17, -3)
- Bruce: 17 (was 18, -1)
- Hamish: 24 (no change)
- Steve: 29 (no change)

### AI Commentary (Restored)
```
Weather: 25°C, clear skies, 11km/h winds.

Fletcher Jakes not only scored 20 points, but he also earned bragging 
rights over his dad Andy, who managed a respectable 19 points—talk about 
a classic father-son rivalry! Bruce Kennaway's 17 points prove he's more 
consistent than a broken record, while Steve's 10 points might just qualify 
him for a participation trophy this week—at least he showed up!

In a season full of surprises, Andy Jakes holds a slim lead while Fletcher 
is breathing down his neck, reminding us that family competition is the 
real heart of golf!
```

---

## Important Notes for Future Sessions

### 1. FILE TO EDIT
**ALWAYS EDIT**: `lambda_function.py` (936 lines, has AI commentary)
**NEVER EDIT**: `lambda_function_aws.py` (old/stripped version)

### 2. DEPLOYMENT COMMAND
```powershell
# Clean rebuild with Linux binaries
if (Test-Path lambda_package) { Remove-Item lambda_package -Recurse -Force }
New-Item -ItemType Directory -Path lambda_package | Out-Null

# Install with LINUX binaries (critical!)
pip install requests beautifulsoup4 openai `
    --platform manylinux2014_x86_64 `
    --target lambda_package `
    --only-binary=:all: `
    --python-version 3.13 `
    --quiet

# Copy function files
Copy-Item lambda_function.py lambda_package\
Copy-Item handicap.py lambda_package\

# Create zip
if (Test-Path lambda_function.zip) { Remove-Item lambda_function.zip }
Push-Location lambda_package
Compress-Archive -Path * -DestinationPath ..\lambda_function.zip -Force
Pop-Location

# Upload
python upload_lambda.py
```

### 3. COURSE CONFIGURATION VALUES (DO NOT CHANGE)
```python
BACK_9_CONFIG = {
    'par': 35,
    'slope': 101,
    'rating': 33.5,           # For index calculation
    'rating_display': 35.5,    # For course handicap display
}

FRONT_9_CONFIG = {
    'par': 34,
    'slope': 101,
    'rating': 33.5,
    'rating_display': 34.5,
}
```

### 4. KEY FUNCTIONS
- `parse_tag_heuer_url()`: Handles 18-hole cards, extracts stableford from indices [9,10,11]
- `calculate_player_handicap_index()`: WHS formula, uses `rating` (33.5)
- `calculate_course_handicap()`: Uses `rating_display` to avoid negative values
- `generate_whatsapp_summary()`: Calculates current and previous handicaps for changes
- `generate_ai_commentary()`: Requires OpenAI API key in Lambda environment

### 5. AWS LAMBDA ENVIRONMENT
- Function: `golf-handicap-tracker`
- Region: `ap-southeast-2`
- Runtime: Python 3.13
- Environment Variable: `OPENAI_API_KEY` (already configured)
- Auth Token: `HnB9_VsxLXQVVQqNXi2ilSyY0hPQDJ9EcEt-mVoGej0`

### 6. DATABASE
- Table: `golf-rounds` (DynamoDB)
- Total rounds: 47
- Latest: 2025-12-19

---

## Summary

All critical bugs fixed:
✅ Round submission working (action auto-detection)
✅ Date parsing with timestamps
✅ Correct stableford extraction (indices 9-11)
✅ Player name extraction from grandparent divs
✅ Positive course handicaps (rating_display)
✅ Handicap change tracking week-over-week
✅ AI commentary with weather (Linux binaries)

**System Status**: Fully operational 🎯

---

## Next Session Checklist

Before making any changes:
1. ✅ Confirm editing `lambda_function.py` (not lambda_function_aws.py)
2. ✅ Read this session file first
3. ✅ Use Linux-compatible pip install for any new dependencies
4. ✅ Test locally before deploying
5. ✅ Check CloudWatch logs if issues arise
6. ✅ Document all changes in new session file
