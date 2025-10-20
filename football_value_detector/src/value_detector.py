"""
Value Detector - Sistema Over 1.5
Detecta apostas com valor positivo (EV+) comparando probabilidades vs odds
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ValueDetector:
    """Detecta oportunidades de apostas com valor positivo"""
    
    # Critérios de filtragem
    MIN_CONFIDENCE = 0.60        # Confiança mínima: 60%
    MIN_EV = 0.05                # EV mínimo: +5%
    MIN_PROBABILITY = 0.65       # Probabilidade mínima Over 1.5: 65%
    MAX_ODDS = 2.50              # Odds máxima: 2.50 (probabilidade implícita 40%)
    MIN_ODDS = 1.10              # Odds mínima: 1.10 (evita odds muito baixas)
    
    def __init__(self):
        """Inicializa o detector de valor"""
        self.kelly_fraction = 0.25  # Kelly fracionário (25% do Kelly completo)
        
    def analyze_match(
        self,
        match_data: Dict,
        probability_data: Dict,
        odds_data: Dict
    ) -> Optional[Dict]:
        """
        Analisa um jogo e detecta se há valor na aposta Over 1.5
        
        Args:
            match_data: Dados do jogo (times, liga, data)
            probability_data: Probabilidades calculadas
            odds_data: Odds disponíveis
            
        Returns:
            Dict com análise completa ou None se não houver valor
        """
        try:
            # 1. Extrai dados necessários
            our_probability = probability_data.get('probability', 0)
            confidence = probability_data.get('confidence', 0)
            over_odds = odds_data.get('over_1_5_odds')
            
            if not over_odds or over_odds < self.MIN_ODDS:
                logger.debug(f"Odds Over 1.5 não disponível ou muito baixa: {over_odds}")
                return None
            
            # 2. Verifica critérios mínimos
            if not self._meets_criteria(our_probability, confidence, over_odds):
                return None
            
            # 3. Calcula métricas de valor
            implied_probability = self._calculate_implied_probability(over_odds)
            edge = our_probability - implied_probability
            expected_value = self._calculate_expected_value(our_probability, over_odds)
            
            # 4. Calcula stake recomendado (Kelly Criterion)
            kelly_stake = self._calculate_kelly_stake(
                our_probability, over_odds
            )
            
            # 5. Classifica qualidade da aposta
            bet_quality = self._classify_bet_quality(
                expected_value, confidence, edge
            )
            
            # 6. Calcula risco
            risk_level = self._calculate_risk_level(
                our_probability, confidence, over_odds
            )
            
            # 7. Monta resultado
            result = {
                'match_id': match_data.get('fixture_id'),
                'home_team': match_data.get('home_team'),
                'away_team': match_data.get('away_team'),
                'league': match_data.get('league'),
                'match_date': match_data.get('date'),
                
                # Probabilidades
                'our_probability': round(our_probability, 4),
                'implied_probability': round(implied_probability, 4),
                'confidence': round(confidence, 2),
                
                # Odds e valor
                'over_1_5_odds': round(over_odds, 2),
                'edge': round(edge, 4),
                'expected_value': round(expected_value, 4),
                
                # Recomendações
                'kelly_stake': round(kelly_stake, 2),
                'recommended_stake': round(kelly_stake * 100, 1),  # Em % do bankroll
                'bet_quality': bet_quality,
                'risk_level': risk_level,
                
                # Breakdown
                'probability_breakdown': probability_data.get('breakdown', {}),
                
                # Timestamp
                'analyzed_at': datetime.now().isoformat()
            }
            
            logger.info(
                f"✅ VALOR DETECTADO: {match_data.get('home_team')} vs "
                f"{match_data.get('away_team')} | EV: {expected_value:.2%} | "
                f"Stake: {kelly_stake:.1%} | Qualidade: {bet_quality}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao analisar jogo: {e}")
            return None
    
    def _meets_criteria(
        self,
        probability: float,
        confidence: float,
        odds: float
    ) -> bool:
        """
        Verifica se o jogo atende aos critérios mínimos
        """
        # 1. Probabilidade mínima
        if probability < self.MIN_PROBABILITY:
            logger.debug(f"Probabilidade muito baixa: {probability:.2%}")
            return False
        
        # 2. Confiança mínima
        if confidence < self.MIN_CONFIDENCE:
            logger.debug(f"Confiança muito baixa: {confidence:.1%}")
            return False
        
        # 3. Odds dentro do range
        if odds > self.MAX_ODDS:
            logger.debug(f"Odds muito alta: {odds}")
            return False
        
        # 4. Verifica se há valor (EV+)
        ev = self._calculate_expected_value(probability, odds)
        if ev < self.MIN_EV:
            logger.debug(f"EV muito baixo: {ev:.2%}")
            return False
        
        return True
    
    def _calculate_implied_probability(self, odds: float) -> float:
        """
        Calcula probabilidade implícita das odds
        
        Implied Probability = 1 / odds
        """
        try:
            return 1.0 / odds
        except ZeroDivisionError:
            return 0.0
    
    def _calculate_expected_value(
        self,
        our_probability: float,
        odds: float
    ) -> float:
        """
        Calcula Expected Value (EV)
        
        EV = (Probabilidade × Odds) - 1
        EV > 0 = Aposta com valor
        EV < 0 = Aposta sem valor
        
        Exemplo:
        - Nossa prob: 75% (0.75)
        - Odds: 1.50
        - EV = (0.75 × 1.50) - 1 = 0.125 = +12.5%
        """
        try:
            ev = (our_probability * odds) - 1.0
            return ev
        except Exception as e:
            logger.error(f"Erro ao calcular EV: {e}")
            return 0.0
    
    def _calculate_kelly_stake(
        self,
        probability: float,
        odds: float
    ) -> float:
        """
        Calcula stake recomendado usando Kelly Criterion
        
        Kelly = (bp - q) / b
        Onde:
        - b = odds - 1 (decimal odds - 1)
        - p = nossa probabilidade
        - q = 1 - p (probabilidade de perder)
        
        Usamos Kelly fracionário (25%) para reduzir variância
        """
        try:
            b = odds - 1.0
            p = probability
            q = 1.0 - p
            
            # Kelly completo
            kelly = (b * p - q) / b
            
            # Kelly fracionário (25%)
            fractional_kelly = kelly * self.kelly_fraction
            
            # Limita stake máximo a 10% do bankroll
            stake = max(0.0, min(fractional_kelly, 0.10))
            
            return stake
            
        except Exception as e:
            logger.error(f"Erro ao calcular Kelly: {e}")
            return 0.01  # 1% default
    
    def _classify_bet_quality(
        self,
        expected_value: float,
        confidence: float,
        edge: float
    ) -> str:
        """
        Classifica qualidade da aposta
        
        Considera: EV, Confiança e Edge
        """
        # Pontuação combinada
        score = (expected_value * 0.4) + (confidence/100 * 0.3) + (edge * 0.3)
        
        if score >= 0.25 and confidence >= 80:
            return "EXCELENTE"
        elif score >= 0.20 and confidence >= 70:
            return "MUITO BOA"
        elif score >= 0.15 and confidence >= 60:
            return "BOA"
        elif score >= 0.10:
            return "REGULAR"
        else:
            return "FRACA"
    
    def _calculate_risk_level(
        self,
        probability: float,
        confidence: float,
        odds: float
    ) -> str:
        """
        Calcula nível de risco da aposta
        """
        # Fatores de risco
        risk_score = 0
        
        # 1. Probabilidade (quanto menor, maior risco)
        if probability < 0.70:
            risk_score += 2
        elif probability < 0.75:
            risk_score += 1
        
        # 2. Confiança (quanto menor, maior risco)
        if confidence < 70:
            risk_score += 2
        elif confidence < 80:
            risk_score += 1
        
        # 3. Odds (quanto maior, maior risco)
        if odds > 2.0:
            risk_score += 2
        elif odds > 1.7:
            risk_score += 1
        
        # Classifica risco
        if risk_score == 0:
            return "BAIXO"
        elif risk_score <= 2:
            return "MODERADO"
        elif risk_score <= 4:
            return "ALTO"
        else:
            return "MUITO ALTO"
    
    def rank_opportunities(
        self,
        opportunities: List[Dict]
    ) -> List[Dict]:
        """
        Rankeia oportunidades por qualidade
        
        Ordena por: EV × Confiança
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
    
    def generate_summary(
        self,
        opportunities: List[Dict]
    ) -> Dict:
        """
        Gera sumário das oportunidades encontradas
        """
        try:
            if not opportunities:
                return {
                    'total_opportunities': 0,
                    'avg_ev': 0,
                    'avg_confidence': 0,
                    'total_kelly_stake': 0,
                    'quality_distribution': {}
                }
            
            total = len(opportunities)
            
            # Médias
            avg_ev = sum(o['expected_value'] for o in opportunities) / total
            avg_conf = sum(o['confidence'] for o in opportunities) / total
            total_stake = sum(o['kelly_stake'] for o in opportunities)
            
            # Distribuição por qualidade
            quality_dist = {}
            for opp in opportunities:
                quality = opp['bet_quality']
                quality_dist[quality] = quality_dist.get(quality, 0) + 1
            
            # Distribuição por risco
            risk_dist = {}
            for opp in opportunities:
                risk = opp['risk_level']
                risk_dist[risk] = risk_dist.get(risk, 0) + 1
            
            return {
                'total_opportunities': total,
                'avg_ev': round(avg_ev, 4),
                'avg_confidence': round(avg_conf, 2),
                'total_kelly_stake': round(total_stake, 4),
                'quality_distribution': quality_dist,
                'risk_distribution': risk_dist,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar sumário: {e}")
            return {}

