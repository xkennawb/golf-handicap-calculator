"""
AWS Lambda function to generate end-of-season report
Call this from iOS Shortcut at year end
"""
import json
import boto3
import os
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

OPENAI_ENABLED = False
try:
    from openai import OpenAI
    OPENAI_ENABLED = True
    print("OpenAI library loaded successfully")
except ImportError as e:
    print(f"OpenAI library not available: {e}")
except Exception as e:
    print(f"Error loading OpenAI: {e}")

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
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

def lambda_handler(event, context):
    """
    Generate year-end report for specified year (or current year if not specified)
    
    Query params:
    - year: Year to generate report for (default: current year)
    """
    
    # Get year from query params or use current year
    query_params = event.get('queryStringParameters', {}) or {}
    year = query_params.get('year', str(datetime.now().year))
    
    try:
        # Get all rounds
        response = table.scan()
        rounds = response.get('Items', [])
        
        # Filter for specified year
        rounds_year = [r for r in rounds if r['date'].startswith(str(year))]
        
        if not rounds_year:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'No rounds found for {year}'
                })
            }
        
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
            
            # NOTE: Database labels are BACKWARDS
            course_field = round_data.get('course', 'back9')
            is_back9_in_reality = (course_field == 'front9' or '-back9' in round_data['date'])
            
            # Get winner of this round
            round_players = sorted(round_data['players'], key=lambda x: int(x['stableford']), reverse=True)
            
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
        
        if not sorted_players:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'No qualified players (10+ rounds) for {year}'
                })
            }
        
        # Most consistent player
        most_consistent = min(sorted_players, key=lambda x: x[1]['std_dev'])
        
        # Best improving streak
        best_streaker = max(sorted_players, key=lambda x: x[1]['best_improving_streak'])
        
        # Most wins
        most_wins = max(sorted_players, key=lambda x: x[1]['winning_rounds'])
        
        # Generate Report
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
        for month in months:
            # Find who won most in this month
            month_leaders = [(name, stats['monthly_wins'][month]) for name, stats in player_stats.items() if stats['monthly_wins'][month] > 0]
            if month_leaders:
                month_leaders.sort(key=lambda x: x[1], reverse=True)
                top_winner = month_leaders[0]
                if top_winner[1] > 0:
                    winner_first_name = get_display_name(top_winner[0]).split()[0]
                    report += f"{month[:3]}: {winner_first_name} ({top_winner[1]} wins)\n"
        
        report += "```\n\n*🎲 SEASON HIGHLIGHTS*\n```\n"
        
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
        
        # Generate AI Commentary
        if OPENAI_ENABLED:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                try:
                    print("Attempting to generate AI commentary...")
                    client = OpenAI(api_key=api_key)
                    
                    # Build context for AI
                    champion_name = get_display_name(sorted_players[0][0])
                    champion_avg = sorted_players[0][1]['avg']
                    champion_wins = sorted_players[0][1]['winning_rounds']
                    runner_up = get_display_name(sorted_players[1][0])
                    runner_up_avg = sorted_players[1][1]['avg']
                    runner_up_wins = sorted_players[1][1]['winning_rounds']
                    third_place = get_display_name(sorted_players[2][0])
                    third_avg = sorted_players[2][1]['avg']
                    
                    # Calculate quarterly standings to show lead changes
                    quarters = {'Q1': [], 'Q2': [], 'Q3': [], 'Q4': []}
                    quarter_leaders = []
                    
                    for name, stats in player_stats.items():
                        for qname, months in [('Q1', ['January', 'February', 'March']), 
                                              ('Q2', ['April', 'May', 'June']),
                                              ('Q3', ['July', 'August', 'September']),
                                              ('Q4', ['October', 'November', 'December'])]:
                            q_rounds = [r for r in stats['rounds'] if r['month'] in months]
                            if q_rounds:
                                q_avg = sum(r['points'] for r in q_rounds) / len(q_rounds)
                                quarters[qname].append((name, q_avg, len(q_rounds)))
                    
                    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                        if quarters[q]:
                            leader = max(quarters[q], key=lambda x: x[1])
                            quarter_leaders.append(f"{q}: {get_display_name(leader[0])} ({leader[1]:.1f} avg)")
                    
                    lead_changes_text = " → ".join(quarter_leaders) if quarter_leaders else "Consistent throughout"
                    
                    # Individual performance details
                    performance_details = []
                    for name, stats in sorted_players:
                        perf = f"{get_display_name(name)}: {stats['avg']:.2f} avg, {stats['winning_rounds']} wins, {stats['rounds_count']} rounds"
                        # Note: Don't include Front 9 vs Back 9 comparison - mostly play Back 9 only
                        performance_details.append(perf)
                    
                    awards_text = f"Consistency Award: {get_display_name(most_consistent[0])}, "
                    awards_text += f"Hot Streak Award: {get_display_name(best_streaker[0])} ({best_streaker[1]['best_improving_streak']} rounds), "
                    awards_text += f"Most Wins: {get_display_name(most_wins[0])} ({most_wins[1]['winning_rounds']} wins)"
                    
                    prompt = f"""Generate a comprehensive 2-3 paragraph AI commentary for the {year} golf season wrap-up.

FINAL STANDINGS:
1. {champion_name}: {champion_avg:.2f} avg, {champion_wins} wins, {sorted_players[0][1]['rounds_count']} rounds
2. {runner_up}: {runner_up_avg:.2f} avg, {runner_up_wins} wins, {sorted_players[1][1]['rounds_count']} rounds  
3. {third_place}: {third_avg:.2f} avg, {sorted_players[2][1]['winning_rounds']} wins, {sorted_players[2][1]['rounds_count']} rounds

QUARTERLY LEADERS (showing how the lead changed):
{lead_changes_text}

INDIVIDUAL PERFORMANCES:
{chr(10).join('- ' + p for p in performance_details)}

AWARDS: {awards_text}

TOTAL ROUNDS: {len(rounds_year)}

IMPORTANT NOTES:
- The group plays almost exclusively on the BACK 9 at Warringah GC (9-hole rounds only)
- DO NOT MENTION "Front 9" AT ALL - they rarely play it
- DO NOT say anyone is a "Front 9 specialist" - WRONG INFORMATION
- Focus on their overall performance, not which 9 holes

CRITICAL PLAYER RELATIONSHIPS - DO NOT GET THIS WRONG:
- Andy Jakes is the FATHER
- Fletcher Jakes is Andy's SON (father-son relationship)
- Bruce Kennaway, Steve Lewthwaite, and Hamish McNee are FRIENDS only (not related to anyone)
- NO ONE ELSE is related

Write an engaging 2-3 paragraph commentary that:
1. Opens by celebrating the champion's victory
2. Discusses how the lead changed throughout the year (use the quarterly data)
3. Highlights individual performances and what made each player's season notable
4. Acknowledges the close competition and standout moments
5. Ends with excitement for next season

Keep it fun, slightly cheeky but respectful, and make it feel like a sports wrap-up article."""

                    print("Calling OpenAI API...")
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a professional sports commentator writing an engaging season wrap-up article. Write 2-3 paragraphs with rich detail and narrative flair."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=800,
                        temperature=0.8
                    )
                    
                    ai_commentary = response.choices[0].message.content.strip()
                    print(f"AI commentary generated: {ai_commentary[:50]}...")
                    
                    report += f"*🎙️ AI ROAST & TOAST*\n```\n{ai_commentary}\n```\n\n"
                    
                except Exception as e:
                    # Log error but continue
                    print(f"AI commentary failed: {str(e)}")
            else:
                print("No OpenAI API key found")
        else:
            print("OpenAI not enabled")
        
        report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"*THANK YOU FOR AN AMAZING*\n"
        report += f"*{year} SEASON! 🏆*\n"
        report += f"*SEE YOU IN {int(year)+1}! ⛳*\n"
        report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'summary': report,
                'year': year,
                'total_rounds': len(rounds_year),
                'qualified_players': len(sorted_players)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
