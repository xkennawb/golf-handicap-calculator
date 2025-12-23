#!/usr/bin/env python3
"""Generate WhatsApp message for latest round"""

from datetime import datetime
from collections import defaultdict

# All rounds data
rounds_data = [
    {'date': '2025-12-05', 'player_scores': {
        'Bruce Kennaway': {'stableford': 13, 'gross': 47},
        'Andy J.': {'stableford': 15, 'gross': 45},
        'Fletcher J.': {'stableford': 14, 'gross': 44},
        'Hamish M.': {'stableford': 13, 'gross': 50},
    }},
    {'date': '2025-11-28', 'player_scores': {
        'Bruce Kennaway': {'stableford': 12, 'gross': 48},
        'Andy J.': {'stableford': 15, 'gross': 45},
        'Hamish M.': {'stableford': 12, 'gross': 51},
    }},
    {'date': '2025-11-21', 'player_scores': {
        'Bruce Kennaway': {'stableford': 15, 'gross': 45},
        'Andy J.': {'stableford': 10, 'gross': 51},
        'Steve': {'stableford': 15, 'gross': 48},
    }},
    {'date': '2025-11-14', 'player_scores': {
        'Bruce Kennaway': {'stableford': 14, 'gross': 46},
        'Eddie': {'stableford': 12, 'gross': 48},
        'Hamish M.': {'stableford': 15, 'gross': 48},
        'Steve': {'stableford': 12, 'gross': 51},
    }},
    {'date': '2025-11-07', 'player_scores': {
        'Bruce Kennaway': {'stableford': 15, 'gross': 45},
        'Hamish M.': {'stableford': 20, 'gross': 43},
        'Steve': {'stableford': 16, 'gross': 47},
    }},
    {'date': '2025-10-31', 'player_scores': {
        'Bruce Kennaway': {'stableford': 15, 'gross': 45},
        'Fletcher J.': {'stableford': 17, 'gross': 41},
        'Hamish M.': {'stableford': 14, 'gross': 49},
        'Steve': {'stableford': 19, 'gross': 46},
    }},
    {'date': '2025-10-24', 'player_scores': {
        'Bruce Kennaway': {'stableford': 15, 'gross': 45},
        'Andy J.': {'stableford': 12, 'gross': 48},
        'Hamish M.': {'stableford': 16, 'gross': 48},
        'Steve': {'stableford': 12, 'gross': 53},
    }},
    {'date': '2025-10-17', 'player_scores': {
        'Bruce Kennaway': {'stableford': 15, 'gross': 45},
        'Andy J.': {'stableford': 18, 'gross': 42},
        'Hamish M.': {'stableford': 17, 'gross': 47},
        'Steve': {'stableford': 13, 'gross': 52},
    }},
    {'date': '2025-10-10', 'player_scores': {
        'Bruce Kennaway': {'stableford': 21, 'gross': 40},
        'Andy J.': {'stableford': 18, 'gross': 42},
        'Hamish M.': {'stableford': 16, 'gross': 48},
        'Steve': {'stableford': 14, 'gross': 51},
    }},
    {'date': '2025-10-03', 'player_scores': {
        'Bruce Kennaway': {'stableford': 13, 'gross': 48},
        'Andy J.': {'stableford': 20, 'gross': 40},
        'Hamish M.': {'stableford': 12, 'gross': 52},
    }},
    {'date': '2025-09-26', 'player_scores': {
        'Bruce Kennaway': {'stableford': 18, 'gross': 43},
        'Andy J.': {'stableford': 16, 'gross': 44},
        'Steve': {'stableford': 22, 'gross': 46},
    }},
    {'date': '2025-09-05', 'player_scores': {
        'Bruce Kennaway': {'stableford': 21, 'gross': 41},
        'Hamish M.': {'stableford': 14, 'gross': 52},
        'Steve': {'stableford': 18, 'gross': 50},
    }},
    {'date': '2025-08-29', 'player_scores': {
        'Bruce Kennaway': {'stableford': 11, 'gross': 51},
        'Andy J.': {'stableford': 12, 'gross': 47},
        'Hamish M.': {'stableford': 16, 'gross': 50},
        'Steve': {'stableford': 10, 'gross': 58},
    }},
    {'date': '2025-08-22', 'player_scores': {
        'Bruce Kennaway': {'stableford': 17, 'gross': 45},
        'Steve': {'stableford': 12, 'gross': 56},
    }},
    {'date': '2025-08-15', 'player_scores': {
        'Bruce Kennaway': {'stableford': 16, 'gross': 45},
        'Andy J.': {'stableford': 18, 'gross': 41},
        'Fletcher J.': {'stableford': 14, 'gross': 44},
        'Hamish M.': {'stableford': 23, 'gross': 43},
    }},
]

# Build all_rounds list
all_rounds = []
for round_data in rounds_data:
    date = datetime.strptime(round_data['date'], '%Y-%m-%d')
    for player, score_data in round_data['player_scores'].items():
        all_rounds.append({
            'date': date,
            'player': player,
            'stableford': score_data['stableford'],
            'gross': score_data['gross'],
        })

all_rounds.sort(key=lambda x: x['date'], reverse=True)

latest_date = all_rounds[0]['date']
latest_rounds = [r for r in all_rounds if r['date'] == latest_date]
latest_rounds.sort(key=lambda x: x['stableford'], reverse=True)

# Season stats
player_stats = defaultdict(lambda: {'rounds': [], 'total_points': 0})
for round_info in all_rounds:
    player = round_info['player']
    if len(player_stats[player]['rounds']) < 20:
        player_stats[player]['rounds'].append(round_info)
        player_stats[player]['total_points'] += round_info['stableford']

season_averages = []
for player, stats in player_stats.items():
    if stats['rounds']:
        avg = stats['total_points'] / len(stats['rounds'])
        season_averages.append({'player': player, 'rounds': len(stats['rounds']), 'average': avg})

season_averages.sort(key=lambda x: x['average'], reverse=True)

# Generate WhatsApp message
print('🏌️ WARRINGAH GOLF - BACK 9 STABLEFORD')
print(f'📅 {latest_date.strftime("%A, %B %d, %Y").upper()}')
print()
print('🏆 TODAY\'S RESULTS:')
for i, r in enumerate(latest_rounds, 1):
    emoji = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '  '
    print(f'{emoji} {i}. {r["player"]} - {r["stableford"]} points (Gross: {r["gross"]})')

print()
print('📊 SEASON LEADERBOARD (Last 20 rounds):')
for i, stat in enumerate(season_averages, 1):
    emoji = '👑' if i == 1 else '⭐' if i == 2 else '🌟' if i == 3 else '  '
    print(f'{emoji} {i}. {stat["player"]} - {stat["average"]:.1f} avg ({stat["rounds"]} rounds)')

print()
print('⛳ Next round: Friday, December 12, 2025')
