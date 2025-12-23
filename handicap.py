"""
Australian World Handicapping System (WHS) Calculator
Implements 9-hole handicap calculation with weather adjustments
"""

from datetime import datetime


class HandicapCalculator:
    def __init__(self):
        pass
    
    def calculate_adjusted_gross_score(self, holes, pars, course_handicap, hole_handicaps):
        """
        Calculate adjusted gross score with net double bogey (ESC) applied per hole.
        
        Args:
            holes: List of scores for each hole (None = X mark/blob)
            pars: List of par values for each hole
            course_handicap: Player's course handicap for the round
            hole_handicaps: List of hole handicap indexes (1-18, where 1 is hardest)
        
        Returns:
            Adjusted gross score with net double bogey applied
        """
        # Determine which holes get strokes
        # Holes are allocated strokes in order of their handicap index
        strokes_per_hole = [0] * len(holes)
        
        # Sort holes by handicap index to allocate strokes
        sorted_holes = sorted(enumerate(hole_handicaps), key=lambda x: x[1])
        
        strokes_remaining = course_handicap
        while strokes_remaining > 0:
            for hole_idx, _ in sorted_holes:
                if strokes_remaining > 0:
                    strokes_per_hole[hole_idx] += 1
                    strokes_remaining -= 1
                else:
                    break
        
        adjusted_total = 0
        for i, (score, par) in enumerate(zip(holes, pars)):
            # Calculate max allowable (net double bogey)
            max_score = par + 2 + strokes_per_hole[i]
            
            # If score is None (X mark/blob), use max allowable
            if score is None:
                actual_score = max_score
            else:
                actual_score = score
            
            # Apply net double bogey cap
            adjusted_score = min(actual_score, max_score)
            adjusted_total += adjusted_score
        
        return adjusted_total
    
    def calculate_9_hole_differential_from_holes(self, holes, pars, course_rating_9, slope_rating, 
                                                  course_handicap, hole_handicaps, weather_factor=1.0):
        """
        Calculate 9-hole score differential using hole-by-hole data with net double bogey.
        
        Args:
            holes: List of scores for each hole (None = X mark/blob)
            pars: List of par values for each hole
            course_rating_9: 9-hole course rating
            slope_rating: Slope rating
            course_handicap: Player's course handicap for the round
            hole_handicaps: List of hole handicap indexes
            weather_factor: Weather adjustment (default 1.0)
        
        Returns:
            Score differential rounded to 1 decimal
        """
        # Calculate adjusted gross score with net double bogey
        adjusted_score = self.calculate_adjusted_gross_score(holes, pars, course_handicap, hole_handicaps)
        
        # Calculate differential
        raw_differential = (adjusted_score - course_rating_9) * (113 / slope_rating)
        
        # Apply weather factor
        weather_adjusted_differential = raw_differential * weather_factor
        
        return round(weather_adjusted_differential, 1)
    
    def calculate_9_hole_differential(self, score, course_rating_9, slope_rating, pars, weather_factor=1.0):
        """
        Calculate 9-hole score differential (legacy method using total score)
        
        Formula: (Adjusted Gross Score - Course Rating) × (113 / Slope Rating)
        For 9 holes, we use half the 18-hole course rating
        """
        # Adjusted gross score (for now, just use raw score - can add ESC later)
        adjusted_score = score
        
        # Apply weather adjustment to the differential
        raw_differential = (adjusted_score - course_rating_9) * (113 / slope_rating)
        
        # Apply weather difficulty factor
        weather_adjusted_differential = raw_differential * weather_factor
        
        return round(weather_adjusted_differential, 1)
    
    def calculate_playing_handicap(self, handicap_index, course_rating, slope_rating, holes=9):
        """
        Calculate playing handicap for the round
        
        Formula: Handicap Index × (Slope Rating / 113) × (holes / 18)
        """
        playing_handicap = handicap_index * (slope_rating / 113) * (holes / 18)
        return round(playing_handicap)
    
    def update_handicap_index(self, current_index, score_differentials, weather_factors=None):
        """
        Update handicap index based on recent score differentials
        Uses best 8 of last 20 scores (simplified WHS)
        
        For 9-hole rounds, two 9-hole differentials combine to one 18-hole differential
        """
        if not score_differentials:
            return current_index
        
        # Apply weather factors if provided
        if weather_factors:
            adjusted_differentials = [
                diff * factor for diff, factor in zip(score_differentials, weather_factors)
            ]
        else:
            adjusted_differentials = score_differentials
        
        # Take the best 8 of last 20 (or fewer if not enough scores)
        num_scores = len(adjusted_differentials)
        
        if num_scores < 3:
            # Not enough scores, return current index
            return current_index
        
        # Determine how many scores to use
        if num_scores >= 20:
            num_to_use = 8
        elif num_scores >= 10:
            num_to_use = 5
        elif num_scores >= 6:
            num_to_use = 3
        else:
            num_to_use = min(2, num_scores)
        
        # Sort and take best scores
        sorted_diffs = sorted(adjusted_differentials)
        best_diffs = sorted_diffs[:num_to_use]
        
        # Calculate average
        new_index = sum(best_diffs) / len(best_diffs)
        
        # Apply adjustment (96% of average per WHS)
        new_index = new_index * 0.96
        
        return round(new_index, 1)
    
    def calculate_stableford_points(self, score, par, playing_handicap_for_hole):
        """
        Calculate Stableford points for a hole
        """
        net_score = score - playing_handicap_for_hole
        
        if net_score <= par - 2:  # Eagle or better
            return 4
        elif net_score == par - 1:  # Birdie
            return 3
        elif net_score == par:  # Par
            return 2
        elif net_score == par + 1:  # Bogey
            return 1
        else:  # Double bogey or worse
            return 0


class RoundAnalyzer:
    def __init__(self, handicap_calculator):
        self.calc = handicap_calculator
    
    def analyze_round(self, player_data, course_rating, slope_rating, pars, weather_factor=1.0):
        """
        Analyze a player's 9-hole round
        Returns detailed stats and updated handicap
        """
        name = player_data['name']
        current_index = player_data['handicap_index']
        scores = player_data['scores']
        
        # Calculate totals
        total_score = sum(scores)
        total_par = sum(pars)
        score_to_par = total_score - total_par
        
        # Calculate 9-hole course rating (half of 18-hole rating)
        course_rating_9 = course_rating / 2
        
        # Calculate playing handicap for this round
        playing_handicap = self.calc.calculate_playing_handicap(
            current_index, course_rating, slope_rating, holes=9
        )
        
        # Calculate differential for this round
        differential = self.calc.calculate_9_hole_differential(
            total_score, course_rating_9, slope_rating, pars, weather_factor
        )
        
        # Net score
        net_score = total_score - playing_handicap
        net_to_par = net_score - total_par
        
        # Calculate Stableford points for each hole
        stableford_points = self._calculate_stableford_for_round(
            scores, pars, playing_handicap, len(scores)
        )
        total_stableford = sum(stableford_points)
        
        return {
            'name': name,
            'gross_score': total_score,
            'par': total_par,
            'score_to_par': score_to_par,
            'playing_handicap': playing_handicap,
            'net_score': net_score,
            'net_to_par': net_to_par,
            'score_differential': differential,
            'current_handicap_index': current_index,
            'weather_factor': weather_factor,
            'stableford_points': total_stableford,
            'stableford_by_hole': stableford_points
        }
    
    def _calculate_stableford_for_round(self, scores, pars, playing_handicap, num_holes):
        """
        Calculate Stableford points for each hole
        Distributes playing handicap across holes based on difficulty
        """
        stableford_points = []
        
        # Simple distribution: give strokes to hardest holes first
        # For 9 holes, distribute playing handicap across holes
        strokes_per_hole = [0] * num_holes
        remaining_strokes = playing_handicap
        
        # Distribute strokes (1 per hole, then 2, etc.)
        stroke_round = 1
        while remaining_strokes > 0:
            for i in range(num_holes):
                if remaining_strokes > 0:
                    strokes_per_hole[i] = stroke_round
                    remaining_strokes -= 1
                else:
                    break
            stroke_round += 1
        
        # Calculate Stableford for each hole
        for i in range(num_holes):
            score = scores[i]
            par = pars[i]
            strokes = strokes_per_hole[i]
            
            points = self.calc.calculate_stableford_points(score, par, strokes)
            stableford_points.append(points)
        
        return stableford_points


if __name__ == "__main__":
    # Test with example data
    calc = HandicapCalculator()
    analyzer = RoundAnalyzer(calc)
    
    # Example player
    player = {
        'name': 'Bruce Kennaway',
        'handicap_index': 19.0,
        'scores': [6, 4, 4, 5, 5, 5, 5, 0, 0]  # Only first 7 holes
    }
    
    # Remove zeros
    player['scores'] = [s for s in player['scores'] if s > 0]
    
    pars = [4, 4, 5, 4, 3, 5, 4]
    course_rating = 68.0
    slope_rating = 118
    weather_factor = 1.08  # Moderate wind
    
    result = analyzer.analyze_round(player, course_rating, slope_rating, pars, weather_factor)
    
    print(f"\n{result['name']}")
    print(f"Gross Score: {result['gross_score']} ({result['score_to_par']:+d})")
    print(f"Playing Handicap: {result['playing_handicap']}")
    print(f"Net Score: {result['net_score']} ({result['net_to_par']:+d})")
    print(f"Score Differential: {result['score_differential']}")
    print(f"Weather Factor: {result['weather_factor']}x")
