"""
Golf Handicap and Stableford Scoring System
Processes golf rounds and generates statistics, Excel export, and WhatsApp summary
"""
import pandas as pd
from datetime import datetime, timedelta
import boto3
import urllib3
from decimal import Decimal
import json
from handicap import HandicapCalculator

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# AWS setup
import os
os.environ['AWS_ACCESS_KEY_ID'] = 'REMOVED_AWS_KEY'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'REMOVED_AWS_SECRET'

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', verify=False)
table = dynamodb.Table('golf-rounds')

# Course configurations
# NOTE: Labels in database are BACKWARDS - "front9" in DB = Back 9 in reality
BACK_9_CONFIG = {
    'name': 'Back 9 (Holes 10-18)',
    'par': 70,
    'slope': 101,
    'rating': 33.5,  # This is what's stored as "front9" in DB
    'hcp_allocations': [8, 9, 18, 6, 17, 3, 14, 12, 2],
}

FRONT_9_CONFIG = {
    'name': 'Front 9 (Holes 1-9)',
    'par': 69,
    'slope': 101,
    'rating': 17.5,  # 35.0 / 2 (18-hole rating / 2)
    'hcp_allocations': [15, 3, 7, 10, 16, 1, 13, 5, 11],
}

COURSE_CONFIGS = {
    'back9': FRONT_9_CONFIG,  # Swapped! DB says "front9" but it's really back 9
    'front9': BACK_9_CONFIG,  # Swapped! DB says "back9" but it's really front 9
}

# Players to track (exclude Eddie, Jo W., Mark, Julian)
PLAYERS_TO_TRACK = {
    'Bruce Kennaway',
    'Andy Jakes',
    'Andy J.',
    'Hamish McNee',
    'Hamish M.',
    'Fletcher Jakes',
    'Fletcher J.',
    'Steve',
}

def normalize_player_name(name):
    """Normalize player names"""
    name_map = {
        'Andy J.': 'Andy Jakes',
        'Andy Jake': 'Andy Jakes',
        'Fletcher J.': 'Fletcher Jakes',
        'Hamish M.': 'Hamish McNee',
        'Hamish McNee': 'Hamish McNee',
        'Bruce Kennaway': 'Bruce Kennaway',
        'Steve': 'Steve',
    }
    return name_map.get(name, name)

def calculate_course_handicap(index, slope, rating, par):
    """Golf Australia formula: CH = round(Index × Slope/113)"""
    ch = round(float(index) * slope / 113)
    return max(0, ch)

def calculate_handicap_indices(df):
    """
    Calculate handicap indices for all players using WHS method
    Treats 9-hole rounds as 18-hole equivalents (doubles gross and rating)
    Returns a dict with player names as keys and their calculated index as values
    """
    hc_calc = HandicapCalculator()
    player_indices = {}
    
    for player_name in df['Player'].unique():
        player_df = df[df['Player'] == player_name].sort_values('Date')
        
        # Calculate differentials treating 9-hole as 18-hole equivalent
        differentials = []
        for _, row in player_df.iterrows():
            # Double the 9-hole values to get 18-hole equivalents
            gross_18 = row['Gross'] * 2
            rating_18 = row['Rating'] * 2
            
            # Differential = (Adjusted Gross Score - Course Rating) × (113 / Slope)
            differential = (gross_18 - rating_18) * (113 / row['Slope'])
            differentials.append(round(differential, 1))
        
        # Calculate index using best differentials (WHS method)
        calculated_index = hc_calc.update_handicap_index(0, differentials)
        player_indices[player_name] = calculated_index
    
    return player_indices

def fetch_rounds_from_db():
    """Fetch all rounds from DynamoDB"""
    try:
        response = table.scan()
        items = response.get('Items', [])
        return items
    except Exception as e:
        print(f"Error fetching from DB: {e}")
        return []

def process_rounds(rounds_data):
    """Process rounds into a format for analysis"""
    all_records = []
    
    for round_data in rounds_data:
        date = round_data['date']
        course = round_data['course']
        config = COURSE_CONFIGS[course]
        
        for player_data in round_data.get('players', []):
            name = normalize_player_name(player_data['name'])
            
            # Skip excluded players
            if name not in PLAYERS_TO_TRACK:
                continue
            
            index = float(player_data['index'])
            gross = int(player_data['gross'])
            stableford = int(player_data['stableford'])
            
            ch = calculate_course_handicap(index, config['slope'], config['rating'], config['par'])
            
            all_records.append({
                'Date': date,
                'Player': name,
                'Index': index,
                'CH': ch,
                'Gross': gross,
                'Stableford': stableford,
                'Par': config['par'],
                'Slope': config['slope'],
                'Rating': config['rating'],
                'Course': course,
            })
    
    return all_records

def generate_console_stats(df):
    """Generate console statistics"""
    print("\n" + "="*70)
    print("GOLF HANDICAP TRACKER - 2025 SEASON STATISTICS")
    print("="*70)
    
    total_rounds = len(df['Date'].unique())
    print(f"\nTotal Rounds Processed: {total_rounds}")
    
    # Leaderboard
    print("\n" + "-"*70)
    print("2025 SEASON LEADERBOARD (Ranked by Average Stableford)")
    print("-"*70)
    
    leaderboard = df.groupby('Player').agg({
        'Stableford': ['count', 'sum', 'mean'],
        'Gross': 'mean'
    }).round(2)
    leaderboard.columns = ['Rounds', 'Total Points', 'Avg Stableford', 'Avg Gross']
    leaderboard = leaderboard.sort_values('Avg Stableford', ascending=False)
    leaderboard = leaderboard.reset_index()
    leaderboard['Rank'] = range(1, len(leaderboard) + 1)
    
    print(f"\n{'Rank':<5} {'Player':<20} {'Rounds':<8} {'Total Pts':<12} {'Avg Stab':<12} {'Avg Gross':<12}")
    print("-"*70)
    
    for _, row in leaderboard.iterrows():
        print(f"{int(row['Rank']):<5} {row['Player']:<20} {int(row['Rounds']):<8} {int(row['Total Points']):<12} {row['Avg Stableford']:<12.2f} {row['Avg Gross']:<12.2f}")
    
    print("="*70 + "\n")
    
    return leaderboard

def generate_excel_export(df):
    """Generate Excel file"""
    df_export = df[['Date', 'Player', 'Index', 'CH', 'Gross', 'Stableford', 'Par', 'Slope', 'Rating']].copy()
    df_export = df_export.sort_values('Date')
    
    filename = 'golf_2025_season_47_rounds_fresh.xlsx'
    
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, sheet_name='Rounds', index=False)
        
        # Format Excel
        workbook = writer.book
        worksheet = writer.sheets['Rounds']
        
        # Column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 20)  # Player
        worksheet.set_column('C:C', 10)  # Index
        worksheet.set_column('D:D', 8)   # CH
        worksheet.set_column('E:E', 8)   # Gross
        worksheet.set_column('F:F', 10)  # Stableford
        worksheet.set_column('G:G', 6)   # Par
        worksheet.set_column('H:H', 8)   # Slope
        worksheet.set_column('I:I', 8)   # Rating
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        for col_num, value in enumerate(df_export.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    print(f"[+] Excel file generated: {filename}")
    return filename

def generate_whatsapp_summary(df, calculated_indices):
    """Generate WhatsApp formatted summary"""
    # Get latest round
    latest_date = df['Date'].max()
    latest_round = df[df['Date'] == latest_date].copy()
    
    # Add 1 day for US timezone compensation
    display_date = datetime.strptime(latest_date, '%Y-%m-%d') + timedelta(days=1)
    display_date_str = display_date.strftime('%A, %B %d, %Y').upper()
    
    summary = f"WARRINGAH SATURDAY GOLF\n"
    summary += f"{display_date_str}\n\n"
    
    # Today's results
    summary += "TODAY'S RESULTS:\n"
    latest_sorted = latest_round.sort_values('Stableford', ascending=False).reset_index(drop=True)
    
    for idx, (_, row) in enumerate(latest_sorted.iterrows()):
        ch = int(row['CH'])
        summary += f"{idx + 1}. {row['Player']} - {int(row['Stableford'])} points, {int(row['Gross'])} gross (Index: {row['Index']}, Warringah: {ch})\n"
    
    # Season leaderboard with CALCULATED stats
    summary += "\n2025 SEASON LEADERBOARD:\n\n"
    
    # Group by player and calculate stats properly
    player_stats = []
    for player_name in df['Player'].unique():
        player_df = df[df['Player'] == player_name].sort_values('Date')
        
        # Use CALCULATED index from WHS algorithm
        index = calculated_indices.get(player_name, player_df['Index'].iloc[-1])
        
        # Recalculate CH with calculated index
        latest_course = player_df['Course'].iloc[-1]
        config = COURSE_CONFIGS[latest_course]
        ch = calculate_course_handicap(index, config['slope'], config['rating'], config['par'])
        
        rounds = len(player_df)
        total_points = int(player_df['Stableford'].sum())
        avg_stab = player_df['Stableford'].mean()
        
        # Best stableford and associated gross
        best_idx = player_df['Stableford'].idxmax()
        best_stab = int(player_df.loc[best_idx, 'Stableford'])
        best_gross = int(player_df.loc[best_idx, 'Gross'])
        
        # If best gross is 0 (data issue), find the best actual gross score
        if best_gross == 0:
            valid_gross = player_df[player_df['Gross'] > 0]['Gross']
            if len(valid_gross) > 0:
                best_gross = int(valid_gross.min())
        
        player_stats.append({
            'name': player_name,
            'index': index,
            'ch': ch,
            'rounds': rounds,
            'total_points': total_points,
            'avg_stab': avg_stab,
            'best_stab': best_stab,
            'best_gross': best_gross
        })
    
    # Sort by average stableford
    player_stats.sort(key=lambda x: x['avg_stab'], reverse=True)
    
    for rank, stat in enumerate(player_stats, 1):
        summary += f"{rank}. {stat['name']} (Index: {stat['index']}, Warringah: {stat['ch']}) - {stat['avg_stab']:.2f} avg ({stat['rounds']} rounds, {stat['total_points']} points)\n"
        summary += f"   Personal Best: {stat['best_stab']} pts, {stat['best_gross']} gross\n"
    
    return summary

# Main execution
if __name__ == '__main__':
    print("[*] Fetching golf rounds from DynamoDB...")
    rounds_data = fetch_rounds_from_db()
    print(f"[+] Fetched {len(rounds_data)} rounds")
    
    if not rounds_data:
        print("[-] No rounds found in database")
        exit(1)
    
    print("[*] Processing rounds...")
    records = process_rounds(rounds_data)
    df = pd.DataFrame(records)
    print(f"[+] Processed {len(df)} player records")
    
    print("[*] Calculating handicap indices...")
    calculated_indices = calculate_handicap_indices(df)
    for player, index in calculated_indices.items():
        print(f"  {player}: {index}")
    
    print("[*] Generating console statistics...")
    leaderboard = generate_console_stats(df)
    
    print("[*] Generating Excel export...")
    generate_excel_export(df)
    
    print("[*] Generating WhatsApp summary...")
    summary = generate_whatsapp_summary(df, calculated_indices)
    
    # Save and display summary
    with open('whatsapp_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("\n" + "="*70)
    print("WHATSAPP SUMMARY")
    print("="*70)
    print(summary)
    print("="*70)
    
    print("\n[+] All outputs generated successfully!")
