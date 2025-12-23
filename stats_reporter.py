"""
Statistics Report Generator
Generate detailed statistics reports for players
"""

from excel_handler import ExcelHandler
from datetime import datetime


class StatsReporter:
    def __init__(self, excel_handler):
        self.excel = excel_handler
    
    def generate_leaderboard(self, year=None):
        """
        Generate a leaderboard for the season
        """
        if year is None:
            year = datetime.now().year
        
        stats = self.excel.get_year_stats(year)
        
        if not stats:
            return "No data available for this year."
        
        # Sort by wins, then win %, then avg stableford
        sorted_players = sorted(
            stats.items(),
            key=lambda x: (
                x[1]['games_won'],
                x[1]['win_percentage'],
                x[1]['avg_stableford']
            ),
            reverse=True
        )
        
        report = f"🏆 {year} Season Leaderboard 🏆\n"
        report += "=" * 50 + "\n\n"
        
        for i, (player_name, player_stats) in enumerate(sorted_players, start=1):
            trophy = "👑" if i == 1 else "🥇" if i == 2 else "🥈" if i == 3 else f"{i}."
            report += f"{trophy} {player_name}\n"
            report += f"   Wins: {player_stats['games_won']}/{player_stats['games_played']}"
            report += f" ({player_stats['win_percentage']:.1f}%)\n"
            report += f"   Avg Gross: {player_stats['avg_gross']:.1f}"
            report += f" | Avg Stableford: {player_stats['avg_stableford']:.1f}\n"
            report += f"   Best Gross: {player_stats['best_gross']}"
            if player_stats['best_stableford'] > 0:
                report += f" | Best Stableford: {player_stats['best_stableford']}"
            report += "\n\n"
        
        return report
    
    def generate_player_report(self, player_name, year=None):
        """
        Generate detailed report for a specific player
        """
        if year is None:
            year = datetime.now().year
        
        stats = self.excel.get_year_stats(year)
        
        if player_name not in stats:
            return f"No data found for {player_name} in {year}."
        
        player_stats = stats[player_name]
        
        report = f"📊 {player_name} - {year} Season Report\n"
        report += "=" * 50 + "\n\n"
        
        report += f"🎮 Games Played: {player_stats['games_played']}\n"
        report += f"🏆 Games Won: {player_stats['games_won']}\n"
        report += f"📈 Win Percentage: {player_stats['win_percentage']:.1f}%\n\n"
        
        report += f"⛳ Scoring Averages:\n"
        report += f"   Gross Score: {player_stats['avg_gross']:.1f}\n"
        report += f"   Stableford: {player_stats['avg_stableford']:.1f}\n\n"
        
        report += f"🌟 Personal Bests:\n"
        report += f"   Best Gross: {player_stats['best_gross']}\n"
        if player_stats['best_stableford'] > 0:
            report += f"   Best Stableford: {player_stats['best_stableford']}\n"
        
        # Recent form (last 5 rounds)
        recent_gross = player_stats['gross_scores'][-5:]
        recent_stableford = player_stats['stableford_scores'][-5:]
        
        if recent_gross:
            report += f"\n📉 Recent Form (Last {len(recent_gross)} rounds):\n"
            report += f"   Gross Scores: {', '.join(map(str, recent_gross))}\n"
            if recent_stableford:
                report += f"   Stableford: {', '.join(map(str, recent_stableford))}\n"
            
            avg_recent_gross = sum(recent_gross) / len(recent_gross)
            report += f"   Recent Avg: {avg_recent_gross:.1f}\n"
        
        return report
    
    def generate_head_to_head(self, player1, player2, year=None):
        """
        Generate head-to-head comparison between two players
        """
        if year is None:
            year = datetime.now().year
        
        stats = self.excel.get_year_stats(year)
        
        if player1 not in stats or player2 not in stats:
            return "One or both players not found in the data."
        
        p1_stats = stats[player1]
        p2_stats = stats[player2]
        
        report = f"⚔️ Head to Head: {player1} vs {player2}\n"
        report += "=" * 50 + "\n\n"
        
        report += f"{'Metric':<25} {player1:<15} {player2:<15}\n"
        report += "-" * 50 + "\n"
        
        report += f"{'Games Played':<25} {p1_stats['games_played']:<15} {p2_stats['games_played']:<15}\n"
        report += f"{'Wins':<25} {p1_stats['games_won']:<15} {p2_stats['games_won']:<15}\n"
        report += f"{'Win %':<25} {p1_stats['win_percentage']:<15.1f} {p2_stats['win_percentage']:<15.1f}\n"
        report += f"{'Avg Gross':<25} {p1_stats['avg_gross']:<15.1f} {p2_stats['avg_gross']:<15.1f}\n"
        report += f"{'Avg Stableford':<25} {p1_stats['avg_stableford']:<15.1f} {p2_stats['avg_stableford']:<15.1f}\n"
        report += f"{'Best Gross':<25} {p1_stats['best_gross']:<15} {p2_stats['best_gross']:<15}\n"
        
        return report
    
    def generate_whatsapp_leaderboard(self, year=None):
        """
        Generate a compact leaderboard suitable for WhatsApp
        """
        if year is None:
            year = datetime.now().year
        
        stats = self.excel.get_year_stats(year)
        
        if not stats:
            return "No data available."
        
        sorted_players = sorted(
            stats.items(),
            key=lambda x: (x[1]['games_won'], x[1]['win_percentage']),
            reverse=True
        )
        
        message = f"🏆 {year} Leaderboard 🏆\n\n"
        
        for i, (player, s) in enumerate(sorted_players, start=1):
            emoji = "👑" if i == 1 else "🥇" if i == 2 else "🥈" if i == 3 else "  "
            message += f"{emoji} {player}\n"
            message += f"   {s['games_won']}W-{s['games_played']-s['games_won']}L"
            message += f" ({s['win_percentage']:.0f}%) | Avg: {s['avg_stableford']:.1f}\n"
        
        return message


if __name__ == "__main__":
    # Test the stats reporter
    excel = ExcelHandler('test_handicaps.xlsx')
    excel.load_or_create_workbook()
    
    reporter = StatsReporter(excel)
    
    print(reporter.generate_leaderboard(2025))
    print("\n" + "="*50 + "\n")
    print(reporter.generate_whatsapp_leaderboard(2025))
