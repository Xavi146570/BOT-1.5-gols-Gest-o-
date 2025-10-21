"""
Probability Calculator - Sistema Over 1.5
"""

import logging
import math
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProbabilityCalculator:
    """Calcula probabilidades Over 1.5"""
    
    WEIGHTS = {
        'poisson': 0.50,
        'historical_rate': 0.30,
        'h2h': 0.20
    }
    
    def __init__(self):
        self.baseline_over_rate = 0.72
    
    def calculate_probability(
        self,
        home_stats: Dict,
        away_stats: Dict,
        h2h_data: Optional[Dict] = None,
        match_context: Optional[Dict] = None
    ) -> Dict:
        """Calcula probabilidade Over 1.5"""
        try:
            poisson_prob = self._calculate_poisson_over_probability(home_stats, away_stats)
            historical_prob = self._calculate_historical_rate(home_stats, away_stats)
            h2h_prob = self._calculate_h2h_probability(h2h_data)
            
            final_probability = (
                poisson_prob * self.WEIGHTS['poisson'] +
                historical_prob * self.WEIGHTS['historical_rate'] +
                h2h_prob * self.WEIGHTS['h2h']
            )
            
            final_probability = max(0.0, min(1.0, final_probability))
            confidence = self._calculate_confidence(home_stats, away_stats)
            
            return {
                'probability': round(final_probability, 4),
                'confidence': round(confidence, 2),
                'breakdown': {
                    'poisson': round(poisson_prob, 4),
                    'historical_rate': round(historical_prob, 4),
                    'h2h': round(h2h_prob, 4)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular probabilidade: {e}")
            return {
                'probability': self.baseline_over_rate,
                'confidence': 50.0,
                'breakdown': {}
            }
    
    def _calculate_poisson_over_probability(self, home_stats: Dict, away_stats: Dict) -> float:
        """Calcula P(Over 1.5) usando Poisson"""
        try:
            home_attack = home_stats.get('goals_for_avg', 1.5)
            away_attack = away_stats.get('goals_for_avg', 1.2)
            
            lambda_total = (home_attack + away_attack) / 1.5
            prob_under = math.exp(-lambda_total) * (1 + lambda_total)
            prob_over = 1 - prob_under
            
            return prob_over
            
        except Exception as e:
            logger.error(f"Erro Poisson: {e}")
            return self.baseline_over_rate
    
    def _calculate_historical_rate(self, home_stats: Dict, away_stats: Dict) -> float:
        """Calcula taxa histórica"""
        try:
            home_rate = home_stats.get('over_1_5_rate', 0.72)
            away_rate = away_stats.get('over_1_5_rate', 0.72)
            return (home_rate * 0.55) + (away_rate * 0.45)
        except Exception:
            return self.baseline_over_rate
    
    def _calculate_h2h_probability(self, h2h_data: Optional[Dict]) -> float:
        """Calcula probabilidade H2H"""
        try:
            if not h2h_data or not h2h_data.get('matches'):
                return self.baseline_over_rate
            
            matches = h2h_data['matches']
            over_count = sum(1 for m in matches if m.get('total_goals', 0) >= 2)
            return over_count / len(matches) if matches else self.baseline_over_rate
        except Exception:
            return self.baseline_over_rate
    
    def _calculate_confidence(self, home_stats: Dict, away_stats: Dict) -> float:
        """Calcula confiança"""
        confidence = 50.0
        
        home_games = home_stats.get('games_played', 0)
        away_games = away_stats.get('games_played', 0)
        
        if home_games >= 10 and away_games >= 10:
            confidence += 30
        elif home_games >= 5 and away_games >= 5:
            confidence += 15
        
        return min(confidence, 100.0)
