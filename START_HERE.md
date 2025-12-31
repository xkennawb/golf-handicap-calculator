# 🏌️ Golf Handicap Tracker - Start Here

**Last Updated**: December 31, 2025

---

## 📚 Documentation Files

Read these in order when starting a session:

1. **QUICK_REFERENCE.md** ← Start here for quick reference
2. **SESSION_2025-12-29_mobile_optimization.md** - WhatsApp format optimization & latest updates
3. **SESSION_2025-12-20_fixes.md** - Critical bug fixes (parsing, handicaps, AI restoration)
4. **SESSION_2025-12-14_improvements.md** - AI commentary, weather, 18-hole support

---

## 🚨 CRITICAL: File to Edit

**✅ ALWAYS EDIT**: `lambda_function.py` (1575 lines, full version with all features)  
**❌ DELETED**: `lambda_function_aws.py` (removed Dec 25, 2025 to prevent confusion)

---

## 🚀 Quick Commands

### Build and Deploy
```powershell
.\build_lambda_package.ps1  # Uses Linux binaries for Lambda compatibility
python upload_lambda.py
```

### Test
```powershell
chcp 65001 >$null; python display_summary.py  # UTF-8 support for emojis
```

### View Historical Summaries
```powershell
python show_saturday_summary.py  # Shows summary for specific date
```

---

## 🔑 Key Facts

- **AWS Function**: `golf-handicap-tracker` in `ap-southeast-2`
- **Runtime**: Python 3.13
- **Database**: DynamoDB table `golf-rounds` (50 rounds as of Dec 31, 2025)
  - 48 Warringah rounds (handicap eligible)
  - 2 Monavale rounds (stableford only, not handicap eligible)
- **Auth Token**: `HnB9_VsxLXQVVQqNXi2ilSyY0hPQDJ9EcEt-mVoGej0`
- **OpenAI Key**: Already configured in Lambda environment ✅
- **iOS Shortcut**: "Post Golf Round" - Share Tag Heuer scorecard to auto-submit rounds

---

## ⚙️ Course Configuration (DO NOT CHANGE)

### Warringah Golf Club

```python
BACK_9_CONFIG = {
    'name': 'Back 9 (Holes 10-18)',
    'par': 35,
    'slope': 101,              # For index calculation (keeps existing handicaps stable)
    'rating': 33.5,            # For index calculation (keeps existing handicaps stable)
    'slope_display': 111,      # Warringah Whites official - for course handicap display only
    'rating_display': 33.0,    # Warringah Whites official - for course handicap display only
}

FRONT_9_CONFIG = {
    'name': 'Front 9 (Holes 1-9)',
    'par': 35,
    'slope': 101,              # For index calculation (keeps existing handicaps stable)
    'rating': 33.5,            # For index calculation (keeps existing handicaps stable)
    'slope_display': 127,      # Warringah Whites official - for course handicap display only
    'rating_display': 35.0,    # Warringah Whites official - for course handicap display only
}
```

### Multi-Course Support

The system now supports rounds from other courses (e.g., Monavale):
- Other course rounds have `handicap_eligible: false`
- Stableford points count toward season averages
- Gross scores NOT used for handicap calculations
- Display shows course name (e.g., "🏌️ Monavale")

---

## 🎮 Summary Features (December 2025)

### WhatsApp Summary Structure

The WhatsApp summary has been optimized for mobile viewing with the following sections:

1. **📅 DATE & COURSE INFO**
   - Condensed date format (e.g., "SAT, DEC 27, 2025") - fits on one line
   - Course name: 🏌️ Warringah Golf Club (or other course)
   - Weather conditions with emojis (🌧️ 🍃 15°C, drizzle, 17km/h winds)
   - Clickable scorecard URL (if available from Tag Heuer)

2. **🏆 TODAY'S RESULTS**
   - Compact table format with 25-character thin dash underlines
   - Rankings (🥇🥈🥉), player names, points, gross scores
   - If 18 holes: Shows both "⛳ FRONT 9" and "⛳ BACK 9" sections
   - Course name displayed for non-Warringah rounds (e.g., "🏌️ Monavale")

3. **☀️ DECEMBER BOARD** (or current month with season emoji)
   - Season emojis: ☀️ Summer, 🍂 Autumn, ❄️ Winter, 🌸 Spring (Southern Hemisphere)
   - Compact table with rankings and averages
   - Trend emojis: 📈 improving, 📉 declining, ➡️ stable
   - Based on last 5 rounds form
   - 25-character thin dash underlines

4. **� LEADERBOARD** (season standings)
   - Compact table with rankings and averages
   - Trend emojis: 📈📉➡️ based on last 5 rounds
   - **Only shows qualified players** (10+ rounds after June)
   - 25-character thin dash underlines
   - **⚠️ Not Qualified** section (after June only)
     - Players with <10 rounds shown separately
     - No bold, no table headers, aligned with main leaderboard
     - Only appears after June (months 7-12)

5. **📋 PLAYER STATS**
   - **Sorted alphabetically by first name** (Andy, Bruce, Fletcher, Hamish, Steve)
   - **Country flags** before names (🏴󠁧󠁢󠁥󠁮󠁧󠁿 England, 🇦🇺 Australia, 🇳🇿 New Zealand)
   - Uppercase player names with 25-character thin dash underlines
   - Emoji bullet format:
     - 🎯 Rounds count (with ⚠️ DNQ if < 10 rounds after June)
     - 📊 WHS handicap (with change arrow) | War HCP (with change arrow)
     - 🏆 PBs: 20 stb | 38 gs (Stableford & Gross personal bests)
     - 📈 Avg: 42.8 (average gross score)
   - Clean vertical layout optimized for mobile

6. **🎭 AI COMMENTARY**
   - Weather line (factual, with emojis: ☀️🌧️⛅☁️⛈️🍃💨)
   - Player banter (humorous, mentions ALL players who played)
   - **Includes handicap changes** when significant (>0.05 change)
   - Season summary with next game prediction (based on hottest form)
   - Father-son relationships correct (Fletcher is Andy's son)

### Removed Sections
- ❌ **Performance Trends** - Removed for cleaner mobile display (trends now shown as emojis)
- ❌ **FUN STATS** - Removed to reduce clutter

### Formatting Standards
- All table underlines: Thin dash (─) character, exactly 25 characters
- Spacing: Single line feed between sections (no double spacing)
- Date format: Abbreviated (SAT, DEC 27, 2025) to fit on one line
- Headers: Bold with asterisks (*TEXT:*) and single line feed after
- Season emojis: ☀️ Summer (Dec-Feb), 🍂 Autumn (Mar-May), ❄️ Winter (Jun-Aug), 🌸 Spring (Sep-Nov)
- DNQ Logic: Only shown after June (month > 6) AND when rounds < 10
- Labels: "WHS" for handicap index, "War HCP" for course handicap
- PBs format: "stb" for stableford, "gs" for gross
- Change indicators: Arrows and numeric changes (e.g., (-0.7))

### AI Commentary Features
- **Weather-aware**: Factual weather line at start
- **Player-specific**: Only mentions players who played that day
- **Handicap changes**: Mentions significant WHS handicap changes (e.g., "Fletcher dropped from 14.7 to 14.0")
- **Form-based predictions**: Identifies next game favorite based on last 5 rounds
- **Accurate nine references**: Correctly identifies Front 9 vs Back 9 scores
- **Season finale aware**: Announces champion in late December games

### 18-Hole Support
- Tag Heuer cards with both Out and In scores automatically split into 2 rounds
- Front 9 stored with standard date (e.g., `2025-12-23`)
- Back 9 stored with `-back9` suffix (e.g., `2025-12-23-back9`)
- Both rounds included in handicap calculations
- Both displayed separately in TODAY'S RESULTS
- AI commentary mentions both nines accurately

### Historical Summaries
- Can view summary for any past date using `?date=YYYY-MM-DD` parameter
- Shows what the summary looked like on that specific date
- Useful for testing and reviewing past performance

---

## 🐛 Known Issues & Solutions

### AI Commentary Not Working
**Cause**: Binary incompatibility (Windows binaries won't work in Linux Lambda)  
**Solution**: Build script uses `--platform manylinux2014_x86_64` for Linux binaries

### Wrong Scores Extracted
**Cause**: Using wrong array indices [3-5] instead of [9-10-11]  
**Solution**: Stableford is at `recap_values[9], recap_values[10], recap_values[11]`

### Negative Handicaps
**Cause**: Using `rating=33.5` with `par=70` in course handicap formula  
**Solution**: Use `rating_display=35.5` for course handicap calculation

### AI Mixing Up Front/Back 9 Scores
**Cause**: Monavale rounds use `course='other_monavale'` not `'front9'`/`'back9'`  
**Solution**: Check date suffix (`-back9`) to determine which nine, not just course field

### Duplicate Rounds on Same Day
**Cause**: DynamoDB primary key is date only (HASH key)  
**Solution**: Back 9 rounds get `-back9` suffix to create unique key

### Father-Son Relationship Wrong
**Cause**: AI hallucinating relationships without clear instruction  
**Solution**: Always include in prompt: "Fletcher Jakes is Andy Jakes' SON (Andy is the father, Fletcher is his son). Bruce Kennaway is NOT related to Fletcher or Andy."

### DNQ Players Mentioned as Leading
**Cause**: AI mentioning players with less than 10 rounds in season standings discussion  
**Solution**: Filter season leaderboard to only include qualified players (10+ rounds) before sending to AI

### Season Finale Not Mentioned
**Cause**: AI not aware when it's the last game of the season  
**Solution**: Auto-detect games after Dec 20 and add champion announcement to AI prompt

### iOS Shortcut Issues
**Cause**: iOS Shortcuts variable passing and JSON formatting issues  
**Solution**: 
- Use Text action: `{"action": "add_round", "url": "[Shortcut Input]"}`
- Ensure URL is quoted in JSON string
- Lambda parses nested `{"JSON": "..."}` format from iOS Shortcuts
- Lambda extracts URL from Share Sheet text format automatically

---

## ✅ System Status

**All Systems Operational** as of Dec 29, 2025:
- ✅ iOS Shortcut "Post Golf Round" working (Share Sheet integration)
- ✅ Round submission working (front 9, back 9, or 18 holes)
- ✅ Scorecard parsing (18-hole cards auto-split into 2 rounds)
- ✅ Handicap calculations (WHS Australia compliant with hard/soft cap protection)
- ✅ Hard/Soft Cap: Prevents excessive handicap increases (WHS standard)
- ✅ Low Handicap Index tracking (365-day rolling window)
- ✅ Multi-course support (Monavale rounds tracked separately)
- ✅ Change tracking (week-over-week handicap changes with arrows)
- ✅ AI commentary with weather (OpenAI GPT-4o-mini)
- ✅ **Handicap change mentions in AI** (drops/increases highlighted)
- ✅ **Form-based predictions** (next game favorite based on last 5 rounds)
- ✅ Father-son relationships correct (Fletcher is Andy's son, not Bruce's)
- ✅ DNQ players filtered from season leaderboard (need 10 rounds to qualify)
- ✅ Season finale detection (Dec 20+) announces champion
- ✅ WhatsApp-optimized mobile format (compact tables, single spacing)
- ✅ Trend emojis in leaderboards (📈📉➡️ based on last 5 rounds)
- ✅ Clean player stats format (uppercase names, emoji bullets)
- ✅ Historical summary support (view any past date)
- ✅ 50 rounds in database (48 Warringah + 2 Monavale)
- ✅ Country flags for players (birthplace emojis)
- ✅ Player stats sorted alphabetically by first name
- ✅ Qualified/non-qualified leaderboard split (after June)
- ✅ Year-over-year comparison disabled (can be re-enabled later)
- ✅ Version control (GitHub: xkennawb/golf-handicap-calculator, private repo)

---

## 📞 Support

If you encounter issues:
1. Check CloudWatch logs in AWS Lambda Console
2. Read the session files (they document all fixes)
3. Test locally with `python get_full_summary.py`
4. Verify correct file being edited (`lambda_function.py`)
5. Ensure build uses Linux binaries (`--platform manylinux2014_x86_64`)
