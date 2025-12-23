# 🏌️ Adding Rounds from Other Courses

## Quick Start

Run the script and follow the prompts:

```powershell
python add_other_course_round.py
```

## What It Does

- ✅ Adds stableford scores to seasonal averages
- ✅ Counts toward monthly tournaments
- ✅ Shows in TODAY'S RESULTS with course name
- ✅ Includes in Best/Worst months
- ❌ Does NOT affect handicap calculations
- ❌ Does NOT track gross scores or handicaps

## Example Usage

```
Enter date (YYYY-MM-DD) or press Enter for today: 2025-12-22
Enter course name (e.g., 'Avondale', 'Long Reef'): Avondale
Enter Stableford scores for each player:
(Press Enter to skip a player)

Andy Jakes: 18
Fletcher Jakes: 20
Bruce Kennaway: 16
Hamish McNee: 
Steve Lewthwaite: 12
```

## How It Appears

**TODAY'S RESULTS** will show:
```
*🏆 TODAY'S RESULTS:* 🏌️ Avondale

🥇 1. Fletcher Jakes
      • 20 points

🥈 2. Andy Jakes
      • 18 points
```

**SEASON LEADERBOARD** includes these scores:
```
🥇 1. Andy Jakes 📈
      • 15.80 Points (31 rounds)  ← Now includes Avondale
      • HCP: 16.1 (-0.3)  ← Unchanged! Calculated from Warringah only
```

## Important Notes

1. **Handicaps stay the same** - Only Warringah rounds affect handicaps
2. **Course name displays** - Shows which course was played
3. **No gross scores** - Other courses only track stableford points
4. **Full integration** - Counts for everything except handicaps

## Technical Details

The round is stored with:
- `handicap_eligible: false` - Skipped in handicap calculations
- `course: other_avondale` - Prefixed to identify non-Warringah
- `course_display_name: Avondale` - Human-readable name

## Testing

After adding a round:
```powershell
python get_full_summary.py
```

Check that:
- ✅ TODAY'S RESULTS shows course name
- ✅ Seasonal averages updated
- ✅ Handicaps unchanged
