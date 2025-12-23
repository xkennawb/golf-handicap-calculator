"""
AWS Lambda Function for Golf Handicap Tracker - iOS Shortcut Integration
Processes Tag Heuer Golf URLs and returns WhatsApp summary
"""

import json
import boto3
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from handicap import HandicapCalculator
import re
from decimal import Decimal
import urllib3

# Disable SSL warnings for local testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', verify=False)
table = dynamodb.Table('golf-rounds')

# Course configurations
# Note: These are 9-hole configurations
BACK_9_CONFIG = {
    'name': 'Back 9 (Holes 10-18)',
    'par': 35,  # 9-hole par (for course handicap display)
    'slope': 101,
    'rating': 33.5,  # 9-hole rating (actual course rating for index calculation)
    'rating_display': 35.5,  # Rating for course handicap display (slightly > par to match WHS system)
}

FRONT_9_CONFIG = {
    'name': 'Front 9 (Holes 1-9)',
    'par': 34,  # 9-hole par (for course handicap display)
    'slope': 101,
    'rating': 33.5,  # 9-hole rating (actual course rating for index calculation)
    'rating_display': 34.5,  # Rating for course handicap display (slightly > par to match WHS system)
}

def calculate_player_handicap_index(rounds_list, slope, rating):
    """
    Calculate WHS handicap index for a player using their rounds
    """
    hc_calc = HandicapCalculator()
    
    # Calculate differentials for all rounds
    differentials = []
    for round_data in rounds_list:
        # Calculate as 18-hole equivalent
        gross_18 = round_data['gross'] * 2
        rating_18 = rating * 2
        
        differential = (gross_18 - rating_18) * (113 / slope)
        differentials.append(round(differential, 1))
    
    # Calculate index using WHS method
    calculated_index = hc_calc.update_handicap_index(0, differentials)
    return calculated_index

def calculate_course_handicap(index, slope, rating, par):
    """USGA formula: CH = int((Index × Slope/113) + (Rating - Par))"""
    return int((index * slope / 113) + (rating - par))

def parse_tag_heuer_url(url):
    """
    Fetch and parse Tag Heuer Golf round data
    Returns: dict with date, course, players
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract date (example: "Friday November 07, 2025" or "Friday November 07, 2025 20:53")
        date_text = soup.find(string=re.compile(r'\w+ \w+ \d{2}, \d{4}'))
        if date_text:
            date_str_clean = date_text.strip()
            # Remove time suffix if present (e.g., " 20:53")
            date_str_clean = re.sub(r'\s+\d{2}:\d{2}$', '', date_str_clean)
            try:
                date_obj = datetime.strptime(date_str_clean, '%A %B %d, %Y')
                date_str = date_obj.strftime('%Y-%m-%d')
            except ValueError as e:
                return {'error': f'Failed to parse date: {date_str_clean} - {str(e)}'}
        else:
            return {'error': 'Could not parse date from Tag Heuer page'}
        
        # Determine course (Front 9 or Back 9)
        page_text = soup.get_text()
        
        # Check if this is an 18-hole scorecard (has both Out and In columns)
        has_out = 'Out' in page_text
        has_in = 'In' in page_text
        is_18_hole_card = has_out and has_in
        
        # For 18-hole cards, we'll need to determine which 9 holes were played
        # by checking the score columns
        # For now, default to back9 if we find numbers 10-18, otherwise front9
        if is_18_hole_card:
            # On 18-hole cards, default to back9 (we'll verify with actual scores below)
            course = 'back9'
            config = BACK_9_CONFIG
        elif 'HOLE 10 11 12 13 14 15 16 17 18' in page_text or re.search(r'\b10\b.*\b11\b.*\b12\b', page_text):
            course = 'back9'
            config = BACK_9_CONFIG
        else:
            course = 'front9'
            config = FRONT_9_CONFIG
        
        # Extract player data
        players = []
        
        # Find all player sections (looking for Index pattern)
        player_sections = soup.find_all(string=re.compile(r'\(Index \d+\.\d+\)'))
        
        for player_section in player_sections:
            # The player name is usually in the grandparent div, get its full text
            grandparent = player_section.parent.parent if player_section.parent else None
            if grandparent:
                player_text = grandparent.get_text().strip()
            else:
                player_text = str(player_section)
            
            # Extract player name and index from the full text
            match = re.search(r'(.+?)\s*\(Index\s+(\d+\.\d+)\)', player_text)
            if match:
                name = match.group(1).strip()
                index = float(match.group(2))
                
                # Find the score table for this player
                # The score table should be a sibling or nearby element
                parent = grandparent if grandparent else player_section.find_parent()
                if parent:
                    # Find the next score-table div
                    score_table = parent.find_next('div', class_='score-table')
                    if not score_table:
                        continue
                    
                    # Find all recap-cell divs (they contain Out, In, Total for scores and stableford)
                    recap_cells = score_table.find_all('div', class_='recap-cell')
                    if not recap_cells:
                        continue
                    
                    # Extract numeric values from recap cells
                    recap_values = []
                    for cell in recap_cells:
                        cell_text = cell.get_text().strip()
                        if cell_text and cell_text.isdigit():
                            recap_values.append(int(cell_text))
                    
                    # For 18-hole cards: recap cells are in order:
                    # [Out_score, In_score, Total_score, Out_putts, In_putts, Total_putts, 
                    #  Out_hcp, In_hcp, Total_hcp, Out_stableford, In_stableford, Total_stableford]
                    # For 9-hole cards: expect fewer values
                    if is_18_hole_card and len(recap_values) >= 12:
                        out_score = recap_values[0]
                        in_score = recap_values[1]
                        total_score = recap_values[2]
                        out_stableford = recap_values[9]
                        in_stableford = recap_values[10]
                        total_stableford = recap_values[11]
                        
                        # Determine which 9 holes were played
                        if in_score > 0 and out_score == 0:
                            gross = in_score
                            stableford = in_stableford
                            course = 'back9'
                            config = BACK_9_CONFIG
                        elif out_score > 0 and in_score == 0:
                            gross = out_score
                            stableford = out_stableford
                            course = 'front9'
                            config = FRONT_9_CONFIG
                        else:
                            # Both sides have scores, use total (18-hole round - not yet supported)
                            continue
                    elif recap_values:
                        # Simple 9-hole card, use last values
                        if len(recap_values) >= 2:
                            gross = recap_values[-2] if len(recap_values) >= 2 else recap_values[-1]
                            stableford = recap_values[-1]
                        else:
                            continue
                    else:
                        continue
                    
                    # Normalize player names
                    name_map = {
                        'Andy J.': 'Andy Jakes',
                        'Fletcher J.': 'Fletcher Jakes',
                        'Hamish M.': 'Hamish McNee',
                        'Bruce Kennaway': 'Bruce Kennaway',
                        'Steve': 'Steve'
                    }
                    
                    normalized_name = name_map.get(name, name)
                    
                    # Skip excluded players
                    if normalized_name in ['Eddie', 'Jo W.', 'Mark', 'Julian']:
                        continue
                    
                    players.append({
                        'name': normalized_name,
                        'index': Decimal(str(index)),
                        'gross': gross,
                        'stableford': stableford
                    })
        
        return {
            'date': date_str,
            'course': course,
            'players': players
        }
    
    except Exception as e:
        return {'error': f'Failed to parse Tag Heuer URL: {str(e)}'}

def get_all_rounds():
    """Retrieve all rounds from DynamoDB"""
    try:
        response = table.scan()
        rounds = response.get('Items', [])
        
        # Convert DynamoDB Decimal to float/int
        for round_data in rounds:
            for player in round_data.get('players', []):
                player['index'] = float(player['index'])
                player['gross'] = int(player['gross'])
                player['stableford'] = int(player['stableford'])
        
        # Sort by date
        rounds.sort(key=lambda x: x['date'])
        return rounds
    except Exception as e:
        print(f"Error retrieving rounds: {e}")
        return []

def check_duplicate_round(date_str):
    """Check if a round for this date already exists"""
    try:
        response = table.get_item(Key={'date': date_str})
        return 'Item' in response
    except Exception as e:
        print(f"Error checking for duplicate: {e}")
        return False

def is_recent_round(date_str):
    """Check if round is from today or recent (within 7 days)"""
    try:
        round_date = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.now()
        days_old = (today - round_date).days
        return days_old <= 7
    except Exception as e:
        print(f"Error checking round date: {e}")
        return False

def save_round(round_data):
    """Save round to DynamoDB"""
    try:
        table.put_item(Item=round_data)
        return True
    except Exception as e:
        print(f"Error saving round: {e}")
        return False

def generate_whatsapp_summary(rounds):
    """Generate WhatsApp formatted summary"""
    if not rounds:
        return "No rounds data available"
    
    # Get latest round
    latest_round = rounds[-1]
    latest_date_obj = datetime.strptime(latest_round['date'], '%Y-%m-%d')
    # Add 1 day for timezone
    latest_date_obj = latest_date_obj + timedelta(days=1)
    latest_date_str = latest_date_obj.strftime('%A, %B %d, %Y').upper()
    
    # Determine course
    if latest_round['course'] == 'back9':
        course_name = "BACK 9"
        config = BACK_9_CONFIG
    else:
        course_name = "FRONT 9"
        config = FRONT_9_CONFIG
    
    # Calculate season statistics
    player_stats = {}
    
    for round_data in rounds:
        # Get course config for this round
        if round_data['course'] == 'back9':
            round_config = BACK_9_CONFIG
        else:
            round_config = FRONT_9_CONFIG
        
        for player in round_data['players']:
            name = player['name']
            if name not in player_stats:
                player_stats[name] = {
                    'rounds': [],
                    'total_points': 0,
                    'total_gross': 0,
                    'best_stableford': 0,
                    'best_gross': 999,
                    'latest_index': 0,
                    'latest_ch': 0
                }
            
            player_stats[name]['rounds'].append(player)
            player_stats[name]['total_points'] += player['stableford']
            player_stats[name]['total_gross'] += player['gross']
            player_stats[name]['best_stableford'] = max(player_stats[name]['best_stableford'], player['stableford'])
            player_stats[name]['best_gross'] = min(player_stats[name]['best_gross'], player['gross'])
            player_stats[name]['latest_index'] = player['index']
    
    # Calculate actual handicap indexes for each player based on their rounds
    for name in player_stats:
        # Calculate handicap index from all their rounds
        calculated_index = calculate_player_handicap_index(
            player_stats[name]['rounds'],
            config['slope'],
            config['rating']
        )
        player_stats[name]['calculated_index'] = calculated_index
        
        # Calculate previous week's index (without today's round) for comparison
        if len(player_stats[name]['rounds']) > 1:
            prev_index = calculate_player_handicap_index(
                player_stats[name]['rounds'][:-1],
                config['slope'],
                config['rating']
            )
            prev_ch = calculate_course_handicap(
                prev_index,
                config['slope'],
                config.get('rating_display', config['rating']),
                config['par']
            )
            player_stats[name]['prev_index'] = prev_index
            player_stats[name]['prev_ch'] = prev_ch
        else:
            player_stats[name]['prev_index'] = calculated_index
            player_stats[name]['prev_ch'] = 0
        
        # Calculate course handicap for the latest course config
        ch = calculate_course_handicap(
            calculated_index,
            config['slope'],
            config.get('rating_display', config['rating']),
            config['par']
        )
        player_stats[name]['latest_ch'] = ch
    
    # Calculate averages
    for name in player_stats:
        rounds_count = len(player_stats[name]['rounds'])
        player_stats[name]['avg_stableford'] = player_stats[name]['total_points'] / rounds_count
        player_stats[name]['rounds_count'] = rounds_count
    
    # Sort by average
    sorted_players = sorted(player_stats.items(), key=lambda x: x[1]['avg_stableford'], reverse=True)
    
    # Build WhatsApp message
    message = f"📱 WARRINGAH SATURDAY GOLF\n"
    message += f"📅 {latest_date_str}\n\n"
    
    # Today's results
    message += "🏆 TODAY'S RESULTS:\n"
    latest_players = sorted(latest_round['players'], key=lambda x: x['stableford'], reverse=True)
    
    for rank, player in enumerate(latest_players, 1):
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        ch = calculate_course_handicap(
            player['index'],
            config['slope'],
            config.get('rating_display', config['rating']),
            config['par']
        )
        message += f"{emoji} {rank}. {player['name']} - {player['stableford']} points, {player['gross']} gross (Index: {player['index']}, Warringah: {ch})\n"
    
    # Season leaderboard
    message += "\n📊 2025 SEASON LEADERBOARD:\n\n"
    
    for rank, (name, stats) in enumerate(sorted_players, 1):
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        
        # Calculate changes
        index_change = stats['calculated_index'] - stats['prev_index']
        ch_change = stats['latest_ch'] - stats['prev_ch']
        
        # Format change indicators
        index_arrow = f" ({index_change:+.1f})" if abs(index_change) > 0.05 else ""
        ch_arrow = f" ({ch_change:+d})" if ch_change != 0 else ""
        
        message += f"{emoji} {rank}. {name}\n"
        message += f"      {stats['avg_stableford']:.2f} Stableford avg ({stats['rounds_count']} rounds)\n"
        message += f"      Index: {stats['calculated_index']:.1f}{index_arrow}, Warringah: {stats['latest_ch']}{ch_arrow}\n"
        message += f"      Personal Best: {stats['best_stableford']} pts, {stats['best_gross']} gross\n"
    
    return message

def lambda_handler(event, context):
    """
    Lambda handler
    Expected event format:
    {
        "action": "add_round",
        "url": "https://www.tagheuergolf.com/rounds/..."
    }
    OR
    {
        "action": "get_summary"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        # Determine action: if URL is provided, treat as add_round, otherwise get_summary
        url = body.get('url')
        action = body.get('action')
        
        # Auto-detect action based on presence of URL
        if url and not action:
            action = 'add_round'
        elif not action:
            action = 'get_summary'
        
        if action == 'add_round':
            if not url:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'URL is required'})
                }
            
            # Parse Tag Heuer URL
            round_data = parse_tag_heuer_url(url)
            
            if 'error' in round_data:
                return {
                    'statusCode': 400,
                    'body': json.dumps(round_data)
                }
            
            # Check if round is too old
            if not is_recent_round(round_data['date']):
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Round is more than 7 days old. Only recent rounds can be submitted.'})
                }
            
            # Check for duplicates
            if check_duplicate_round(round_data['date']):
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'A round for this date already exists. Duplicate submission prevented.'})
                }
            
            # Save to DynamoDB
            save_round(round_data)
        
        # Get all rounds and generate summary
        rounds = get_all_rounds()
        summary = generate_whatsapp_summary(rounds)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'summary': summary,
                'rounds_count': len(rounds)
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
