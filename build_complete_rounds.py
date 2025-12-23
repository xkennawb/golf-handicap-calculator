#!/usr/bin/env python3
"""
Build complete rounds data with proper blob/X handling
Manually extracted from Tag Heuer data
"""

# Course data
BACK_9_PARS = [5, 4, 3, 4, 3, 4, 4, 3, 4]  # Par 34, holes 10-18
BACK_9_HCP = [8, 9, 18, 6, 17, 3, 14, 12, 2]

FRONT_9_PARS = [4, 4, 5, 4, 3, 4, 4, 3, 4]  # Par 35, holes 1-9  
FRONT_9_HCP = [15, 3, 7, 10, 16, 1, 13, 5, 11]

def blob(par, hcp_index, strokes):
    """Calculate blob score: Par + 2 + (1 if gets stroke else 0)"""
    return par + 2 + (1 if hcp_index <= strokes else 0)

rounds_data = []

# ROUND 1: December 5, 2025 - Back 9, White tees (68.0/118)
print("1. December 5, 2025")
rounds_data.append({
    'date': '2025-12-05',
    'player_scores': {
        # Bruce: 8 strokes on back 9
        # Raw: 0 6 4 4 5  5  5 5 47
        # Holes: 6,4,4,5,X(14),5,X(16),5,5
        # X at 14 (par 3, hcp 17): 3+2+1=6
        # X at 16 (par 4, hcp 14): 4+2+1=7
        'Bruce Kennaway': {'holes': [6,4,4,5,6,5,7,5,5], 'gross': 47, 'tees': 'White'},
        
        # Andy: 8 strokes
        # Raw: 0 6 5 4 6 3  5 4 5 45
        # X at 15 (par 4, hcp 3): 4+2+1=7
        'Andy J.': {'holes': [6,5,4,6,3,7,5,4,5], 'gross': 45, 'tees': 'White'},
        
        # Fletcher: 6 strokes  
        # Raw: 0  4 3 4 4   4 4 44
        # X at 10 (par 5, hcp 8): 5+2+0=7 (no stroke, hcp>6)
        # X at 15 (par 4, hcp 3): 4+2+1=7
        # X at 16 (par 4, hcp 14): 4+2+0=6 (no stroke)
        'Fletcher J.': {'holes': [7,4,3,4,4,7,6,4,5], 'gross': 44, 'tees': 'White'},
        
        # Hamish: 11 strokes
        # Raw: 0  6 4 5 6 6 5 4 6 50
        # X at 10 (par 5, hcp 8): 5+2+1=8
        'Hamish M.': {'holes': [8,6,4,5,6,6,5,4,6], 'gross': 50, 'tees': 'White'},
    }
})

# ROUND 2: November 28, 2025 - Back 9, White
print("2. November 28, 2025")
rounds_data.append({
    'date': '2025-11-28',
    'player_scores': {
        # Bruce: 0 7 7  5 4 5 5 4 6 48
        # X at 12 (par 3, hcp 18): 3+2+0=5 (Bruce has 8 strokes, hcp 18 > 8, no stroke)
        'Bruce Kennaway': {'holes': [7,7,5,5,4,5,5,4,6], 'gross': 48, 'tees': 'White'},
        'Andy J.': {'holes': [6,5,3,5,4,7,6,3,6], 'gross': 45, 'tees': 'White'},
        'Hamish M.': {'holes': [8,7,4,4,6,6,6,4,6], 'gross': 51, 'tees': 'White'},
    }
})

# ROUND 3: November 21, 2025 - Back 9, White
print("3. November 21, 2025")
rounds_data.append({
    'date': '2025-11-21',
    'player_scores': {
        # Bruce: 0 5  3 6 4 5 4 5 6 45
        # X at 11 (par 4, hcp 9): 4+2+1=7
        'Bruce Kennaway': {'holes': [5,7,3,6,4,5,4,5,6], 'gross': 45, 'tees': 'White'},
        # Andy: 0 9  4 5 5 5 5 4 7 51
        # X at 11: 4+2+1=7
        'Andy J.': {'holes': [9,7,4,5,5,5,5,4,7], 'gross': 51, 'tees': 'White'},
        # Steve: 0   3 4 3 6 6 3 8 48
        # X at 10: 5+2+1=8, X at 11: 4+2+1=7
        'Steve': {'holes': [8,7,3,4,3,6,6,3,8], 'gross': 48, 'tees': 'White'},
    }
})

# ROUND 4: November 14, 2025 - Back 9, White
print("4. November 14, 2025")
rounds_data.append({
    'date': '2025-11-14',
    'player_scores': {
        # Bruce: 0 5 4 4 6 4 6 6 4  46
        # X at 18 (par 4, hcp 2): 4+2+1=7
        'Bruce Kennaway': {'holes': [5,4,4,6,4,6,6,4,7], 'gross': 46, 'tees': 'White'},
        'Eddie': {'holes': [8,6,4,5,4,6,5,4,6], 'gross': 48, 'tees': 'White'},
        # Hamish: 0 7 7 3 5 3 6 4 5  48
        # X at 18: 4+2+2=8 (Hamish has 11 strokes, gets 2 on some holes with very low hcp)
        # Actually hcp 2 means hole 18, so Hamish gets 1 stroke: 4+2+1=7
        'Hamish M.': {'holes': [7,7,3,5,3,6,4,5,8], 'gross': 48, 'tees': 'White'},
        # Steve: 0 8 6 3 5 4 7 6 4  51
        # X at 18: 4+2+2=8 (Steve 11 strokes gets on hcp<=11)
        'Steve': {'holes': [8,6,3,5,4,7,6,4,8], 'gross': 51, 'tees': 'White'},
    }
})

# ROUND 5: November 7, 2025 - Back 9, White
print("5. November 7, 2025")
rounds_data.append({
    'date': '2025-11-07',
    'player_scores': {
        # Bruce: 0  4 3 5 3 7 5 4 6 45
        # X at 10: 5+2+1=8
        'Bruce Kennaway': {'holes': [8,4,3,5,3,7,5,4,6], 'gross': 45, 'tees': 'White'},
        'Hamish M.': {'holes': [7,5,3,5,3,6,5,4,5], 'gross': 43, 'tees': 'White'},
        # Steve: 0 6  3 5 4 5 6 3 8 47
        # X at 11: 4+2+1=7
        'Steve': {'holes': [6,7,3,5,4,5,6,3,8], 'gross': 47, 'tees': 'White'},
    }
})

# Continue with remaining 36 rounds...
# For brevity, I'll add key rounds and then generate the rest

print(f"\nBuilt {len(rounds_data)} rounds")
print("Verifying totals...")

for i, round_info in enumerate(rounds_data, 1):
    print(f"\nRound {i}: {round_info['date']}")
    for player, data in round_info['player_scores'].items():
        calc_total = sum(data['holes'])
        expected = data['gross']
        status = "✓" if calc_total == expected else f"✗ ({calc_total} != {expected})"
        print(f"  {player:20s}: {status}")

print(f"\nTotal rounds ready: {len(rounds_data)}")
print("Need to add remaining", (41 - len(rounds_data)), "rounds")
