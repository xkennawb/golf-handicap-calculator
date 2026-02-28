"""
Recalculate Stableford scores for 2025-12-26+ rounds using CORRECTED WHS handicaps.

Uses the correct 18-hole stroke index allocation method:
- CH = round(WHS × slope_display/113 + (rating_display - par))
- Each hole with SI ≤ CH gets 1 stroke
- If CH > 18, holes with SI ≤ (CH-18) get an additional stroke
"""
import boto3
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime, timedelta
from load_credentials import load_credentials
import re
import urllib3

urllib3.disable_warnings()
load_credentials()

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', verify=False)
table = dynamodb.Table('golf-rounds')

# ─── Course configurations ──────────────────────────────────────────────────
BACK_9_CONFIG = {
    'name': 'Back 9 (Holes 10-18)',
    'par': 35,
    'slope': 101,        # For index/differential calculation
    'rating': 33.5,      # For index/differential calculation
    'slope_display': 111, # For course handicap (Warringah Whites official)
    'rating_display': 33.0,
}

# Back 9 stroke indexes (18-hole SI values)
BACK_9_SI = [8, 9, 18, 6, 17, 3, 14, 12, 2]
BACK_9_PARS = [5, 4, 3, 4, 3, 4, 4, 3, 4]  # par = 34 actual card, 35 for CH calc

# Front 9 stroke indexes (for reference, not used in current recalc)
FRONT_9_SI = [15, 1, 5, 10, 16, 7, 13, 4, 11]

# ─── WHS lookup table ───────────────────────────────────────────────────────
WHS_TABLE = {
    3: 1, 4: 1, 5: 1,
    6: 2, 7: 2, 8: 2,
    9: 3, 10: 3, 11: 3,
    12: 4, 13: 4, 14: 4,
    15: 5, 16: 5,
    17: 6, 18: 6,
    19: 7,
    20: 8
}

NAME_MAP = {
    'Andy J.': 'Andy Jakes',
    'Fletcher J.': 'Fletcher Jakes',
    'Hamish M.': 'Hamish McNee',
    'Bruce Kennaway': 'Bruce Kennaway',
    'Steve': 'Steve',
    'Steve Lewthwaite': 'Steve',
    'Steve L.': 'Steve',
}


def calculate_course_handicap(whs_index, slope_display, rating_display, par):
    """WHS Course Handicap: CH = round(WHS × S/113 + (CR - Par))"""
    ch = round(float(whs_index) * slope_display / 113 + (rating_display - par))
    return max(0, ch)


def allocate_strokes_18hole_si(course_handicap, hole_si_values):
    """
    Allocate strokes using 18-hole stroke index method.
    
    Each hole with SI ≤ CH gets 1 stroke.
    If CH > 18, holes with SI ≤ (CH - 18) get an additional stroke.
    If CH > 36, holes with SI ≤ (CH - 36) get yet another stroke.
    """
    strokes = [0] * len(hole_si_values)
    
    for i, si in enumerate(hole_si_values):
        if si <= course_handicap:
            strokes[i] += 1
        if course_handicap > 18 and si <= (course_handicap - 18):
            strokes[i] += 1
        if course_handicap > 36 and si <= (course_handicap - 36):
            strokes[i] += 1
    
    return strokes


def calculate_stableford_per_hole(scores, pars, strokes):
    """Calculate Stableford points for each hole"""
    points = []
    for score, par, s in zip(scores, pars, strokes):
        if score == 0 or score is None:
            points.append(0)
            continue
        net_score = score - s
        diff = net_score - par
        if diff <= -2:
            points.append(4)
        elif diff == -1:
            points.append(3)
        elif diff == 0:
            points.append(2)
        elif diff == 1:
            points.append(1)
        else:
            points.append(0)
    return points


def calculate_whs_index(differentials):
    """Calculate WHS index using correct last-20 window"""
    if len(differentials) < 3:
        return None
    last_20 = differentials[-20:] if len(differentials) > 20 else differentials
    num_scores = len(last_20)
    num_to_use = WHS_TABLE.get(num_scores, 8)
    sorted_diffs = sorted(last_20)
    best_diffs = sorted_diffs[:num_to_use]
    new_index = sum(best_diffs) / len(best_diffs) * 0.96
    return round(new_index, 1)


def apply_handicap_caps(new_index, low_handicap_index):
    """Apply WHS hard cap and soft cap"""
    if low_handicap_index is None:
        return new_index
    increase = new_index - low_handicap_index
    if increase <= 3.0:
        return new_index
    if increase <= 5.0:
        excess = increase - 3.0
        return round(low_handicap_index + 3.0 + (excess * 0.5), 1)
    return round(low_handicap_index + 5.0, 1)


def get_low_handicap_index(differentials, dates, as_of_date):
    """Get lowest WHS index achieved in last 365 days"""
    cutoff = (datetime.strptime(as_of_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
    indices = []
    for i, date in enumerate(dates):
        if date >= cutoff:
            idx = calculate_whs_index(differentials[:i+1])
            if idx is not None:
                indices.append(idx)
    return min(indices) if indices else None


def calculate_differential(gross, slope, rating):
    """Calculate 18-hole equivalent score differential from 9-hole gross"""
    gross_18 = gross * 2
    rating_18 = rating * 2
    diff = (gross_18 - rating_18) * (113 / slope)
    return round(diff, 1)


def get_corrected_whs_at_date(player_name, as_of_date, diff_history):
    """Calculate corrected WHS for a player as of a date (before that round)"""
    if player_name not in diff_history:
        return None
    diffs_before = [d for date, d in diff_history[player_name] if date < as_of_date]
    if len(diffs_before) < 3:
        return None
    raw_index = calculate_whs_index(diffs_before)
    if raw_index is None:
        return None
    dates_before = [date for date, d in diff_history[player_name] if date < as_of_date]
    lhi = get_low_handicap_index(diffs_before, dates_before, as_of_date)
    if lhi is not None:
        raw_index = apply_handicap_caps(raw_index, lhi)
    return round(raw_index, 1)


def scrape_hole_scores(url):
    """
    Scrape Tag Heuer scorecard for hole-by-hole scores.
    Returns dict of {player_name: [score1, ..., score9]} for back 9.
    """
    print(f"  Scraping: {url}")
    response = requests.get(url, timeout=15, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    score_tables = soup.find_all('div', class_='score-table')
    if not score_tables:
        return None
    
    player_sections = soup.find_all(string=re.compile(r'\(Index \d+\.\d+\)'))
    
    players = {}
    for ps in player_sections:
        gp = ps.parent.parent if ps.parent else None
        if not gp:
            continue
        pt = gp.get_text().strip()
        match = re.search(r'(.+?)\s*\(Index\s+(\d+\.\d+)\)', pt)
        if not match:
            continue
        
        name = NAME_MAP.get(match.group(1).strip(), match.group(1).strip())
        th_index = float(match.group(2))
        
        if name in ['Eddie', 'Jo W.', 'Mark', 'Julian']:
            continue
        if name in players:
            continue  # Skip duplicate entries (page shows stats twice)
        
        score_table = gp.find_next('div', class_='score-table')
        if not score_table:
            continue
        
        for row in score_table.find_all('div', recursive=False):
            cells = row.find_all('div')
            texts = [c.get_text().strip() for c in cells]
            if not texts:
                continue
            label = texts[0]
            
            if label == 'Score':
                # De-duplicate: take every other value starting from index 1
                all_vals = texts[1::2]
                # Back 9 starts after front 9 (9 values) and Out (1 value) = index 10
                if len(all_vals) >= 19:  # 18-hole card
                    back9_scores = all_vals[10:19]
                else:  # 9-hole card
                    back9_scores = all_vals[:9]
                
                scores = []
                for v in back9_scores:
                    try:
                        scores.append(int(v) if v and v.isdigit() else 0)
                    except:
                        scores.append(0)
                
                players[name] = {
                    'scores': scores,
                    'th_index': th_index,
                }
                break  # Got scores, move to next player
    
    # Also get stableford and HCP strokes for verification
    player_sections2 = soup.find_all(string=re.compile(r'\(Index \d+\.\d+\)'))
    seen = set()
    for ps in player_sections2:
        gp = ps.parent.parent if ps.parent else None
        if not gp:
            continue
        pt = gp.get_text().strip()
        match = re.search(r'(.+?)\s*\(Index\s+(\d+\.\d+)\)', pt)
        if not match:
            continue
        name = NAME_MAP.get(match.group(1).strip(), match.group(1).strip())
        if name in seen or name not in players:
            continue
        seen.add(name)
        
        score_table = gp.find_next('div', class_='score-table')
        if not score_table:
            continue
        
        for row in score_table.find_all('div', recursive=False):
            cells = row.find_all('div')
            texts = [c.get_text().strip() for c in cells]
            if not texts:
                continue
            label = texts[0]
            all_vals = texts[1::2]
            
            if label == 'HCP Strokes':
                back9 = all_vals[10:19] if len(all_vals) >= 19 else all_vals[:9]
                players[name]['th_hcp_strokes'] = [int(v) if v and v.isdigit() else 0 for v in back9]
            
            if label.startswith('Stableford'):
                back9 = all_vals[10:19] if len(all_vals) >= 19 else all_vals[:9]
                players[name]['th_stableford'] = [int(v) if v and v.isdigit() else 0 for v in back9]
    
    return players


def build_differential_history(all_rounds, slope, rating):
    """Build chronological differential history per player"""
    history = {}
    for r in all_rounds:
        date = r['date']
        date_clean = re.match(r'(\d{4}-\d{2}-\d{2})', date)
        if date_clean:
            date = date_clean.group(1)
        for p in r.get('players', []):
            name = p['name']
            gross = int(p.get('gross', 0))
            if gross == 0:
                continue
            diff = calculate_differential(gross, slope, rating)
            if name not in history:
                history[name] = []
            history[name].append((date, diff))
    return history


def main():
    print("=" * 80)
    print("STABLEFORD RECALCULATION - CORRECTED (18-HOLE SI ALLOCATION)")
    print("=" * 80)
    
    # Get all rounds
    response = table.scan()
    all_rounds = sorted(response['Items'], key=lambda x: x['date'])
    
    # Build differential history
    diff_history = build_differential_history(all_rounds, 101, 33.5)
    
    # Rounds to recalculate (all with scorecard URLs)
    target_rounds = [r for r in all_rounds if r.get('scorecard_url') and r['date'] >= '2025-12-26']
    print(f"\nRounds to recalculate: {len(target_rounds)}")
    
    config = BACK_9_CONFIG
    all_changes = []
    db_updates = []
    
    for round_data in target_rounds:
        date = round_data['date']
        url = round_data.get('scorecard_url', '')
        
        print(f"\n{'='*80}")
        print(f"ROUND: {date} - {config['name']}")
        print(f"{'='*80}")
        
        # Scrape hole-by-hole scores
        scraped = scrape_hole_scores(url)
        if not scraped:
            print("  SKIPPING - could not scrape")
            continue
        
        for player in round_data.get('players', []):
            name = player['name']
            old_stableford = int(player.get('stableford', 0))
            old_whs = float(player.get('index', 0))
            gross = int(player.get('gross', 0))
            
            if gross == 0 or name not in scraped:
                continue
            
            scores = scraped[name]['scores']
            th_index = scraped[name]['th_index']
            th_hcp_strokes = scraped[name].get('th_hcp_strokes', [])
            th_stableford = scraped[name].get('th_stableford', [])
            
            # Calculate OLD CH (using Tag Heuer index)
            old_ch = calculate_course_handicap(th_index, config['slope_display'], config['rating_display'], config['par'])
            old_strokes = allocate_strokes_18hole_si(old_ch, BACK_9_SI)
            old_stableford_calc = calculate_stableford_per_hole(scores, BACK_9_PARS, old_strokes)
            old_stableford_total = sum(old_stableford_calc)
            
            # Get CORRECTED WHS at this date
            corrected_whs = get_corrected_whs_at_date(name, date, diff_history)
            if corrected_whs is None:
                print(f"  {name}: Insufficient history for corrected WHS")
                continue
            
            # Calculate NEW CH (using corrected WHS)
            new_ch = calculate_course_handicap(corrected_whs, config['slope_display'], config['rating_display'], config['par'])
            new_strokes = allocate_strokes_18hole_si(new_ch, BACK_9_SI)
            new_stableford_calc = calculate_stableford_per_hole(scores, BACK_9_PARS, new_strokes)
            new_stableford_total = sum(new_stableford_calc)
            
            change = new_stableford_total - old_stableford
            
            print(f"\n  {name}:")
            print(f"    Tag Heuer WHS: {th_index:>5.1f}  |  Old DB WHS: {old_whs:>5.1f}  |  Corrected WHS: {corrected_whs:>5.1f}")
            print(f"    Old CH: {old_ch:>2d} ({sum(old_strokes)} strokes)  |  New CH: {new_ch:>2d} ({sum(new_strokes)} strokes)  |  CH diff: {new_ch - old_ch:+d}")
            print(f"    Scores: {scores}  (Gross: {sum(s for s in scores if s)})")
            print(f"    SI:     {BACK_9_SI}")
            
            if th_hcp_strokes:
                print(f"    TH HCP strokes: {th_hcp_strokes} = {sum(th_hcp_strokes)}")
            print(f"    Old strokes:    {old_strokes} = {sum(old_strokes)}")
            print(f"    New strokes:    {new_strokes} = {sum(new_strokes)}")
            
            if th_stableford:
                print(f"    TH stableford:  {th_stableford} = {sum(th_stableford)}")
            print(f"    Old stableford: {old_stableford_calc} = {old_stableford_total}")
            print(f"    NEW stableford: {new_stableford_calc} = {new_stableford_total}")
            print(f"    DB value: {old_stableford}  ->  New: {new_stableford_total}  ({new_stableford_total - old_stableford:+d})")
            
            all_changes.append({
                'date': date,
                'name': name,
                'th_whs': th_index,
                'corrected_whs': corrected_whs,
                'old_ch': old_ch,
                'new_ch': new_ch,
                'old_stableford': old_stableford,
                'new_stableford': new_stableford_total,
                'change': new_stableford_total - old_stableford
            })
            
            if new_stableford_total != old_stableford:
                db_updates.append({
                    'date': date,
                    'player_name': name,
                    'old_stableford': old_stableford,
                    'new_stableford': new_stableford_total
                })
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY OF STABLEFORD CHANGES")
    print(f"{'='*80}\n")
    
    print(f"{'Date':<13} {'Player':<20} {'TH WHS':>7} {'New WHS':>8} {'Old CH':>7} {'New CH':>7} {'Old Stab':>9} {'New Stab':>9} {'Chg':>5}")
    print("-" * 100)
    
    for c in all_changes:
        marker = " <<<" if c['change'] != 0 else ""
        print(f"{c['date']:<13} {c['name']:<20} {c['th_whs']:>7.1f} {c['corrected_whs']:>8.1f} {c['old_ch']:>7d} {c['new_ch']:>7d} {c['old_stableford']:>9d} {c['new_stableford']:>9d} {c['change']:>+5d}{marker}")
    
    print(f"\n\nDB updates needed: {len(db_updates)}")
    for u in db_updates:
        print(f"  {u['date']} - {u['player_name']}: {u['old_stableford']} -> {u['new_stableford']} ({u['new_stableford'] - u['old_stableford']:+d})")
    
    if db_updates:
        print(f"\n⚠️  Ready to update {len(db_updates)} Stableford scores in DynamoDB.")
        answer = input("Proceed with updates? (yes/no): ").strip().lower()
        if answer == 'yes':
            updates_by_date = {}
            for u in db_updates:
                if u['date'] not in updates_by_date:
                    updates_by_date[u['date']] = []
                updates_by_date[u['date']].append(u)
            
            for date, updates in updates_by_date.items():
                response = table.get_item(Key={'date': date})
                round_data = response.get('Item')
                if not round_data:
                    continue
                players = round_data.get('players', [])
                for update in updates:
                    for i, p in enumerate(players):
                        if p['name'] == update['player_name']:
                            players[i]['stableford'] = update['new_stableford']
                            print(f"  Updated {date} - {update['player_name']}: {update['old_stableford']} -> {update['new_stableford']}")
                            break
                table.put_item(Item={**round_data, 'players': players})
            
            print("\n✅ All Stableford scores updated!")
        else:
            print("\n❌ No changes made.")
    else:
        print("\n✅ No Stableford changes needed - all values already correct!")


if __name__ == '__main__':
    main()
