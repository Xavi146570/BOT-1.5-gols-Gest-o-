"""
Value Detector - Sistema Over 1.5
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ValueDetector:
    """Detecta oportunidades com valor"""
    
    MIN_CONFIDENCE = 0.60
    MIN_EV = 0.05
    MIN_PROBABILITY = 0.65
    MAX_ODDS = 2.50
    MIN_ODDS = 1.10
    
    def __init__(self):
        self.kelly_fraction = 0.25
    
    def analyze_match(self, match_data: Dict, probability_data: Dict, odds_data: Dict) -> Optional[Dict]:
        """Analisa jogo e detecta valor"""
        try:
            our_probability = probability_data.get('probability', 0)
            confidence = probability_data.get('confidence', 0)
            over_odds = odds_data.get('over_1_5_odds')
            
            if not over_odds or over_odds < self.MIN_ODDS:
                return None
            
            if not self._meets_criteria(our_probability, confidence, over_odds):
                return None
            
            implied_probability = 1.0 / over_odds
            edge = our_probability - implied_probability
            expected_value = (our_probability * over_odds) - 1.0
            kelly_stake = self._calculate_kelly_stake(our_probability, over_odds)
            bet_quality = self._classify_bet_quality(expected_value, confidence)
            risk_level = self._calculate_risk_level(our_probability, confidence)
            
            return {
                'match_id': match_data.get('fixture_id'),
                'home_team': match_data.get('home_team'),
                'away_team': match_data.get('away_team'),
                'league': match_data.get('league'),
                'match_date': match_data.get('date'),
                'our_probability': round(our_probability, 4),
                'implied_probability': round(implied_probability, 4),
                'confidence': round(confidence, 2),
                'over_1_5_odds': round(over_odds, 2),
                'edge': round(edge, 4),
                'expected_value': round(expected_value, 4),
                'kelly_stake': round(kelly_stake, 4),
                'recommended_stake': round(kelly_stake * 100, 1),
                'bet_quality': bet_quality,
                'risk_level': risk_level,
                'probability_breakdown': probability_data.get('breakdown', {}),
                'analyzed_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao analisar jogo: {e}")
            return None
    
    def _meets_criteria(self, probability: float, confidence: float, odds: float) -> bool:
        if probability < self.MIN_PROBABILITY:
            return False
        if confidence < self.MIN_CONFIDENCE:
            return False
        if odds > self.MAX_ODDS or odds < self.MIN_ODDS:
            return False
        ev = (probability * odds) - 1.0
        if ev < self.MIN_EV:
            return False
        return True
    
    def _calculate_kelly_stake(self, probability: float, odds: float) -> float:
        try:
            b = odds - 1.0
            p = probability
            q = 1.0 - p
            kelly = (b * p - q) / b
            fractional_kelly = kelly * self.kelly_fraction
            return max(0.0, min(fractional_kelly, 0.10))
        except Exception:
            return 0.01
    
    def _classify_bet_quality(self, ev: float, confidence: float) -> str:
        score = (ev * 0.6) + (confidence/100 * 0.4)
        if score >= 0.20 and confidence >= 80:
            return "EXCELENTE"
        elif score >= 0.15 and confidence >= 70:
            return "MUITO BOA"
        elif score >= 0.10 and confidence >= 60:
            return "BOA"
        else:
            return "REGULAR"
    
    def _calculate_risk_level(self, probability: float, confidence: float) -> str:
        risk_score = 0
        if probability < 0.70:
            risk_score += 2
        if confidence < 70:
            risk_score += 2
        if risk_score == 0:
            return "BAIXO"
        elif risk_score <= 2:
            return "MODERADO"
        else:
            return "ALTO"

# ADICIONE ESTE MÉTODO AQUI:
    def rank_opportunities(
        self,
        opportunities: List[Dict]
    ) -> List[Dict]:
        """
        Rankeia oportunidades por qualidade
        
        Ordena por: EV × Confiança
        
        Args:
            opportunities: Lista de oportunidades
            
        Returns:
            Lista ordenada por ranking
        """
        try:
            if not opportunities:
                return []
            
            # Adiciona score de ranking
            for opp in opportunities:
                ev = opp.get('expected_value', 0)
                conf = opp.get('confidence', 0) / 100
                opp['ranking_score'] = ev * conf
            
            # Ordena por score (maior primeiro)
            ranked = sorted(
                opportunities,
                key=lambda x: x.get('ranking_score', 0),
                reverse=True
            )
            
            return ranked
            
        except Exception as e:
            logger.error(f"Erro ao rankear oportunidades: {e}")
            return opportunities

