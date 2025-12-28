# WHS Hard/Soft Cap Protection

**Implemented**: December 28, 2025

## What Is It?

The World Handicap System (WHS) includes **hard cap** and **soft cap** rules to prevent a player's handicap index from increasing too rapidly due to a bad stretch of rounds. This protects against handicap inflation.

## How It Works

### Low Handicap Index (LHI)
- System tracks your **lowest handicap index** achieved in the **last 365 days**
- This serves as the baseline for cap calculations
- Updates automatically with each round

### Soft Cap (3.0 Stroke Threshold)
If your handicap would increase by more than **3.0 strokes** from your LHI:
- The first 3.0 strokes of increase are allowed in full
- Any increase beyond 3.0 is **reduced by 50%**

**Example:**
```
Low Handicap Index: 15.0
New calculated index: 19.5 (increase of 4.5)

Calculation:
- First 3.0 strokes: allowed in full
- Remaining 1.5 strokes: 1.5 × 50% = 0.75
- Final capped index: 15.0 + 3.0 + 0.75 = 18.75

Protection saved: 0.75 strokes
```

### Hard Cap (5.0 Stroke Maximum)
Your handicap index **cannot increase** by more than **5.0 strokes** from your LHI, regardless of how poorly you play.

**Example:**
```
Low Handicap Index: 15.0
New calculated index: 22.0 (increase of 7.0)

Result:
- Hard cap limits increase to 5.0
- Final capped index: 15.0 + 5.0 = 20.0

Protection saved: 2.0 strokes
```

## When Does It Apply?

✅ **Applies to increases only** - Your handicap can always decrease without restriction
✅ **365-day rolling window** - LHI is your lowest index in the past year
✅ **Automatic** - No manual intervention needed

## Why Is This Important?

1. **Fairness**: Prevents temporary bad form from inflating handicaps
2. **Integrity**: Maintains the credibility of the handicap system
3. **WHS Compliance**: Makes your handicaps legitimate for tournament play
4. **Player Protection**: You can have a bad stretch without permanently damaging your handicap

## Implementation Details

### Files Modified
- `handicap.py`: Added `apply_handicap_caps()` method to `HandicapCalculator`
- `lambda_function.py`: Updated `calculate_player_handicap_index()` to track LHI and apply caps

### Code Location
- **Cap Logic**: `handicap.py` lines 155-181
- **LHI Tracking**: `lambda_function.py` lines 221-235

### Testing
Run `test_handicap_caps.py` to verify cap calculations:
```powershell
python test_handicap_caps.py
```

## Current Player Status

As of Dec 28, 2025, all players are playing consistently, so caps have not been triggered. The protection is in place for future scenarios where someone has a bad stretch of rounds.

## References

- World Handicap System Rules of Handicapping (Golf Australia)
- WHS Hard Cap: Maximum 5.0 stroke increase from LHI
- WHS Soft Cap: 50% reduction of increases beyond 3.0 strokes
