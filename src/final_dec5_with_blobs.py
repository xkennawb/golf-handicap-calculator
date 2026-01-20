#!/usr/bin/env python3
"""Final December 5th calculation with blob identification"""

# December 5, 2025 - Back 9
PARS = [5, 4, 3, 4, 3, 4, 4, 3, 4]  # Par 34, holes 10-18

players = {
    'Bruce Kennaway': {
        'tag_gross': 47,
        'tag_stableford': [2, 3, 1, 2, 0, 2, 0, 1, 2],  # = 13
        'tag_strokes_per_hole': [1, 1, 0, 1, 0, 1, 0, 0, 1],
        'blob_holes': [14, 16],  # 0-point holes (indices 4, 6)
    },
    'Andy J.': {
        'tag_gross': 45,
        'tag_stableford': [2, 2, 1, 1, 3, 0, 2, 2, 2],  # = 15
        'tag_strokes_per_hole': [1, 1, 0, 1, 0, 1, 0, 0, 1],
        'blob_holes': [15],  # 0-point hole (index 5)
    },
    'Fletcher J.': {
        'tag_gross': 44,
        'tag_stableford': [0, 3, 2, 3, 1, 0, 0, 2, 3],  # = 14
        'tag_strokes_per_hole': [1, 1, 0, 1, 0, 1, 0, 0, 1],
        'blob_holes': [10, 15, 16],  # 0-point holes (indices 0, 5, 6)
    },
    'Hamish M.': {
        'tag_gross': 50,
        'tag_stableford': [0, 1, 2, 2, 0, 2, 2, 2, 2],  # = 13
        'tag_strokes_per_hole': [1, 1, 1, 1, 1, 2, 1, 1, 2],
        'blob_holes': [10, 14],  # 0-point holes (indices 0, 4)
    },
}

print('December 5, 2025 - FINAL CALCULATION WITH BLOBS')
print('='*70)
print('\nBlob Formula: Gross = Par + 2 + Strokes on that hole\n')

for name, data in players.items():
    stableford = data['tag_stableford']
    strokes_per_hole = data['tag_strokes_per_hole']
    expected_gross_total = data['tag_gross']
    blob_holes = data['blob_holes']
    
    print(f'{name}:')
    print(f'  Blob holes: {blob_holes}')
    print(f'  Hole:       10  11  12  13  14  15  16  17  18')
    print(f'  Par:         {" ".join(f"{p:2d}" for p in PARS)}')
    print(f'  Strokes:     {" ".join(f"{s:2d}" for s in strokes_per_hole)}')
    print(f'  Stableford:  {" ".join(f"{pts:2d}" for pts in stableford)}')
    
    # Calculate gross scores
    holes = []
    for i in range(9):
        hole_num = i + 10
        par = PARS[i]
        pts = stableford[i]
        strokes = strokes_per_hole[i]
        
        if hole_num in blob_holes:
            # Blob: Par + 2 + Strokes
            gross = par + 2 + strokes
        else:
            # Regular: calculate from stableford points
            if pts == 4:
                net = par - 2
            elif pts == 3:
                net = par - 1
            elif pts == 2:
                net = par
            elif pts == 1:
                net = par + 1
            else:  # 0 points (but not a blob - maybe very bad score)
                net = par + 2
            gross = net + strokes
        
        holes.append(gross)
    
    calc_total = sum(holes)
    tag_total_stableford = sum(stableford)
    
    print(f'  Gross:       {" ".join(f"{g:2d}" for g in holes)} = {calc_total}')
    print(f'  Expected:    {expected_gross_total}')
    print(f'  Stableford:  {tag_total_stableford} points')
    
    if calc_total == expected_gross_total:
        print(f'  ✓ PERFECT MATCH!')
    else:
        print(f'  ✗ Still off by {expected_gross_total - calc_total}')
    
    print()

print('='*70)
print('FINAL RESULTS FOR DECEMBER 5, 2025:')
print('='*70)
results = [(name, sum(data['tag_stableford'])) for name, data in players.items()]
results.sort(key=lambda x: x[1], reverse=True)
for i, (name, pts) in enumerate(results, 1):
    print(f'{i}. {name:20s} - {pts} points')
