"""
AWS Lambda Function for Golf Handicap Tracker - iOS Shortcut Integration
Processes Tag Heuer Golf URLs and returns WhatsApp summary with AI commentary
"""

import json
import boto3
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from handicap import HandicapCalculator
import re
from decimal import Decimal
import os

# OpenAI setup
try:
    from openai import OpenAI
    OPENAI_ENABLED = True
    print("✓ OpenAI imported successfully")
except ImportError as e:
    OPENAI_ENABLED = False
    print(f"✗ OpenAI not available - ImportError: {e}")
except Exception as e:
    OPENAI_ENABLED = False
    print(f"✗ OpenAI not available - Error: {type(e).__name__}: {e}")

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('golf-rounds')

# Simple in-memory cache for commentary (Lambda container reuse)
commentary_cache = {}

def parse_date_flexible(date_str):
    """
    Parse date string flexibly to handle formats like:
    - 2025-12-22 (standard)
    - 2025-12-22-back9 (multiple rounds same day)
    Returns datetime object or uses actual_date field if available
    """
    try:
        # Try standard format first
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        # Try extracting just the date part (YYYY-MM-DD) from strings like "2025-12-22-back9"
        match = re.match(r'(\d{4}-\d{2}-\d{2})', date_str)
        if match:
            return datetime.strptime(match.group(1), '%Y-%m-%d')
        raise ValueError(f"Cannot parse date: {date_str}")

def get_weather_for_round(round_date, tee_time_utc=None):
    """
    Fetch historical weather data for the round using Open-Meteo API (free, no key needed)
    Always uses morning weather (8am Sydney time) for typical golf rounds
    If tee_time_utc provided, uses that specific hour
    Returns simple weather description string or None
    """
    try:
        # Warringah Golf Club coordinates (North Manly, Sydney)
        latitude = -33.7544
        longitude = 151.2677
        
        # Parse the date string (format: "2025-12-05")
        if isinstance(round_date, str):
            date_str = round_date
        else:
            date_str = round_date.strftime('%Y-%m-%d')
        
        # Determine which hour to fetch (default to 8am Sydney time)
        local_hour = 8  # Default morning tee time
        
        # If we have tee time, convert UTC to Sydney time
        if tee_time_utc:
            try:
                # Parse UTC time (format: "21:30")
                hour, minute = map(int, tee_time_utc.split(':'))
                # Sydney is UTC+10 (or UTC+11 during daylight saving)
                # Approximate with +11 for summer months (Oct-Apr)
                month = int(date_str.split('-')[1])
                offset = 11 if month >= 10 or month <= 4 else 10
                local_hour = (hour + offset) % 24
                print(f"DEBUG: Converted UTC {tee_time_utc} to Sydney hour {local_hour}")
            except Exception as e:
                print(f"DEBUG: Tee time conversion error, using 8am default: {e}")
                local_hour = 8
        
        # Open-Meteo hourly historical weather API
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': date_str,
            'end_date': date_str,
            'hourly': 'temperature_2m,windspeed_10m,precipitation,weathercode',
            'timezone': 'Australia/Sydney'
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Extract hourly data for the tee time
        hourly = data['hourly']
        temp = round(hourly['temperature_2m'][local_hour])
        wind = round(hourly['windspeed_10m'][local_hour])
        rain = hourly['precipitation'][local_hour]
        
        # Weather description from code
        weather_code = hourly['weathercode'][local_hour]
        weather_desc = {
            0: 'clear skies', 1: 'mainly clear', 2: 'partly cloudy', 3: 'overcast',
            45: 'foggy', 48: 'foggy', 51: 'light drizzle', 53: 'drizzle', 55: 'heavy drizzle',
            61: 'light rain', 63: 'rain', 65: 'heavy rain', 71: 'light snow', 73: 'snow',
            75: 'heavy snow', 80: 'rain showers', 81: 'showers', 82: 'heavy showers',
            95: 'thunderstorm', 96: 'thunderstorm with hail', 99: 'severe thunderstorm'
        }.get(weather_code, 'mixed conditions')
        
        rain_text = f", {rain}mm rain" if rain > 0 else ""
        return f"{temp}°C, {weather_desc}, {wind}km/h winds{rain_text}"
        
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None

# Course configurations
# NOTE: Labels in database are BACKWARDS - "front9" in DB = Back 9 in reality
BACK_9_CONFIG = {
    'name': 'Back 9 (Holes 10-18)',
    'par': 35,
    'slope': 101,  # For index calculation (keeps existing handicaps stable)
    'rating': 33.5,  # For index calculation (keeps existing handicaps stable)
    'slope_display': 111,  # Warringah Whites official - for course handicap display only
    'rating_display': 33.0,  # Warringah Whites official - for course handicap display only
}

FRONT_9_CONFIG = {
    'name': 'Front 9 (Holes 1-9)',
    'par': 35,  # Front 9 par is 35
    'slope': 101,  # For index calculation (keeps existing handicaps stable)
    'rating': 33.5,  # For index calculation (keeps existing handicaps stable)
    'slope_display': 127,  # Warringah Whites official - for course handicap display only
    'rating_display': 35.0,  # Warringah Whites official - for course handicap display only
}

def calculate_course_handicap(index, slope, rating, par):
    """
    WHS Course Handicap Formula: CH = round(Index × Slope/113 + (Rating - Par))
    Uses official Warringah Whites ratings from Tag Heuer
    """
    ch = round(float(index) * slope / 113 + (rating - par))
    return max(0, ch)

def estimate_pcc_from_weather(weather_string):
    """
    Estimate Playing Conditions Calculation (PCC) adjustment based on weather.
    Returns -1, 0, or +1 adjustment to apply to score differential.
    
    WHS PCC is officially calculated by Golf Australia using all scores,
    but we estimate based on weather:
    - Heavy rain (>10mm) or strong winds (>30km/h) = +1 (harder conditions)
    - Normal conditions = 0
    - Perfect conditions = 0 (we don't go negative)
    """
    if not weather_string:
        return 0
    
    try:
        # Extract rain amount (format: "20°C, rain, 15km/h winds, 12.5mm rain")
        import re
        rain_match = re.search(r'(\d+\.?\d*)mm rain', weather_string)
        wind_match = re.search(r'(\d+)km/h winds', weather_string)
        
        rain = float(rain_match.group(1)) if rain_match else 0
        wind = int(wind_match.group(1)) if wind_match else 0
        
        # Check for adverse conditions
        if rain > 10:  # Heavy rain
            return 1
        elif wind > 30:  # Strong winds
            return 1
        else:
            return 0
    except Exception as e:
        print(f"DEBUG: PCC estimation error: {e}")
        return 0

def calculate_player_handicap_index(rounds_list, slope, rating):
    """
    Calculate WHS handicap index for a player using their rounds
    Weather-based PCC only applied to rounds after 2025-12-14
    Applies hard/soft cap based on Low Handicap Index from last 365 days
    """
    hc_calc = HandicapCalculator()
    
    # PCC cutoff date - only apply to rounds after this
    PCC_START_DATE = "2025-12-14"
    
    # Calculate differentials for all rounds
    differentials = []
    round_indices = []  # Track index after each round for LHI calculation
    
    for round_data in rounds_list:
        # Calculate as 18-hole equivalent
        gross_18 = round_data['gross'] * 2
        rating_18 = rating * 2
        
        differential = (gross_18 - rating_18) * (113 / slope)
        
        # Apply weather-based PCC ONLY for rounds after Dec 14, 2025
        if 'date' in round_data and round_data['date'] > PCC_START_DATE:
            if 'weather' in round_data and round_data['weather']:
                pcc = estimate_pcc_from_weather(round_data['weather'])
                if pcc != 0:
                    differential += pcc
                    print(f"DEBUG: Applied PCC {pcc:+d} for {round_data['date']}: {round_data['weather'][:50]}")
        
        differentials.append(round(differential, 1))
    
    # Calculate Low Handicap Index from last 365 days
    from datetime import datetime, timedelta
    cutoff_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Get indices from rounds in last 365 days
    low_handicap_index = None
    recent_indices = []
    
    for i, round_data in enumerate(rounds_list):
        if round_data.get('date', '') >= cutoff_date:
            # Calculate index up to this point
            temp_index = hc_calc.update_handicap_index(0, differentials[:i+1])
            recent_indices.append(temp_index)
    
    if recent_indices:
        low_handicap_index = min(recent_indices)
    
    # Calculate final index using WHS method with hard/soft cap
    calculated_index = hc_calc.update_handicap_index(0, differentials, low_handicap_index=low_handicap_index)
    return calculated_index

def parse_tag_heuer_url(url):
    """
    Fetch and parse Tag Heuer Golf round data
    Returns: dict with date, course, players, url
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract date (example: "Friday November 07, 2025" or "Friday November 07, 2025 20:53")
        date_text = soup.find(string=re.compile(r'\w+ \w+ \d{2}, \d{4}'))
        tee_time_utc = None
        
        if date_text:
            date_str_clean = date_text.strip()
            # Extract time if present (UTC format)
            time_match = re.search(r'(\d{2}:\d{2})$', date_str_clean)
            if time_match:
                tee_time_utc = time_match.group(1)
            # Remove time suffix for date parsing
            date_str_clean = re.sub(r'\s+\d{2}:\d{2}$', '', date_str_clean)
            try:
                date_obj = datetime.strptime(date_str_clean, '%A %B %d, %Y')
                date_str = date_obj.strftime('%Y-%m-%d')
            except ValueError as e:
                return {
                    'error': f'❌ DATE FORMAT CHANGED: Could not parse "{date_str_clean}". Tag Heuer may have changed their date format. Error: {str(e)}',
                    'error_type': 'DATE_PARSE_ERROR'
                }
        else:
            return {
                'error': '❌ DATE NOT FOUND: Could not find date on Tag Heuer page. The page structure may have changed.',
                'error_type': 'DATE_NOT_FOUND'
            }
        
        # Determine course (Front 9 or Back 9)
        page_text = soup.get_text()
        
        # Check if this is an 18-hole scorecard (has both Out and In columns)
        has_out = 'Out' in page_text
        has_in = 'In' in page_text
        is_18_hole_card = has_out and has_in
        
        # For 18-hole cards, default to back9 (we'll determine actual 9 from scores)
        if is_18_hole_card:
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
        
        if not player_sections:
            return {
                'error': '❌ NO PLAYERS FOUND: Could not find any player data. Tag Heuer may have changed their scorecard format (looking for "Index X.X" pattern).',
                'error_type': 'NO_PLAYERS_FOUND'
            }
        
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
                    recap_cells_text = []  # Keep all text for debugging
                    for cell in recap_cells:
                        cell_text = cell.get_text().strip()
                        recap_cells_text.append(cell_text)  # Store all text
                        if cell_text and cell_text.isdigit():
                            recap_values.append(int(cell_text))
                    
                    print(f"DEBUG {name}: All recap cells = {recap_cells_text}")
                    print(f"DEBUG {name}: Numeric values = {recap_values}")
                    
                    # For 18-hole cards: recap cells are in order:
                    # [Out_score, In_score, Total_score, Out_putts, In_putts, Total_putts, 
                    #  Out_hcp, In_hcp, Total_hcp, Out_stableford, In_stableford, Total_stableford]
                    # Stableford is indices 9, 10, 11
                    if is_18_hole_card and len(recap_values) >= 12:
                        out_score = recap_values[0]
                        in_score = recap_values[1]
                        out_stableford = recap_values[9]
                        in_stableford = recap_values[10]
                        
                        print(f"DEBUG {name}: recap_values = {recap_values}")
                        print(f"DEBUG {name}: OUT={out_score}, IN={in_score}, OUT_stab={out_stableford}, IN_stab={in_stableford}")
                        
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
                            # Both sides have scores - this is a full 18-hole round!
                            # Store both front 9 and back 9 data for this player
                            gross = 'SPLIT_18'  # Special marker
                            stableford = 'SPLIT_18'
                            # Store the data for splitting later
                            front9_data = {
                                'gross': out_score,
                                'stableford': out_stableford
                            }
                            back9_data = {
                                'gross': in_score,
                                'stableford': in_stableford
                            }
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
                    
                    if 'gross' in locals() and 'stableford' in locals():
                        # Check if this is a split 18-hole player
                        if gross == 'SPLIT_18' and stableford == 'SPLIT_18':
                            # Add to player list with split marker and both 9s data
                            players.append({
                                'name': normalized_name,
                                'index': Decimal(str(index)),
                                'split_18': True,
                                'front9': front9_data,
                                'back9': back9_data
                            })
                        else:
                            # Regular 9-hole player
                            players.append({
                                'name': normalized_name,
                                'index': Decimal(str(index)),
                                'gross': gross,
                                'stableford': stableford
                            })
        
        # Check if we found any valid players
        if not players:
            return {
                'error': '❌ SCORE PARSING FAILED: Found player names but could not extract scores. Tag Heuer scorecard format may have changed (score-table or recap-cell structure).',
                'error_type': 'SCORE_PARSE_ERROR'
            }
        
        # Check if any players have split 18-hole data
        has_split_players = any(p.get('split_18', False) for p in players)
        
        if has_split_players:
            # Create two separate rounds: front 9 and back 9
            front9_players = []
            back9_players = []
            
            for player in players:
                if player.get('split_18', False):
                    # Split this player into two rounds
                    front9_players.append({
                        'name': player['name'],
                        'index': player['index'],
                        'gross': player['front9']['gross'],
                        'stableford': player['front9']['stableford']
                    })
                    back9_players.append({
                        'name': player['name'],
                        'index': player['index'],
                        'gross': player['back9']['gross'],
                        'stableford': player['back9']['stableford']
                    })
                else:
                    # This player only played one 9, add them to the appropriate round
                    # Determine which round based on course variable
                    if course == 'front9':
                        front9_players.append(player)
                    else:
                        back9_players.append(player)
            
            # Return list of two rounds
            rounds = []
            if front9_players:
                rounds.append({
                    'date': date_str,
                    'time_utc': tee_time_utc,
                    'course': 'front9',
                    'players': front9_players,
                    'scorecard_url': url
                })
            if back9_players:
                rounds.append({
                    'date': date_str,
                    'time_utc': tee_time_utc,
                    'course': 'back9',
                    'players': back9_players,
                    'scorecard_url': url
                })
            
            return rounds  # Return list of rounds
        
        # Single 9-hole round
        return {
            'date': date_str,
            'time_utc': tee_time_utc,
            'course': course,
            'players': players,
            'scorecard_url': url
        }
    
    except Exception as e:
        return {
            'error': f'❌ PARSING ERROR: {str(e)}. This likely means Tag Heuer has changed their scorecard format.',
            'error_type': 'GENERAL_PARSE_ERROR',
            'details': str(e)
        }

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
        round_date = parse_date_flexible(date_str)
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

def generate_ai_commentary(todays_rounds, sorted_players, season_leaderboard=None, form_data=None, prediction_text=None, handicap_changes=None):
    """
    Generate humorous AI commentary about the round(s)
    todays_rounds: list of rounds from today (could be 1 for 9 holes, or 2 for 18 holes)
    Returns None if OpenAI unavailable or on error
    """
    print(f"DEBUG: generate_ai_commentary called, OPENAI_ENABLED={OPENAI_ENABLED}")
    
    if not OPENAI_ENABLED:
        print("DEBUG: OpenAI library not available")
        return None
    
    api_key = os.environ.get('OPENAI_API_KEY')
    print(f"DEBUG: API key present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
    
    if not api_key:
        print("OpenAI API key not configured")
        return None
    
    # Use latest round for cache key
    latest_round = todays_rounds[-1]
    
    # Check cache (5 minute TTL)
    cache_key = f"{latest_round['date']}"
    if cache_key in commentary_cache:
        cached_time, cached_commentary = commentary_cache[cache_key]
        if (datetime.now() - cached_time).seconds < 300:  # 5 minutes
            print("Using cached commentary")
            return cached_commentary
    
    try:
        # Build context for AI - include ALL rounds from today
        player_info = []
        
        # If 18 holes (2 rounds), show both with very explicit labeling
        if len(todays_rounds) == 2:
            # Determine front 9 and back 9 by checking date suffix or course field
            front9_round = None
            back9_round = None
            
            for r in todays_rounds:
                if '-back9' in r['date']:
                    back9_round = r
                elif r['course'] == 'back9':
                    back9_round = r
                else:
                    front9_round = r
            
            # Fallback if logic doesn't work
            if not front9_round:
                front9_round = todays_rounds[0]
            if not back9_round:
                back9_round = todays_rounds[1]
            
            player_info.append("===== FRONT 9 SCORES =====")
            for p in front9_round['players']:
                player_info.append(f"{p['name']}: {p['stableford']} points on FRONT 9, {p['gross']} gross on FRONT 9")
            
            player_info.append("\n===== BACK 9 SCORES =====")
            for p in back9_round['players']:
                player_info.append(f"{p['name']}: {p['stableford']} points on BACK 9, {p['gross']} gross on BACK 9")
        else:
            # Single 9-hole round - determine by date suffix or course field
            if '-back9' in todays_rounds[0]['date'] or todays_rounds[0]['course'] == 'back9':
                round_label = "===== BACK 9 SCORES ====="
                nine_label = "BACK 9"
            else:
                round_label = "===== FRONT 9 SCORES ====="
                nine_label = "FRONT 9"
                
            player_info.append(round_label)
            for p in todays_rounds[0]['players']:
                player_info.append(f"{p['name']}: {p['stableford']} points on {nine_label}, {p['gross']} gross on {nine_label}")
        
        # Get weather if available (with tee time if present)
        tee_time = latest_round.get('time_utc')
        print(f"DEBUG: Round date={latest_round['date']}, tee_time_utc={tee_time}")
        weather_info = get_weather_for_round(latest_round['date'], tee_time)
        print(f"DEBUG: Weather fetched: {weather_info}")
        
        # Add weather emoji based on conditions
        weather_emoji = ""
        if weather_info:
            weather_lower = weather_info.lower()
            # Check sky conditions first
            if 'rain' in weather_lower or 'shower' in weather_lower:
                weather_emoji = "🌧️"
            elif 'storm' in weather_lower or 'thunder' in weather_lower:
                weather_emoji = "⛈️"
            elif 'partly cloudy' in weather_lower or 'partly cloud' in weather_lower:
                weather_emoji = "⛅"
            elif 'cloud' in weather_lower or 'overcast' in weather_lower:
                weather_emoji = "☁️"
            elif 'clear' in weather_lower or 'sunny' in weather_lower or 'sun' in weather_lower:
                weather_emoji = "☀️"
            else:
                # Default sunny emoji if no sky condition detected
                weather_emoji = "☀️"
            
            # Add wind emoji if mentioned
            if 'strong wind' in weather_lower or 'gust' in weather_lower or 'windy' in weather_lower:
                weather_emoji += " 💨"
            elif 'wind' in weather_lower or 'breeze' in weather_lower:
                weather_emoji += " 🍃"
            
            weather_emoji += " "  # Add space after emoji
        
        weather_text = f"\nWeather: {weather_emoji}{weather_info}" if weather_info else ""
        
        # Build season leaderboard text if available - only include qualified players (10+ rounds)
        season_text = ""
        qualified_leaders = []
        if season_leaderboard:
            # Filter to only qualified players (10+ rounds)
            for name, stats in season_leaderboard:
                if stats['rounds_count'] >= 10:
                    qualified_leaders.append((name, stats))
            
            # Get current year from latest round date
            current_year = parse_date_flexible(latest_round['date']).year
            season_text = f"\n\n{current_year} Season Standings (QUALIFIED PLAYERS ONLY - 10+ rounds):\n"
            for rank, (name, stats) in enumerate(qualified_leaders[:5], 1):  # Top 5 qualified
                season_text += f"{rank}. {name}: {stats['avg_stableford']:.1f} avg, {stats['rounds_count']} rounds, {stats['total_points']} total pts\n"
            
            season_text += "\nNOTE: Players with fewer than 10 rounds are marked DNQ (Did Not Qualify) and should NOT be mentioned as 'leading' or 'top of' the standings.\n"
        
        # Check if both Fletcher and Andy are playing (father-son dynamic)
        # Check across all rounds from today
        all_player_names = []
        for round_data in todays_rounds:
            all_player_names.extend([p['name'] for p in round_data['players']])
        has_father_son = 'Fletcher Jakes' in all_player_names and 'Andy Jakes' in all_player_names
        
        # Build relationship context - always include to avoid confusion
        relationship_text = "\nIMPORTANT PLAYER RELATIONSHIPS - DO NOT GET THIS WRONG:\n- Fletcher Jakes is Andy Jakes' SON (Andy is the father, Fletcher is his son)\n- Bruce Kennaway is NOT related to Fletcher or Andy\n- DO NOT call Fletcher and Andy brothers - they are father and son\n"
        
        # Add form/prediction context if available - only for players who played today
        form_text = ""
        if form_data:
            # Filter form data to only include today's players
            todays_player_names = set(all_player_names)
            form_text = "\n\nRecent Form (last 5 rounds) - for today's players only:\n"
            for name, data in form_data.items():
                if name in todays_player_names:
                    form_text += f"- {name}: {data['trend']} {data['avg']:.1f} avg\n"
        
        prediction_context = f"\n\nPrediction: {prediction_text}\n" if prediction_text else ""
        
        # Add handicap changes context
        handicap_context = handicap_changes if handicap_changes else ""
        
        # Add 18-hole context if applicable
        holes_context = ""
        if len(todays_rounds) == 2:
            holes_context = "\nNOTE: This was an 18-hole round (front 9 and back 9). Comment on both nines in your banter.\n"
        
        # Get list of today's players for the prompt
        unique_players_today = list(set(all_player_names))
        players_today_text = f"\n\nPLAYERS WHO PLAYED TODAY: {', '.join(unique_players_today)}\nONLY mention these players in your banter section.\n"
        
        # Check if this is the final round of the season (late December)
        round_date = parse_date_flexible(latest_round['date'])
        is_season_finale = round_date.month == 12 and round_date.day >= 20
        
        # Add season champion context if this is the finale
        champion_text = ""
        if is_season_finale and qualified_leaders:
            # Andy Jakes is the champion (first in qualified leaders)
            champion_name = qualified_leaders[0][0]
            champion_stats = qualified_leaders[0][1]
            champion_text = f"\n\n🏆 SEASON FINALE - 2025 CHAMPION: {champion_name} wins the 2025 Warringah season title with {champion_stats['avg_stableford']:.1f} average points over {champion_stats['rounds_count']} rounds! Make sure to mention this achievement in your season summary.\n"
        
        prompt = f"""Generate a golf round commentary with THREE distinct parts:

1. WEATHER LINE (purely factual, no commentary): Simply state the weather conditions at Warringah Golf Club. Just the facts.
2. PLAYER BANTER (humorous): 2-3 sentences of witty commentary about the players who PLAYED TODAY. Only mention players from the "PLAYERS WHO PLAYED TODAY" list. DO NOT mention any other players in the banter section. DO NOT mention weather, temperature, conditions, wind, rain, or anything weather-related in this section. Reference their recent form if relevant. IMPORTANT: If there are handicap changes listed below, you MUST mention them in your banter - this is significant news that should not be ignored.
3. SEASON SUMMARY (1 sentence): A brief, witty observation about the overall season leaderboard standings. You may mention any player in the season standings here. IMPORTANT: If a prediction is provided below, you MUST include it by mentioning who the next game favorite is based on their recent form.
{relationship_text}{players_today_text}{champion_text}{holes_context}{form_text}{handicap_context}{prediction_context}
Today's Results:
{chr(10).join(player_info)}{weather_text}{season_text}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. The scores above explicitly state "on FRONT 9" or "on BACK 9" next to each score
2. DO NOT mix up which scores belong to which nine
3. If a player scored X points "on FRONT 9", do not say they scored X points on the back 9
4. Each line clearly states which nine the score is from - read it carefully
5. Example: "Steve: 20 points on FRONT 9" means Steve scored 20 on the FRONT nine, NOT the back nine

Format:
Weather: [temperature, conditions, wind - factual only, no jokes]

[humorous commentary mentioning ALL players by name - ZERO weather references - BE PRECISE about which nine each score was on]

[one sentence about season standings]

Example:
Weather: 18°C with partly cloudy skies and 15km/h winds.

Andy's 16 points lead the pack, Bruce's 14 keeps him in the hunt, while Hamish and Fletcher battle it out for the remaining spots!

Andy maintains his stranglehold on the season with a commanding average, while the pack scrambles to keep pace!"""

        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a golf commentator. Write ONE factual weather sentence, then humorous sentences about ALL players mentioned, then ONE sentence about season standings. NEVER mention weather in the player commentary."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.8,
            timeout=10  # 10 second timeout
        )
        
        print(f"DEBUG: OpenAI API call successful")
        commentary = response.choices[0].message.content.strip()
        print(f"DEBUG: Commentary generated: {commentary[:50]}...")
        
        # Cache it
        commentary_cache[cache_key] = (datetime.now(), commentary)
        
        # Clean up old cache entries (keep last 10)
        if len(commentary_cache) > 10:
            oldest_key = min(commentary_cache.keys(), key=lambda k: commentary_cache[k][0])
            del commentary_cache[oldest_key]
        
        return commentary
        
    except Exception as e:
        print(f"ERROR generating AI commentary: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_whatsapp_summary(rounds, specific_date=None):
    """Generate WhatsApp formatted summary
    
    Args:
        rounds: List of all rounds
        specific_date: Optional specific date (YYYY-MM-DD) to generate summary for
    """
    if not rounds:
        return "No rounds data available"
    
    # If specific date provided, filter rounds up to that date and use it as "latest"
    if specific_date:
        print(f"Generating summary for specific date: {specific_date}")
        # Convert specific_date to datetime for comparison
        target_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
        
        # Filter rounds up to and including the specific date
        filtered_rounds = []
        for r in rounds:
            round_date = parse_date_flexible(r['date']).date()
            if round_date <= target_date:
                filtered_rounds.append(r)
        
        if not filtered_rounds:
            return f"No rounds found on or before {specific_date}"
        
        rounds = filtered_rounds
        print(f"Filtered to {len(rounds)} rounds up to {specific_date}")
    
    # Get latest round(s) - could be multiple if 18 holes played on same day
    latest_round = rounds[-1]
    latest_date_obj = parse_date_flexible(latest_round['date'])
    # Add 1 day for timezone
    latest_date_obj = latest_date_obj + timedelta(days=1)
    latest_date_str = latest_date_obj.strftime('%A, %B %d, %Y').upper()
    
    # Find all rounds from the latest date (front 9 and back 9 on same day)
    latest_date_base = latest_round['date'].split('-back9')[0]  # Remove suffix if present
    todays_rounds = [r for r in rounds if r['date'].split('-back9')[0] == latest_date_base]
    
    # Determine course (use last round's config for handicap calculations)
    if latest_round['course'] == 'back9':
        course_name = "BACK 9"
        config = BACK_9_CONFIG
    else:
        course_name = "FRONT 9"
        config = FRONT_9_CONFIG
    
    # Calculate season statistics
    player_stats = {}
    
    # Get current year for season filtering
    current_year = latest_date_obj.year
    
    for round_data in rounds:
        # Parse round date to check year
        round_date = parse_date_flexible(round_data['date'])
        round_year = round_date.year
        
        # Get course config for this round
        if round_data['course'] == 'back9':
            round_config = BACK_9_CONFIG
        else:
            round_config = FRONT_9_CONFIG
        
        # Check if this round is eligible for handicap calculation
        handicap_eligible = round_data.get('handicap_eligible', True)  # Default to True for existing rounds
        
        for player in round_data['players']:
            name = player['name']
            if name not in player_stats:
                player_stats[name] = {
                    'rounds': [],  # Only handicap-eligible rounds
                    'season_rounds': [],  # Current year only for average (includes all courses)
                    'total_points': 0,  # Current year only
                    'total_gross': 0,  # Current year only
                    'best_stableford': 0,  # All-time PB
                    'best_gross': 999,  # All-time PB
                    'latest_index': 0,
                    'latest_ch': 0
                }
            
            # Only add to handicap rounds if eligible
            if handicap_eligible:
                player_stats[name]['rounds'].append(player)
                player_stats[name]['latest_index'] = player['index']
            
            # Only add to season stats if it's current year (includes ALL courses)
            if round_year == current_year:
                player_stats[name]['season_rounds'].append(player)
                player_stats[name]['total_points'] += player['stableford']
                if handicap_eligible:  # Only track gross for handicap-eligible rounds
                    player_stats[name]['total_gross'] += player['gross']
            
            # All-time PBs (only from handicap-eligible rounds with valid scores)
            if handicap_eligible:
                player_stats[name]['best_stableford'] = max(player_stats[name]['best_stableford'], player['stableford'])
                if player['gross'] > 0:  # Valid gross score
                    player_stats[name]['best_gross'] = min(player_stats[name]['best_gross'], player['gross'])
    
    # Calculate actual handicap indexes for each player based on their handicap-eligible rounds only
    for name in player_stats:
        # Calculate handicap index from handicap-eligible rounds only
        calculated_index = calculate_player_handicap_index(
            player_stats[name]['rounds'],  # Only handicap-eligible rounds
            config['slope'],  # Keep using existing slope for stable index calculation
            config['rating']  # Keep using existing rating for stable index calculation
        )
        player_stats[name]['calculated_index'] = calculated_index
        
        # Calculate previous week's index (without today's round) for comparison
        if len(player_stats[name]['rounds']) > 1:
            prev_index = calculate_player_handicap_index(
                player_stats[name]['rounds'][:-1],
                config['slope'],  # Keep using existing slope for stable index calculation
                config['rating']  # Keep using existing rating for stable index calculation
            )
            prev_ch = calculate_course_handicap(
                prev_index,
                BACK_9_CONFIG['slope_display'],
                BACK_9_CONFIG['rating_display'],
                BACK_9_CONFIG['par']
            )
            player_stats[name]['prev_index'] = prev_index
            player_stats[name]['prev_ch'] = prev_ch
        else:
            player_stats[name]['prev_index'] = calculated_index
            player_stats[name]['prev_ch'] = 0
        
        # Calculate course handicap for Warringah Back 9 (always show this in leaderboard)
        ch = calculate_course_handicap(
            calculated_index,
            BACK_9_CONFIG['slope_display'],
            BACK_9_CONFIG['rating_display'],
            BACK_9_CONFIG['par']
        )
        player_stats[name]['latest_ch'] = ch
    
    # Calculate averages (from current season only)
    for name in player_stats:
        season_rounds_count = len(player_stats[name]['season_rounds'])
        if season_rounds_count > 0:
            player_stats[name]['avg_stableford'] = player_stats[name]['total_points'] / season_rounds_count
            # Only calculate avg gross if we have gross scores (handicap-eligible rounds)
            if player_stats[name]['total_gross'] > 0:
                # Count only handicap-eligible rounds for avg gross
                handicap_rounds = len([r for r in player_stats[name]['season_rounds'] if r.get('gross', 0) > 0])
                if handicap_rounds > 0:
                    player_stats[name]['avg_gross'] = player_stats[name]['total_gross'] / handicap_rounds
                else:
                    player_stats[name]['avg_gross'] = 0
            else:
                player_stats[name]['avg_gross'] = 0
            player_stats[name]['rounds_count'] = season_rounds_count
        else:
            # Player has no rounds in current year (shouldn't normally happen)
            player_stats[name]['avg_stableford'] = 0
            player_stats[name]['avg_gross'] = 0
            player_stats[name]['rounds_count'] = 0
    
    # Filter to only include players with at least 1 round in current season
    active_players = {name: stats for name, stats in player_stats.items() if stats['rounds_count'] > 0}
    
    # Sort by average
    sorted_players = sorted(active_players.items(), key=lambda x: x[1]['avg_stableford'], reverse=True)
    
    # Build WhatsApp message with bold headers and multi-line formatting
    message = f"*📅 {latest_date_str}*\n\n"
    
    # Add scorecard URL if available
    scorecard_url = latest_round.get('scorecard_url')
    if scorecard_url:
        message += f"🔗 Scorecard:\n{scorecard_url}\n\n"
    
    # Display name mapping
    def get_display_name(name):
        """Convert database names to display names"""
        if name == "Steve":
            return "Steve Lewthwaite"
        return name
    
    # Today's results
    # Check if latest round is from another course
    is_other_course = not latest_round.get('handicap_eligible', True)
    course_display = latest_round.get('course_display_name', 'Warringah')
    
    # Check if we have both front 9 and back 9 from same day
    has_18_holes = len(todays_rounds) == 2
    
    if is_other_course:
        message += f"*🏆 TODAY'S RESULTS:* 🏌️ {course_display}\n\n"
    else:
        message += "*🏆 TODAY'S RESULTS:*\n\n"
    
    # Display each round from today
    for round_idx, round_data in enumerate(todays_rounds):
        # Add course label when playing 9 holes or when 18 holes (label each 9)
        if has_18_holes or (len(todays_rounds) == 1 and not is_other_course):
            # Determine if front or back 9 from course field or date suffix
            is_back9 = round_data['course'] == 'back9' or '-back9' in round_data['date']
            if is_back9:
                message += "⛳ `BACK 9`\n"
            else:
                message += "🚩 `FRONT 9`\n"
        
        # Get config for this specific round
        if round_data['course'] == 'back9':
            round_config = BACK_9_CONFIG
        else:
            round_config = FRONT_9_CONFIG
        
        round_players = sorted(round_data['players'], key=lambda x: x['stableford'], reverse=True)
        
        # Start monospaced block with table format
        message += "```\n"
        message += "Rk Player      Pts Gross\n"
        message += "─────────────────────────\n"
        
        for rank, player in enumerate(round_players, 1):
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            display_name = get_display_name(player['name'])
            first_name = display_name.split()[0]
            
            # Show gross for Warringah rounds, dash for other courses
            if not is_other_course and player['gross'] > 0:
                gross_display = f"{player['gross']:3d}"
            else:
                gross_display = "  -"
            
            message += f"{emoji}{rank:2d} {first_name:10s} {player['stableford']:3d} {gross_display}\n"
        
        # End monospaced block
        message += "```\n"
        
        # Add spacing between front 9 and back 9
        if has_18_holes and round_idx == 0:
            message += "\n"
    
    # Get current year from latest round
    current_year = latest_date_obj.year
    
    # Filter rounds for current year only (needed for monthly tournament)
    current_year_rounds = [r for r in rounds if parse_date_flexible(r['date']).year == current_year]
    
    # ========================================
    # MONTHLY TOURNAMENT (Current month only)
    # ========================================
    current_month = latest_date_obj.month
    current_month_name = latest_date_obj.strftime('%B')
    
    # Calculate monthly stats
    monthly_stats = {}
    for round_data in current_year_rounds:
        round_date = parse_date_flexible(round_data['date'])
        if round_date.month == current_month:
            for player in round_data['players']:
                name = player['name']
                if name not in monthly_stats:
                    monthly_stats[name] = {
                        'total_points': 0,
                        'rounds': 0
                    }
                monthly_stats[name]['total_points'] += player['stableford']
                monthly_stats[name]['rounds'] += 1
    
    # Calculate monthly averages
    monthly_leaderboard = []
    for name, stats in monthly_stats.items():
        if stats['rounds'] > 0:
            avg = stats['total_points'] / stats['rounds']
            monthly_leaderboard.append((name, avg, stats['rounds']))
    
    # Sort by average
    monthly_leaderboard.sort(key=lambda x: x[1], reverse=True)
    
    # Display monthly tournament if we have data
    if monthly_leaderboard:
        message += f"*🏅 {current_month_name.upper()} BOARD:*\n"
        message += "```\n"
        
        # Table header - compact format (removed Rds column)
        message += "Rk Player       Avg\n"
        message += "─────────────────────────\n"
        
        for rank, (name, avg, round_count) in enumerate(monthly_leaderboard, 1):
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            display_name = get_display_name(name)
            
            # Use first name only for compact display
            first_name = display_name.split()[0]
            
            # Calculate trend for this player (last 5 rounds in current month)
            player_monthly_rounds = []
            for round_data in current_year_rounds:
                round_date = parse_date_flexible(round_data['date'])
                if round_date.month == current_month:
                    for player in round_data['players']:
                        if player['name'] == name:
                            player_monthly_rounds.append(player['stableford'])
            
            # Determine trend emoji
            if len(player_monthly_rounds) >= 3:
                trend = "📈" if player_monthly_rounds[-1] > player_monthly_rounds[0] else "📉" if player_monthly_rounds[-1] < player_monthly_rounds[0] else "➡️"
            else:
                trend = "➡️"
            
            # Format table row with compact spacing (removed round_count, added trend)
            message += f"{emoji}{rank:2d} {first_name:11s} {avg:4.1f}{trend}\n"
        
        message += "```\n"
    
    # Calculate form guide BEFORE season leaderboard (need for trend indicators)
    form_guide = {}
    for name, stats in player_stats.items():
        last_5 = stats['season_rounds'][-5:] if len(stats['season_rounds']) >= 5 else stats['season_rounds']
        if last_5:
            scores = [r['stableford'] for r in last_5]
            avg_last_5 = sum(scores) / len(scores)
            trend = "📈" if len(scores) >= 3 and scores[-1] > scores[0] else "📉" if len(scores) >= 3 and scores[-1] < scores[0] else "➡️"
            form_guide[name] = {
                'scores': scores,
                'avg': avg_last_5,
                'trend': trend
            }
    
    # Season leaderboard - Compact table
    message += f"*📊 {current_year} LEADERBOARD:*\n"
    message += "```\n"
    message += "Rk Player       Avg\n"
    message += "─────────────────────────\n"
    
    for rank, (name, stats) in enumerate(sorted_players, 1):
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        display_name = get_display_name(name)
        first_name = display_name.split()[0]
        
        # Get trend indicator
        trend = form_guide.get(name, {}).get('trend', '')
        
        message += f"{emoji}{rank:2d} {first_name:11s} {stats['avg_stableford']:4.1f}{trend}\n"
    
    message += "```\n"
    
    # Player Stats - Detailed section
    message += f"*📋 PLAYER STATS:*\n"
    message += "```\n"
    
    for rank, (name, stats) in enumerate(sorted_players, 1):
        # Calculate changes
        index_change = stats['calculated_index'] - stats['prev_index']
        ch_change = stats['latest_ch'] - stats['prev_ch']
        
        # Format change indicators
        index_arrow = f" ({index_change:+.1f})" if abs(index_change) > 0.05 else ""
        ch_arrow = f" ({ch_change:+d})" if ch_change != 0 else ""
        
        # Check if player qualifies (only show DNQ after June)
        show_dnq = latest_date_obj.month > 6 and stats['rounds_count'] < 10
        dnq_text = " ⚠️ DNQ" if show_dnq else ""
        
        display_name = get_display_name(name)
        
        # Cleaner format with emojis for visual clarity (Option 1)
        message += f"{display_name.upper()}\n"
        message += f"─────────────────────────\n"
        message += f"🎯 {stats['rounds_count']} rounds{dnq_text}\n"
        message += f"📊 WHS {stats['calculated_index']:.1f}{index_arrow} | War HCP {stats['latest_ch']}{ch_arrow}\n"
        message += f"🏆 PBs: {stats['best_stableford']} stab | {stats['best_gross']} gross\n"
        message += f"📈 Avg: {stats['avg_gross']:.1f}\n\n"
    
    message += "```"
    
    # ========================================
    # YEAR-OVER-YEAR COMPARISON (2026+)
    # ========================================
    if current_year >= 2026:
        # Get previous year's data for same date range
        prev_year = current_year - 1
        current_day_of_year = latest_date_obj.timetuple().tm_yday
        
        # Filter previous year rounds up to the same day of year
        prev_year_rounds = []
        for r in rounds:
            round_date = parse_date_flexible(r['date'])
            if round_date.year == prev_year:
                day_of_year = round_date.timetuple().tm_yday
                if day_of_year <= current_day_of_year:
                    prev_year_rounds.append(r)
        
        # Calculate previous year stats
        prev_year_stats = {}
        if prev_year_rounds:
            for round_data in prev_year_rounds:
                for player in round_data['players']:
                    name = player['name']
                    if name not in prev_year_stats:
                        prev_year_stats[name] = {
                            'total_stableford': 0,
                            'rounds_count': 0,
                            'total_gross': 0,
                            'differentials': []
                        }
                    
                    prev_year_stats[name]['total_stableford'] += player['stableford']
                    prev_year_stats[name]['rounds_count'] += 1
                    if player.get('gross', 0) > 0:
                        prev_year_stats[name]['total_gross'] += player['gross']
                    
                    # Calculate differential for handicap
                    course_key = round_data['course']
                    if course_key == 'back9':
                        config = BACK_9_CONFIG
                    else:
                        config = FRONT_9_CONFIG
                    
                    if player.get('gross', 0) > 0:
                        diff = calculate_differential(
                            player['gross'],
                            config['rating'],
                            config['slope'],
                            config['par']
                        )
                        prev_year_stats[name]['differentials'].append({
                            'differential': diff,
                            'date': round_data['date']
                        })
            
            # Calculate previous year averages and handicaps
            for name in prev_year_stats:
                stats = prev_year_stats[name]
                stats['avg_stableford'] = stats['total_stableford'] / stats['rounds_count']
                if stats['total_gross'] > 0:
                    stats['avg_gross'] = stats['total_gross'] / stats['rounds_count']
                else:
                    stats['avg_gross'] = 0
                
                # Calculate handicap index
                if stats['differentials']:
                    sorted_diffs = sorted(stats['differentials'], key=lambda x: x['date'])
                    differentials = [d['differential'] for d in sorted_diffs]
                    hc_calc = HandicapCalculator()
                    stats['handicap_index'] = hc_calc.update_handicap_index(0, differentials)
                else:
                    stats['handicap_index'] = 0
        
        # Build comparison if we have previous year data
        if prev_year_stats:
            message += f"*📊 YEAR-OVER-YEAR COMPARISON:*\n"
            message += f"({current_year} vs {prev_year} - Same Period)\n\n"
            message += "```\n"
            
            # Only compare players who played in both years
            for rank, (name, stats) in enumerate(sorted_players, 1):
                if name in prev_year_stats:
                    prev_stats = prev_year_stats[name]
                    
                    # Calculate changes
                    pts_change = stats['avg_stableford'] - prev_stats['avg_stableford']
                    hcp_change = stats['calculated_index'] - prev_stats['handicap_index']
                    
                    # Determine trend emoji
                    if pts_change > 1.0:
                        trend = "📈"
                    elif pts_change > 0.2:
                        trend = "↗️"
                    elif pts_change < -1.0:
                        trend = "📉"
                    elif pts_change < -0.2:
                        trend = "↘️"
                    else:
                        trend = "➡️"
                    
                    emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
                    display_name = get_display_name(name)
                    
                    message += f"{emoji} {rank}. {display_name}\n"
                    message += f"  {current_year}: {stats['avg_stableford']:.1f} avg • {stats['rounds_count']} rounds • WHS {stats['calculated_index']:.1f}\n"
                    message += f"  {prev_year}: {prev_stats['avg_stableford']:.1f} avg • {prev_stats['rounds_count']} rounds • WHS {prev_stats['handicap_index']:.1f}\n"
                    message += f"  {trend} {pts_change:+.1f} pts • {hcp_change:+.1f} HCP\n\n"
            
            message += "```\n\n"
    
    # Calculate hottest player for AI commentary (best last 5 avg)
    hottest = max(form_guide.items(), key=lambda x: x[1]['avg']) if form_guide else None
    
    # Prepare handicap change information for today's players
    todays_player_names = [p['name'] for round_data in todays_rounds for p in round_data['players']]
    
    handicap_changes_text = ""
    for name, stats in player_stats.items():
        if name in todays_player_names:
            index_change = stats['calculated_index'] - stats['prev_index']
            if abs(index_change) > 0.05:  # Only mention significant changes
                direction = "dropped" if index_change < 0 else "increased"
                handicap_changes_text += f"- {name}: WHS handicap {direction} from {stats['prev_index']:.1f} to {stats['calculated_index']:.1f} ({index_change:+.1f})\n"
    
    if handicap_changes_text:
        handicap_changes_text = f"\n\nHANDICAP CHANGES FROM TODAY'S ROUND (mention these changes in your commentary):\n{handicap_changes_text}"
    
    # Add AI commentary
    print("DEBUG: About to call generate_ai_commentary")
    try:
        # Prepare prediction text for AI
        ai_prediction_text = None
        if hottest:
            hottest_name = hottest[0]
            ai_prediction_text = f"{hottest_name} is the favorite for next round (hottest form: {hottest[1]['avg']:.1f} avg last 5)"
        
        commentary = generate_ai_commentary(
            todays_rounds,  # Pass all rounds from today (could be 1 or 2)
            sorted_players, 
            sorted_players, 
            form_data=form_guide,
            prediction_text=ai_prediction_text,
            handicap_changes=handicap_changes_text
        )
        print(f"DEBUG: generate_ai_commentary returned: {commentary is not None}")
        if commentary:
            print(f"DEBUG: Adding commentary to message")
            message += f"\n*🎭 AI COMMENTARY:*\n```\n{commentary}\n```\n"
        else:
            print(f"DEBUG: No commentary generated (returned None)")
    except Exception as e:
        print(f"ERROR: AI commentary generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    return message

def lambda_handler(event, context):
    """
    Lambda handler with authentication
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
    print(f"=== Lambda Invoked ===")
    
    # Authentication check
    SECRET_TOKEN = os.environ.get('AUTH_TOKEN', 'golf-handicap-secret-2025')
    
    # Extract token from headers (Function URL format)
    provided_token = None
    if isinstance(event, dict):
        headers = event.get('headers', {})
        if headers:
            # Check various header formats
            provided_token = (
                headers.get('x-auth-token') or 
                headers.get('X-Auth-Token') or
                headers.get('authorization') or
                headers.get('Authorization')
            )
            
            # Strip "Bearer " prefix if present
            if provided_token and provided_token.startswith('Bearer '):
                provided_token = provided_token[7:]  # Remove "Bearer " (7 characters)
    
    # Verify token
    if provided_token != SECRET_TOKEN:
        print(f"❌ Authentication failed - Invalid or missing token")
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Unauthorized - Invalid or missing authentication token'})
        }
    
    print(f"✓ Authentication successful")
    print(f"Event type: {type(event)}")
    print(f"Event keys: {list(event.keys()) if isinstance(event, dict) else 'Not a dict'}")
    
    # Log the raw event for debugging
    try:
        print(f"Full event: {json.dumps(event)}")
    except:
        print(f"Event (non-JSON): {str(event)[:500]}")
    
    # Debug mode - return event details if debug parameter is present
    if isinstance(event, dict) and event.get('debug') == 'true':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'debug': True,
                'event_type': str(type(event)),
                'event_keys': list(event.keys()) if isinstance(event, dict) else [],
                'body_type': str(type(event.get('body', None))),
                'body_preview': str(event.get('body', ''))[:200],
                'http_method': event.get('requestContext', {}).get('http', {}).get('method', 'UNKNOWN')
            }, indent=2)
        }
    
    try:
        # Parse request body - handle different event formats
        body = {}
        
        # Check HTTP method
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'UNKNOWN')
        print(f"HTTP Method: {http_method}")
        
        # Function URL sends body as string
        if 'body' in event and isinstance(event['body'], str):
            print(f"Body is string, length: {len(event['body'])}")
            
            # Check if it's a Tag Heuer URL directly (not JSON)
            if event['body'].strip().startswith('https://www.tagheuergolf.com/'):
                print(f"Direct Tag Heuer URL detected")
                body = {
                    'action': 'add_round',
                    'url': event['body'].strip()
                }
            else:
                # Try to parse as JSON
                try:
                    body = json.loads(event['body'])
                    print(f"Successfully parsed JSON body")
                    
                    # Handle iOS Shortcut format: {"JSON": "{\"action\": ...}"}
                    if 'JSON' in body and isinstance(body['JSON'], str):
                        print(f"Detected nested JSON string from iOS Shortcut")
                        try:
                            body = json.loads(body['JSON'])
                            print(f"Successfully parsed nested JSON")
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse nested JSON: {e}")
                    
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    body = event
        # API Gateway or direct invoke
        elif 'body' in event and isinstance(event['body'], dict):
            print(f"Body is dict")
            body = event['body']
        # Direct event (no wrapper)
        else:
            print(f"No body wrapper, using event directly")
            body = event
        
        print(f"Parsed body: {json.dumps(body)}")
        
        # Auto-detect action if URL is provided without explicit action
        action = body.get('action')
        if not action and body.get('url'):
            action = 'add_round'
            print(f"Auto-detected action=add_round from URL")
        elif not action:
            action = 'get_summary'
        
        # Check for specific date parameter (for historical summaries)
        query_params = event.get('queryStringParameters', {}) or {}
        specific_date = query_params.get('date') or body.get('specific_date')
        
        print(f"Action: {action}")
        if specific_date:
            print(f"Specific date requested: {specific_date}")
        
        if action == 'add_round':
            url = body.get('url')
            if not url:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'URL is required'})
                }
            
            # Handle URL extraction from text (iOS Share Sheet may include description)
            # Example: "I played 26 at Warringah...\nhttps://www.tagheuergolf.com/rounds/..."
            if isinstance(url, str) and 'tagheuergolf.com' in url:
                # Extract URL using regex
                import re
                url_match = re.search(r'https://www\.tagheuergolf\.com/rounds/[A-Za-z0-9-]+', url)
                if url_match:
                    url = url_match.group(0)
                    print(f"Extracted URL from text: {url}")
            
            # Parse Tag Heuer URL (may return single round or list of rounds for 18 holes)
            round_data = parse_tag_heuer_url(url)
            
            # Handle parsing error (but not duplicate detection)
            if isinstance(round_data, dict) and 'error' in round_data:
                error_msg = round_data.get('error', 'Unknown error')
                print(f"❌ PARSING FAILED: {error_msg}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(round_data)
                }
            
            # Convert single round to list for uniform processing
            rounds_to_process = round_data if isinstance(round_data, list) else [round_data]
            
            # Process each round
            saved_count = 0
            duplicate_count = 0
            for rd in rounds_to_process:
                # Check if round is too old
                if not is_recent_round(rd['date']):
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': '⏰ Round is more than 7 days old. Only recent rounds can be submitted.',
                            'error_type': 'OLD_ROUND'
                        })
                    }
                
                # For 18-hole rounds, need unique storage keys
                # Store front9 and back9 with date suffixes to avoid overwrite
                if len(rounds_to_process) == 2:
                    # 18-hole round - modify dates for storage
                    if rd['course'] == 'back9':
                        storage_date = f"{rd['date']}-back9"
                    else:
                        storage_date = rd['date']  # front9 uses standard date
                    display_date = rd['date']  # Keep original for display
                    
                    if not check_duplicate_round(storage_date):
                        rd_copy = rd.copy()
                        rd_copy['date'] = storage_date
                        save_round(rd_copy)
                        saved_count += 1
                        print(f"✅ New round saved for {display_date} ({rd['course']})")
                    else:
                        duplicate_count += 1
                        print(f"ℹ️ Duplicate round detected for {display_date} ({rd['course']}), skipping save")
                else:
                    # Single 9-hole round - use original logic
                    if not check_duplicate_round(rd['date']):
                        save_round(rd)
                        saved_count += 1
                        print(f"✅ New round saved for {rd['date']}")
                    else:
                        duplicate_count += 1
                        print(f"ℹ️ Duplicate round detected for {rd['date']}, skipping save")
            
            print(f"Total rounds saved: {saved_count}, duplicates skipped: {duplicate_count}")
        
        # Get all rounds and generate summary
        rounds = get_all_rounds()
        summary = generate_whatsapp_summary(rounds, specific_date=specific_date)
        
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
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'error_type': type(e).__name__
            })
        }
