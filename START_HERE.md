# 🏌️ Golf Handicap Tracker - Start Here

**Last Updated**: December 27, 2025

---

## 📚 Documentation Files

Read these in order when starting a session:

1. **QUICK_REFERENCE.md** ← Start here for quick reference
2. **SESSION_2025-12-14_improvements.md** - AI commentary, weather, 18-hole support
3. **SESSION_2025-12-20_fixes.md** - Critical bug fixes (parsing, handicaps, AI restoration)

---

## 🚨 CRITICAL: File to Edit

**✅ ALWAYS EDIT**: `lambda_function.py` (1644 lines, full version with all features)  
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
- **Database**: DynamoDB table `golf-rounds` (50 rounds as of Dec 27, 2025)
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

### Core Sections
- 📅 **TODAY'S RESULTS** - Latest round(s) with bullet points
  - Shows course name (Warringah or other courses)
  - If 18 holes played: Shows both "Front 9:" and "Back 9:" sections
  - Each player listed with points and gross score
- 📊 **SEASON LEADERBOARD** - Year stats with trend indicators (📈📉➡️) and bullet points
  - Includes average gross score for each player
  - **DNQ indicator** for players with less than 10 rounds (need 10 to qualify)
- 🏅 **MONTHLY TOURNAMENT** - Current month only
- 📈 **PERFORMANCE TRENDS** - Continuous line graphs showing year-long form
  - Spark line visualization for each player (Jan-Dec)
  - Carries forward last value when no rounds played (smooth trend)
  - Trend summary comparing first quarter vs last quarter
  - Shows if finishing strong, declining, or consistent
- 🎮 **FUN STATS** - Head-to-head, hot hand, clutch factor (W-L format), predictions, rotating badges
- 🎭 **AI COMMENTARY** - Weather-aware banter
  - Only mentions players who actually played that day
  - Separate weather line (factual only) with **weather emojis** (☀️🌧️⛅☁️⛈️🍃💨)
  - Accurate about Front 9 vs Back 9 scores

### Labels & Formatting
- "HCP:" and "Warringah HCP:" (not "Index:" or "Warringah:")
- "Points" for averages (not "avg" or "avg stableford")
- Bullet points (•) for all stats under player names
- Separate lines for HCP and Warringah HCP in TODAY'S RESULTS
- "Avg Gross:" shown in season leaderboard

### Weekly Rotation
- Rivalry matchups rotate based on ISO week number
- Achievement badges (20+ Club, Most Improved, Grinder) rotate weekly
- All features year-specific (reset in 2026)

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

**All Systems Operational** as of Dec 27, 2025:
- ✅ iOS Shortcut "Post Golf Round" working (Share Sheet integration)
- ✅ Round submission working (front 9, back 9, or 18 holes)
- ✅ Scorecard parsing (18-hole cards auto-split into 2 rounds)
- ✅ Handicap calculations (WHS compliant, both nines for 18-hole rounds)
- ✅ Multi-course support (Monavale rounds tracked separately)
- ✅ Change tracking (week-over-week)
- ✅ Performance trends (continuous line graphs with trend summaries)
- ✅ AI commentary with weather (only mentions players who played)
- ✅ Father-son relationships correct (Fletcher is Andy's son, not Bruce's)
- ✅ DNQ players (less than 10 rounds) not mentioned as "leading"
- ✅ Season finale detection (Dec 20+) announces champion
- ✅ WhatsApp-formatted summaries with bullet points
- ✅ Fun features (rivalries, badges, predictions, clutch factor)
- ✅ Monthly tournament and best/worst months
- ✅ Consistent labeling throughout
- ✅ Historical summary support
- ✅ 50 rounds in database (48 Warringah + 2 Monavale)
- ✅ Version control (GitHub: xkennawb/golf-handicap-calculator, private repo)

---

## 📞 Support

If you encounter issues:
1. Check CloudWatch logs in AWS Lambda Console
2. Read the session files (they document all fixes)
3. Test locally with `python get_full_summary.py`
4. Verify correct file being edited (`lambda_function.py`)
5. Ensure build uses Linux binaries (`--platform manylinux2014_x86_64`)
