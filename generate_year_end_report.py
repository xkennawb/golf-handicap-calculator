"""
Generate comprehensive end-of-season report for any year
Usage: python generate_year_end_report.py [year]
Example: python generate_year_end_report.py 2025
"""
import boto3
import sys
import os
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

try:
    from openai import OpenAI
    OPENAI_ENABLED = True
except ImportError:
    OPENAI_ENABLED = False
    print("OpenAI library not available - AI commentary will be skipped")

# Get year from command line or use current year
if len(sys.argv) > 1:
    year = sys.argv[1]
else:
    year = str(datetime.now().year - 1)  # Default to previous year

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', verify=False)
table = dynamodb.Table('golf-rounds')

def parse_date(date_str):
    """Parse date from string, handling -back9 suffix"""
    clean_date = date_str.split('-back9')[0]
    return datetime.strptime(clean_date, '%Y-%m-%d')

def get_display_name(name):
    """Convert database names to display names"""
    if name == "Steve":
        return "Steve Lewthwaite"
    return name

# Get all rounds
response = table.scan()
rounds = response.get('Items', [])

# Filter for specified year
rounds_year = [r for r in rounds if r['date'].startswith(str(year))]
print(f"Analyzing {len(rounds_year)} rounds from {year}...\n")

# Calculate comprehensive stats
player_stats = defaultdict(lambda: {
    'rounds': [],
    'total_points': 0,
    'best_score': 0,
    'worst_score': 100,
    'monthly_wins': defaultdict(int),
    'front9_points': [],
    'back9_points': [],
    'winning_rounds': 0,
    'podium_finishes': 0
})

# Process each round
for round_data in rounds_year:
    round_date = parse_date(round_data['date'])
    month = round_date.strftime('%B')
    
    # NOTE: Database labels are BACKWARDS - "front9" in DB = Back 9 in reality, "back9" in DB = Front 9 in reality
    course_field = round_data.get('course', 'back9')
    is_back9_in_reality = (course_field == 'front9' or '-back9' in round_data['date'])
    
    # Get winner of this round
    round_players = sorted(round_data['players'], key=lambda x: int(x['stableford']), reverse=True)
    winner_points = int(round_players[0]['stableford']) if round_players else 0
    
    for rank, player in enumerate(round_players, 1):
        name = player['name']
        points = int(player['stableford'])
        
        player_stats[name]['rounds'].append({
            'date': round_date,
            'points': points,
            'month': month,
            'nine': 'back9' if is_back9_in_reality else 'front9'
        })
        player_stats[name]['total_points'] += points
        player_stats[name]['best_score'] = max(player_stats[name]['best_score'], points)
        player_stats[name]['worst_score'] = min(player_stats[name]['worst_score'], points)
        
        if is_back9_in_reality:
            player_stats[name]['back9_points'].append(points)
        else:
            player_stats[name]['front9_points'].append(points)
        
        # Track wins and podiums
        if rank == 1:
            player_stats[name]['winning_rounds'] += 1
            player_stats[name]['monthly_wins'][month] += 1
        if rank <= 3:
            player_stats[name]['podium_finishes'] += 1

# Calculate averages and additional metrics
for name, stats in player_stats.items():
    rounds_count = len(stats['rounds'])
    if rounds_count > 0:
        stats['avg'] = stats['total_points'] / rounds_count
        stats['rounds_count'] = rounds_count
        
        # Calculate consistency (standard deviation)
        avg = stats['avg']
        variance = sum((r['points'] - avg) ** 2 for r in stats['rounds']) / rounds_count
        stats['std_dev'] = variance ** 0.5
        
        # Front 9 vs Back 9 performance
        if stats['front9_points']:
            stats['front9_avg'] = sum(stats['front9_points']) / len(stats['front9_points'])
        if stats['back9_points']:
            stats['back9_avg'] = sum(stats['back9_points']) / len(stats['back9_points'])
        
        # Calculate streaks
        sorted_rounds = sorted(stats['rounds'], key=lambda x: x['date'])
        current_streak = 0
        best_streak = 0
        prev_points = None
        
        for r in sorted_rounds:
            if prev_points is None or r['points'] >= prev_points:
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0
            prev_points = r['points']
        
        stats['best_improving_streak'] = best_streak
        
        # Win rate
        stats['win_rate'] = (stats['winning_rounds'] / rounds_count * 100) if rounds_count > 0 else 0

# Sort players by average
sorted_players = sorted(
    [(name, stats) for name, stats in player_stats.items() if stats['rounds_count'] >= 10],
    key=lambda x: x[1]['avg'],
    reverse=True
)

# Generate Report
# Most consistent player (lowest std dev)
most_consistent = min(sorted_players, key=lambda x: x[1]['std_dev'])

# Best improving streak
best_streaker = max(sorted_players, key=lambda x: x[1]['best_improving_streak'])

# Most wins
most_wins = max(sorted_players, key=lambda x: x[1]['winning_rounds'])

report = f"""⛳ *{year} SEASON REVIEW*
━ *WARRINGAH GC* ━

*📊 SEASON OVERVIEW*
```
Total Rounds: {len(rounds_year)}
Qualified Players: {len(sorted_players)}
Season: Jan - Dec {year}
```

*🏅 FINAL STANDINGS*
```
🥇 {get_display_name(sorted_players[0][0])}
   Average:  {sorted_players[0][1]['avg']:.2f} pts
   Rounds:   {sorted_players[0][1]['rounds_count']}
   Total:    {sorted_players[0][1]['total_points']} pts
   Best:     {sorted_players[0][1]['best_score']} pts
   Wins:     {sorted_players[0][1]['winning_rounds']} ({sorted_players[0][1]['win_rate']:.1f}%)
   Podiums:  {sorted_players[0][1]['podium_finishes']}

🥈 {get_display_name(sorted_players[1][0])}
   Average:  {sorted_players[1][1]['avg']:.2f} pts
   Rounds:   {sorted_players[1][1]['rounds_count']}
   Total:    {sorted_players[1][1]['total_points']} pts
   Best:     {sorted_players[1][1]['best_score']} pts
   Wins:     {sorted_players[1][1]['winning_rounds']} ({sorted_players[1][1]['win_rate']:.1f}%)
   Podiums:  {sorted_players[1][1]['podium_finishes']}

🥉 {get_display_name(sorted_players[2][0])}
   Average:  {sorted_players[2][1]['avg']:.2f} pts
   Rounds:   {sorted_players[2][1]['rounds_count']}
   Total:    {sorted_players[2][1]['total_points']} pts
   Best:     {sorted_players[2][1]['best_score']} pts
   Wins:     {sorted_players[2][1]['winning_rounds']} ({sorted_players[2][1]['win_rate']:.1f}%)
   Podiums:  {sorted_players[2][1]['podium_finishes']}
```

*🎯 CONSISTENCY AWARD*
```
{get_display_name(most_consistent[0])}
Std Dev: {most_consistent[1]['std_dev']:.2f}
```

*🔥 HOT STREAK AWARD*
```
{get_display_name(best_streaker[0])}
{best_streaker[1]['best_improving_streak']} consecutive improving rounds
```

*🏆 MOST ROUND WINS*
```
{get_display_name(most_wins[0])}
{most_wins[1]['winning_rounds']} victories ({most_wins[1]['win_rate']:.1f}% win rate)
```

*📅 MONTHLY DOMINANCE*
```
"""

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
monthly_rounds = defaultdict(int)
for round_data in rounds_year:
    month = parse_date(round_data['date']).strftime('%B')
    monthly_rounds[month] += 1

for month in months:
    if monthly_rounds[month] > 0:
        # Find who won most in this month
        month_leaders = [(name, stats['monthly_wins'][month]) for name, stats in player_stats.items() if stats['monthly_wins'][month] > 0]
        if month_leaders:
            month_leaders.sort(key=lambda x: x[1], reverse=True)
            top_winner = month_leaders[0]
            if top_winner[1] > 0:
                winner_first_name = get_display_name(top_winner[0]).split()[0]
                report += f"{month[:3]}: {winner_first_name} ({top_winner[1]} wins)\n"

report += "```\n\n"

# Fun facts
report += f"*🎲 SEASON HIGHLIGHTS*\n```\n"

# Highest single round
highest_round = max(
    [(name, max(stats['rounds'], key=lambda x: x['points'])) for name, stats in player_stats.items() if stats['rounds']],
    key=lambda x: x[1]['points']
)
report += f"🌟 Best Round:\n"
report += f"   {get_display_name(highest_round[0])}\n"
report += f"   {highest_round[1]['points']} pts on {highest_round[1]['date'].strftime('%b %d')}\n\n"

# Most rounds played
most_active = max(sorted_players, key=lambda x: x[1]['rounds_count'])
report += f"💪 Most Active:\n"
report += f"   {get_display_name(most_active[0])}\n"
report += f"   {most_active[1]['rounds_count']} rounds played\n\n"

# Biggest improvement
for name, stats in sorted_players:
    recent_5 = stats['rounds'][-5:] if len(stats['rounds']) >= 5 else []
    early_5 = stats['rounds'][:5] if len(stats['rounds']) >= 5 else []
    if recent_5 and early_5:
        recent_avg = sum(r['points'] for r in recent_5) / len(recent_5)
        early_avg = sum(r['points'] for r in early_5) / len(early_5)
        stats['improvement'] = recent_avg - early_avg

if any('improvement' in stats for name, stats in sorted_players):
    most_improved = max([(name, stats) for name, stats in sorted_players if 'improvement' in stats], key=lambda x: x[1]['improvement'])
    if most_improved[1]['improvement'] > 0:
        report += f"📈 Most Improved:\n"
        report += f"   {get_display_name(most_improved[0])}\n"
        report += f"   +{most_improved[1]['improvement']:.1f} pts improvement\n"

report += "```\n\n"
report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
report += f"*THANK YOU FOR AN AMAZING*\n"
report += f"*{year} SEASON! 🏆*\n"
report += f"*SEE YOU IN {int(year)+1}! ⛳*\n"
report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# Generate AI commentary
if OPENAI_ENABLED:
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        try:
            print("\nGenerating AI commentary...")
            
            # Build context for AI
            champion = sorted_players[0]
            runner_up = sorted_players[1]
            third_place = sorted_players[2]
            
            # Build player summary
            player_summary = f"""
SEASON CHAMPION: {get_display_name(champion[0])} - {champion[1]['avg']:.2f} avg, {champion[1]['winning_rounds']} wins
RUNNER-UP: {get_display_name(runner_up[0])} - {runner_up[1]['avg']:.2f} avg, {runner_up[1]['winning_rounds']} wins
THIRD PLACE: {get_display_name(third_place[0])} - {third_place[1]['avg']:.2f} avg, {third_place[1]['winning_rounds']} wins

TOTAL ROUNDS: {len(rounds_year)}
MOST ACTIVE: {get_display_name(most_active[0])} ({most_active[1]['rounds_count']} rounds)
MOST CONSISTENT: {get_display_name(most_consistent[0])} (Std Dev: {most_consistent[1]['std_dev']:.2f})
HOT STREAK: {get_display_name(best_streaker[0])} ({best_streaker[1]['best_improving_streak']} consecutive improving rounds)
"""
            
            if 'improvement' in most_improved[1]:
                player_summary += f"MOST IMPROVED: {get_display_name(most_improved[0])} (+{most_improved[1]['improvement']:.1f} pts)\n"
            
            prompt = f"""You are reviewing the {year} golf season at Warringah Golf Club. Write a humorous, insightful year-end commentary about the season.

{player_summary}

CRITICAL PLAYER RELATIONSHIPS:
- Andy Jakes is the FATHER
- Fletcher Jakes is Andy's SON (father-son relationship)
- Bruce Kennaway, Steve, and Hamish McNee are FRIENDS only (not related to anyone)
- NO ONE ELSE is related

Write 3-4 sentences that:
1. Celebrate the champion and their achievement
2. Acknowledge other top performers and notable stats
3. Highlight the most interesting storylines (most improved, hot streaks, consistency)
4. End with an encouraging note for next season

Be witty, respectful, and fun. This is for a friendly group chat."""

            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a witty golf commentator writing a year-end review. Be humorous but respectful. CRITICAL: Only Andy Jakes and Fletcher Jakes are related (father-son). Everyone else are just friends."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.8,
                timeout=15
            )
            
            commentary = response.choices[0].message.content.strip()
            
            # Add AI commentary to report
            report += f"\n*🎭 AI ROAST & TOAST:*\n```\n{commentary}\n```\n"
            print("✅ AI commentary generated")
            
        except Exception as e:
            print(f"⚠️  Could not generate AI commentary: {e}")
    else:
        print("⚠️  OpenAI API key not configured - skipping AI commentary")
else:
    print("⚠️  OpenAI library not available - skipping AI commentary")

print(report)

# Save to file
with open(f'{year}_season_report.txt', 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n✅ Report saved to: {year}_season_report.txt")
