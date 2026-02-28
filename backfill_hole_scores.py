"""
One-time backfill: Add hole_scores to all historical rounds in DynamoDB.

Scrapes Tag Heuer scorecard URLs to extract hole-by-hole scores and stores
them permanently in each player's round data. This means future Lambda
invocations won't need to re-scrape for best/worst hole stats.

Usage:
    python backfill_hole_scores.py          # Dry run (preview changes)
    python backfill_hole_scores.py --apply  # Apply changes to DynamoDB
"""
import boto3
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from load_credentials import load_credentials
import re
import sys
import urllib3

urllib3.disable_warnings()
load_credentials()

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', verify=False)
table = dynamodb.Table('golf-rounds')

NAME_MAP = {
    'Andy J.': 'Andy Jakes',
    'Fletcher J.': 'Fletcher Jakes',
    'Hamish M.': 'Hamish McNee',
    'Bruce Kennaway': 'Bruce Kennaway',
    'Steve': 'Steve',
    'Steve Lewthwaite': 'Steve',
    'Steve L.': 'Steve',
}


def scrape_hole_scores(url):
    """Scrape Tag Heuer scorecard for all players' hole-by-hole scores."""
    response = requests.get(url, timeout=15, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    players = {}
    player_sections = soup.find_all(string=re.compile(r'\(Index \d+\.\d+\)'))
    
    for ps in player_sections:
        gp = ps.parent.parent if ps.parent else None
        if not gp:
            continue
        pt = gp.get_text().strip()
        match = re.search(r'(.+?)\s*\(Index\s+(\d+\.\d+)\)', pt)
        if not match:
            continue
        
        name = NAME_MAP.get(match.group(1).strip(), match.group(1).strip())
        if name in players:
            continue
        if name in ['Eddie', 'Jo W.', 'Mark', 'Julian']:
            continue
        
        score_table = gp.find_next('div', class_='score-table')
        if not score_table:
            continue
        
        for row in score_table.find_all('div', recursive=False):
            cells = row.find_all('div')
            texts = [c.get_text().strip() for c in cells]
            if not texts or texts[0] != 'Score':
                continue
            
            all_vals = texts[1::2]
            if len(all_vals) >= 19:  # 18-hole card
                players[name] = {
                    'front9': [int(v) if v and v.isdigit() else 0 for v in all_vals[0:9]],
                    'back9': [int(v) if v and v.isdigit() else 0 for v in all_vals[10:19]],
                }
            elif len(all_vals) >= 9:  # 9-hole card
                players[name] = {
                    'back9': [int(v) if v and v.isdigit() else 0 for v in all_vals[:9]],
                }
            break
    
    return players


def main():
    apply = '--apply' in sys.argv
    
    print("=" * 70)
    print("BACKFILL HOLE SCORES")
    print(f"Mode: {'APPLY (writing to DynamoDB)' if apply else 'DRY RUN (preview only)'}")
    print("=" * 70)
    
    # Get all rounds
    response = table.scan()
    all_rounds = sorted(response['Items'], key=lambda x: x['date'])
    
    total = 0
    already_has = 0
    no_url = 0
    updated = 0
    failed = 0
    
    for round_data in all_rounds:
        total += 1
        date = round_data['date']
        url = round_data.get('scorecard_url')
        
        # Check if any player already has hole_scores
        has_scores = any(p.get('hole_scores') for p in round_data.get('players', []))
        if has_scores:
            already_has += 1
            print(f"  ✅ {date} - already has hole_scores")
            continue
        
        if not url:
            no_url += 1
            print(f"  ⚠️  {date} - no scorecard URL")
            continue
        
        # Scrape hole scores
        try:
            scraped = scrape_hole_scores(url)
            if not scraped:
                failed += 1
                print(f"  ❌ {date} - scrape returned no data")
                continue
            
            # Determine which 9 this round is
            is_back9 = round_data['course'] == 'back9' or '-back9' in date
            nine = 'back9' if is_back9 else 'front9'
            
            # Match scraped scores to players in the round
            players = round_data.get('players', [])
            matched = 0
            for player in players:
                name = player['name']
                if name in scraped and nine in scraped[name]:
                    scores = scraped[name][nine]
                    if len(scores) == 9 and any(s > 0 for s in scores):
                        player['hole_scores'] = [Decimal(str(s)) for s in scores]
                        matched += 1
                        print(f"  📝 {date} - {name}: {scores}")
            
            if matched > 0:
                if apply:
                    table.put_item(Item=round_data)
                    print(f"  💾 {date} - saved {matched} players")
                else:
                    print(f"  🔍 {date} - would save {matched} players (dry run)")
                updated += 1
            else:
                failed += 1
                print(f"  ❌ {date} - no player scores matched")
        
        except Exception as e:
            failed += 1
            print(f"  ❌ {date} - error: {e}")
    
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total rounds:           {total}")
    print(f"Already had hole_scores: {already_has}")
    print(f"No scorecard URL:       {no_url}")
    print(f"Updated:                {updated}")
    print(f"Failed:                 {failed}")
    
    if not apply and updated > 0:
        print(f"\n⚠️  Run with --apply to write changes to DynamoDB:")
        print(f"    python backfill_hole_scores.py --apply")


if __name__ == '__main__':
    main()
