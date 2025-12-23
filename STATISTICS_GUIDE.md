# Statistics Features Guide

## Overview

The golf handicap calculator now tracks comprehensive statistics for all players throughout the season.

## Statistics Tracked

### Per Round
- ✅ Gross Score
- ✅ Stableford Points
- ✅ Net Score
- ✅ Score Differential
- ✅ Weather conditions and difficulty factor

### Season Statistics (Year-to-Date)

For each player:

1. **Games Played** - Total number of rounds played
2. **Games Won** - Number of rounds where player had lowest net score
3. **Win Percentage** - (Games Won / Games Played) × 100
4. **Average Gross Score** - Mean of all gross scores
5. **Average Stableford Score** - Mean of all Stableford points
6. **Best Gross Score** - Personal best gross score for the year
7. **Best Stableford Score** - Highest Stableford points achieved

## Accessing Statistics

### Via iOS Shortcut (Future Enhancement)

You can create separate shortcuts to:
- Get current leaderboard
- Get detailed stats
- Get head-to-head comparisons

### Via Lambda Function

Send POST requests with different actions:

#### 1. Get Leaderboard
```json
{
  "action": "get_leaderboard",
  "year": 2025
}
```

Returns a WhatsApp-formatted leaderboard.

#### 2. Get Full Stats
```json
{
  "action": "get_stats",
  "year": 2025
}
```

Returns detailed JSON with all player statistics.

#### 3. Get Current Handicaps
```json
{
  "action": "get_handicaps"
}
```

Returns current handicap index for each player.

### Via Excel

Open `handicaps.xlsx` in Excel to see:
- All historical rounds with detailed scores
- Filter by player, date, course
- Create your own pivot tables and charts

### Via Python

```python
from excel_handler import ExcelHandler
from stats_reporter import StatsReporter

# Load data
excel = ExcelHandler('handicaps.xlsx')
excel.load_or_create_workbook()

# Get stats
stats = excel.get_year_stats(2025)

# Generate reports
reporter = StatsReporter(excel)
print(reporter.generate_leaderboard(2025))
print(reporter.generate_player_report('Bruce Kennaway', 2025))
print(reporter.generate_head_to_head('Bruce Kennaway', 'Andy J.', 2025))
```

## WhatsApp Message Format

After each round, the WhatsApp message includes:

```
⛳ Golf Handicaps Update
📅 Friday, December 05, 2025
🏌️ Warringah Golf Club

🏆 Today's Results:
🥇 Andy J.
   Gross: 45 (+9) | Stableford: 15
   Net: 37 (+1) | Index: 19.0

🥈 Fletcher J.
   Gross: 44 (+8) | Stableford: 14
   Net: 38 (+2) | Index: 14.0

💨 Weather Factor: 1.08x

📊 2025 Season Stats:

Andy J.:
  Games: 12 | Wins: 5 (41.7%)
  Avg Gross: 46.2 | Avg Stableford: 14.3
  Best Gross: 42 | Best Stableford: 18

Bruce Kennaway:
  Games: 12 | Wins: 3 (25.0%)
  Avg Gross: 48.5 | Avg Stableford: 12.8
  Best Gross: 44 | Best Stableford: 16
```

## Leaderboard Calculations

### Winner Determination
- Winner = Lowest net score for each round
- Ties count as a win for all tied players

### Ranking Order
Players are ranked by:
1. Total wins (highest first)
2. Win percentage (highest first)
3. Average Stableford score (highest first)

## Statistics Reports Available

### 1. Season Leaderboard
Shows all players ranked by performance.

### 2. Player Report
Detailed individual statistics including recent form.

### 3. Head-to-Head
Compare two players directly across all metrics.

### 4. WhatsApp Leaderboard
Compact format perfect for sharing in group chats.

## Excel Columns

The Excel file contains these columns:

| Column | Description |
|--------|-------------|
| Date | Round date (YYYY-MM-DD) |
| Player | Player name |
| Course | Golf course name |
| Gross Score | Total strokes taken |
| Stableford | Total Stableford points |
| Par | Course par for holes played |
| Score to Par | Gross score - Par |
| Playing HC | Handicap strokes for this round |
| Net Score | Gross - Playing HC |
| Differential | Score differential for handicap calculation |
| Weather Factor | Difficulty multiplier (1.0 = normal) |
| Weather Conditions | Description of weather |
| Current Index | Handicap index at time of round |
| Notes | Additional information |

## Tips

1. **Track Progress**: Compare your average scores month-by-month
2. **Set Goals**: Try to improve your win percentage each quarter
3. **Analyze Trends**: Look for patterns in your best performances
4. **Weather Impact**: See how weather difficulty affects your scores
5. **Friendly Competition**: Use head-to-head stats for friendly banter

## Future Enhancements

Potential features to add:
- Course-specific statistics
- Monthly breakdowns
- Handicap progression charts
- Best round by course
- Worst round (for motivation!)
- Improvement percentage
- Consistency score (standard deviation)

## Questions?

Check the main README.md for general setup and usage instructions.
