# 🏌️ Golf Handicap Tracker - Quick Reference

## 🚨 CRITICAL: Read This First

### Files to Edit
- ✅ **ALWAYS EDIT**: `lambda_function.py` (1755 lines, has AI commentary and all features)
- ❌ **DELETED**: `lambda_function_aws.py` (removed Dec 25, 2025 to prevent confusion)

### Build & Deploy
```powershell
# One command to build and deploy
.\build_lambda_package.ps1 && python upload_lambda.py
```

**IMPORTANT**: The build script uses `--platform manylinux2014_x86_64` to get Linux-compatible binaries. This is REQUIRED for OpenAI/pydantic to work in Lambda.

---

## 📋 Key Configuration Values (DO NOT CHANGE)

### Course Ratings
```python
BACK_9_CONFIG = {
    'par': 35,
    'slope': 101,
    'rating': 33.5,           # Used for INDEX calculation
    'rating_display': 35.5,    # Used for COURSE HANDICAP display (avoids negatives)
}

FRONT_9_CONFIG = {
    'par': 34,
    'slope': 101,
    'rating': 33.5,
    'rating_display': 34.5,
}
```

**Why two ratings?**
- `rating`: Actual course difficulty for WHS handicap index calculation
- `rating_display`: ≈ par value to prevent negative course handicaps in display

---

## 🔧 How It Works

### Round Submission Flow
1. iOS Shortcut sends: `{"url": "https://www.tagheuergolf.com/rounds/..."}`
2. Lambda auto-detects `action=add_round` if URL present
3. Parse Tag Heuer scorecard:
   - Detect 18-hole card (has "Out" and "In" columns)
   - Find player names in grandparent div
   - Extract 12 recap cells: [Out/In/Total] × [Score/Putts/HCP/Stableford]
   - Stableford points are at indices **[9,10,11]** (not [3-5] which is putts!)
4. Save to DynamoDB table `golf-rounds`
5. Calculate handicap index using WHS formula
6. Generate AI commentary with OpenAI
7. Return WhatsApp-formatted summary

### Handicap Calculation
```python
# Index (from gross scores)
differential = (gross_18 - rating_18) * (113 / slope)
index = WHS_best_8_of_20(differentials)

# Course Handicap (for display)
CH = round(index × slope/113 + (rating_display - par))
```

### Change Tracking
Compares current handicap vs handicap WITHOUT today's round to show weekly movement:
```
Index: 16.1 (-0.3), Warringah: 15 (-1)
```

---

## 🎭 AI Commentary

### Requirements
- OpenAI API key in Lambda environment variable: `OPENAI_API_KEY`
- Already configured in AWS Lambda ✅

### Output Format
```
Weather: 25°C, clear skies, 11km/h winds.

[Player banter mentioning ALL players by name]

[One-line season summary]
```

### Weather Data
- Free API: Open-Meteo (no key needed)
- Location: Warringah Golf Club (-33.7544, 151.2677)
- Uses tee time if available, defaults to 8am Sydney time

---

## 📊 Database Structure

### DynamoDB Table: `golf-rounds`
```json
{
  "date": "2025-12-19",
  "course": "back9",
  "players": [
    {
      "name": "Andy Jakes",
      "index": 19.0,
      "gross": 41,
      "stableford": 19
    }
  ]
}
```

**Total Rounds**: 47 (as of Dec 20, 2025)

---

## 🐛 Common Issues & Solutions

### Issue: AI Commentary Not Appearing
**Cause**: Binary incompatibility (Windows binaries in Linux Lambda)
**Solution**: Rebuild with `--platform manylinux2014_x86_64`

### Issue: Wrong Scores (Getting Putts Instead of Stableford)
**Cause**: Using indices [3-5] instead of [9-11]
**Solution**: `recap_values[9], recap_values[10], recap_values[11]`

### Issue: Negative Handicaps
**Cause**: Using `rating=33.5` with `par=70` in course handicap formula
**Solution**: Use `rating_display=35.5` for course handicap calculation

### Issue: Round Not Saving
**Cause**: iOS Shortcut not sending `"action"` parameter
**Solution**: Auto-detect action when URL present without explicit action

---

## 📝 Session Files

Read these BEFORE making changes:
- `SESSION_2025-12-14_improvements.md` - AI commentary, weather, 18-hole support
- `SESSION_2025-12-20_fixes.md` - Critical bug fixes, parsing issues

Always create a new session file for significant changes!

---

## 🧪 Testing

### Local Test
```powershell
python get_full_summary.py
```

### Test Today's URL Parsing
```powershell
python test_fixed_parser.py
```

### Check Database
```powershell
python check_db.py
```

---

## 🔑 AWS Resources

- **Function**: `golf-handicap-tracker`
- **Region**: `ap-southeast-2` (Sydney)
- **Runtime**: Python 3.13
- **URL**: https://wgrf7ptkhss36vmv7zph4aqzxy0spsff.lambda-url.ap-southeast-2.on.aws/
- **Auth Token**: `HnB9_VsxLXQVVQqNXi2ilSyY0hPQDJ9EcEt-mVoGej0`
- **DynamoDB**: `golf-rounds` table

---

## ✅ Pre-Deployment Checklist

Before deploying changes:
1. [ ] Editing `lambda_function.py` (not lambda_function_aws.py)
2. [ ] Read latest session file
3. [ ] Tested locally with real URLs
4. [ ] Build script uses Linux binaries (`--platform manylinux2014_x86_64`)
5. [ ] Course config values unchanged (unless fixing ratings)
6. [ ] Created session file documenting changes

---

## 📞 Key Functions Reference

| Function | Purpose | Key Details |
|----------|---------|-------------|
| `parse_tag_heuer_url()` | Parse scorecard | Indices [9,10,11] for stableford |
| `calculate_player_handicap_index()` | WHS handicap | Uses `rating=33.5` |
| `calculate_course_handicap()` | Course handicap | Uses `rating_display` |
| `generate_whatsapp_summary()` | Format output | Calculates change indicators |
| `generate_ai_commentary()` | OpenAI commentary | Requires Linux binaries |
| `lambda_handler()` | Main entry | Auto-detects action from URL |

---

**Last Updated**: December 31, 2025
**Status**: ✅ All systems operational

## 📱 WhatsApp Summary Format (Current)

### Section Order
1. 📅 Date & Scorecard Link
2. 🏆 TODAY'S RESULTS (compact table, 25-char underlines)
3. 🏅 DECEMBER BOARD (monthly leaderboard with trend emojis)
4. 🐐 LEADERBOARD (season leaderboard with trend emojis, qualified players only)
5. ⚠️ Not Qualified (after June only, <10 rounds, no headers, aligned columns)
6. 📋 PLAYER STATS (alphabetical by first name, country flags, uppercase names, emoji bullets)
7. 🎭 AI COMMENTARY (weather + banter + handicap changes + prediction)

### Removed Sections
- ❌ Performance Trends (replaced with trend emojis)
- ❌ FUN STATS (too busy for mobile)

### Format Standards
- All underlines: 25 characters, thin dash (─)
- Spacing: Single `\n` between sections
- Headers: Shortened for mobile (e.g., "DECEMBER BOARD" not "DECEMBER LEADERBOARD")
- Leaderboard: "🐐 LEADERBOARD" (no year, just LEADERBOARD)
- Player stats: Alphabetical by first name (Andy, Bruce, Fletcher, Hamish, Steve)
- Country flags: 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England, 🇦🇺 Australia, 🇳🇿 New Zealand before player names
- Player stats: Emoji bullets (🎯📊🏆📈), uppercase names
- Trend emojis: 📈📉➡️ based on last 5 rounds
- DNQ: Only after June (month > 6), shown as `⚠️ DNQ` on rounds line
- Not Qualified section: After June, no bold, no headers/underlines, aligned with leaderboard
- AI mentions handicap changes when significant (>0.05)
- Year-over-year comparison: Disabled (can be re-enabled by changing if False to if current_year >= 2026)
