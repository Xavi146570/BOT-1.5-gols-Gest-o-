"""
Probability Calculator - Sistema Over 1.5
Calcula probabilidades de jogos terem 2+ gols usando múltiplos indicadores
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math

logger = logging.getLogger(__name__)


class ProbabilityCalculator:
    """Calcula probabilidades Over 1.5 usando múltiplos métodos"""
    
    # Pesos dos indicadores (total = 100%)
    WEIGHTS = {
        'poisson': 0.25,           # 25% - Modelo estatístico base
        'historical_rate': 0.15,   # 15% - Taxa histórica Over 1.5
        'recent_trend': 0.10,      # 10% - Tendência recente
        'h2h': 0.12,               # 12% - Confrontos diretos
        'offensive_strength': 0.10, # 10% - Força ofensiva
        'offensive_trend': 0.08,   # 8% - Tendência ofensiva
        'season_phase': 0.08,      # 8% - Fase da temporada
        'motivation': 0.07,        # 7% - Motivação dos times
        'match_importance': 0.05   # 5% - Importância do jogo
    }
    
    def __init__(self):
        """Inicializa o calculador"""
        self.baseline_over_rate = 0.72  # ~72% dos jogos têm Over 1.5
        
    def calculate_probability(
        self,
        home_stats: Dict,
        away_stats: Dict,
        h2h_data: Optional[Dict] = None,
        match_context: Optional[Dict] = None
    ) -> Dict:
        """
        Calcula probabilidade final de Over 1.5
        
        Args:
            home_stats: Estatísticas do time da casa
            away_stats: Estatísticas do time visitante
            h2h_data: Dados de confrontos diretos
            match_context: Contexto do jogo (fase, importância, etc)
            
        Returns:
            Dict com probabilidade final e breakdown
        """
        try:
            # 1. INDICADORES PRIMÁRIOS (50%)
            poisson_prob = self._calculate_poisson_over_probability(
                home_stats, away_stats
            )
            
            historical_prob = self._calculate_historical_rate(
                home_stats, away_stats
            )
            
            recent_prob = self._calculate_recent_trend(
                home_stats, away_stats
            )
            
            # 2. INDICADORES SECUNDÁRIOS (30%)
            h2h_prob = self._calculate_h2h_probability(h2h_data)
            
            offensive_prob = self._calculate_offensive_strength(
                home_stats, away_stats
            )
            
            offensive_trend_prob = self._calculate_offensive_trend(
                home_stats, away_stats
            )
            
            # 3. INDICADORES CONTEXTUAIS (20%)
            season_adjustment = self._calculate_season_phase_adjustment(
                match_context
            )
            
            motivation_adjustment = self._calculate_motivation_factor(
                match_context
            )
            
            importance_adjustment = self._calculate_match_importance(
                match_context
            )
            
            # 4. CÁLCULO FINAL PONDERADO
            final_probability = (
                poisson_prob * self.WEIGHTS['poisson'] +
                historical_prob * self.WEIGHTS['historical_rate'] +
                recent_prob * self.WEIGHTS['recent_trend'] +
                h2h_prob * self.WEIGHTS['h2h'] +
                offensive_prob * self.WEIGHTS['offensive_strength'] +
                offensive_trend_prob * self.WEIGHTS['offensive_trend'] +
                season_adjustment * self.WEIGHTS['season_phase'] +
                motivation_adjustment * self.WEIGHTS['motivation'] +
                importance_adjustment * self.WEIGHTS['match_importance']
            )
            
            # Garantir que está entre 0 e 1
            final_probability = max(0.0, min(1.0, final_probability))
            
            # 5. CONFIANÇA DO CÁLCULO
            confidence = self._calculate_confidence(
                home_stats, away_stats, h2h_data
            )
            
            return {
                'probability': round(final_probability, 4),
                'confidence': round(confidence, 2),
                'breakdown': {
                    'poisson': round(poisson_prob, 4),
                    'historical_rate': round(historical_prob, 4),
                    'recent_trend': round(recent_prob, 4),
                    'h2h': round(h2h_prob, 4),
                    'offensive_strength': round(offensive_prob, 4),
                    'offensive_trend': round(offensive_trend_prob, 4),
                    'season_phase': round(season_adjustment, 4),
                    'motivation': round(motivation_adjustment, 4),
                    'match_importance': round(importance_adjustment, 4)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular probabilidade: {e}")
            return {
                'probability': self.baseline_over_rate,
                'confidence': 0.30,
                'breakdown': {},
                'error': str(e)
            }
    
    def _calculate_poisson_over_probability(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Calcula P(Over 1.5) usando Distribuição de Poisson
        
        Over 1.5 = Pelo menos 2 gols
        P(Over 1.5) = 1 - P(Under 1.5)
        P(Under 1.5) = P(0 gols) + P(1 gol)
        
        Usando Poisson: P(X=k) = (λ^k * e^-λ) / k!
        P(Under 1.5) = e^-λ × (1 + λ)
        """
        try:
            # Gols esperados do time da casa
            home_attack = home_stats.get('goals_for_avg', 1.5)
            away_defense = away_stats.get('goals_against_avg', 1.5)
            lambda_home = (home_attack + away_defense) / 2
            
            # Gols esperados do time visitante
            away_attack = away_stats.get('goals_for_avg', 1.2)
            home_defense = home_stats.get('goals_against_avg', 1.2)
            lambda_away = (away_attack + home_defense) / 2
            
            # Lambda total (gols esperados no jogo)
            lambda_total = lambda_home + lambda_away
            
            # P(Under 1.5) = e^-λ × (1 + λ)
            prob_under = math.exp(-lambda_total) * (1 + lambda_total)
            
            # P(Over 1.5) = 1 - P(Under 1.5)
            prob_over = 1 - prob_under
            
            logger.debug(f"Poisson: λ_home={lambda_home:.2f}, λ_away={lambda_away:.2f}, "
                        f"λ_total={lambda_total:.2f}, P(Over 1.5)={prob_over:.4f}")
            
            return prob_over
            
        except Exception as e:
            logger.error(f"Erro no cálculo Poisson: {e}")
            return self.baseline_over_rate
    
    def _calculate_historical_rate(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Calcula probabilidade baseada na taxa histórica Over 1.5
        """
        try:
            home_rate = home_stats.get('over_1_5_rate', 0.72)
            away_rate = away_stats.get('over_1_5_rate', 0.72)
            
            # Média ponderada (casa tem mais peso)
            historical_prob = (home_rate * 0.55) + (away_rate * 0.45)
            
            return historical_prob
            
        except Exception as e:
            logger.error(f"Erro ao calcular taxa histórica: {e}")
            return self.baseline_over_rate
    
    def _calculate_recent_trend(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Analisa tendência recente (últimos 5 jogos)
        """
        try:
            home_recent = home_stats.get('recent_over_1_5_rate', 0.72)
            away_recent = away_stats.get('recent_over_1_5_rate', 0.72)
            
            # Média das tendências recentes
            recent_prob = (home_recent + away_recent) / 2
            
            return recent_prob
            
        except Exception as e:
            logger.error(f"Erro ao calcular tendência recente: {e}")
            return self.baseline_over_rate
    
    def _calculate_h2h_probability(
        self,
        h2h_data: Optional[Dict]
    ) -> float:
        """
        Calcula probabilidade baseada em confrontos diretos
        """
        try:
            if not h2h_data or not h2h_data.get('matches'):
                return self.baseline_over_rate
            
            matches = h2h_data['matches']
            if len(matches) == 0:
                return self.baseline_over_rate
            
            # Conta jogos Over 1.5 no H2H
            over_count = sum(
                1 for match in matches
                if match.get('total_goals', 0) >= 2
            )
            
            h2h_rate = over_count / len(matches)
            
            # Dá menos peso se tiver poucos jogos H2H
            if len(matches) < 3:
                h2h_rate = (h2h_rate * 0.6) + (self.baseline_over_rate * 0.4)
            
            return h2h_rate
            
        except Exception as e:
            logger.error(f"Erro ao calcular H2H: {e}")
            return self.baseline_over_rate
    
    def _calculate_offensive_strength(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Avalia força ofensiva combinada dos times
        """
        try:
            home_attack = home_stats.get('goals_for_avg', 1.5)
            away_attack = away_stats.get('goals_for_avg', 1.2)
            
            total_attack = home_attack + away_attack
            
            # Normaliza para probabilidade
            # Se total_attack >= 3.0, prob = 0.85+
            # Se total_attack <= 1.5, prob = 0.50-
            if total_attack >= 3.0:
                prob = 0.85 + min((total_attack - 3.0) * 0.05, 0.10)
            elif total_attack >= 2.5:
                prob = 0.75
            elif total_attack >= 2.0:
                prob = 0.65
            else:
                prob = 0.50 + (total_attack - 1.5) * 0.3
            
            return min(prob, 0.95)
            
        except Exception as e:
            logger.error(f"Erro ao calcular força ofensiva: {e}")
            return self.baseline_over_rate
    
    def _calculate_offensive_trend(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Avalia tendência ofensiva recente
        """
        try:
            home_trend = home_stats.get('recent_goals_avg', 1.5)
            away_trend = away_stats.get('recent_goals_avg', 1.2)
            
            # Compara com média geral
            home_general = home_stats.get('goals_for_avg', 1.5)
            away_general = away_stats.get('goals_for_avg', 1.2)
            
            # Se times estão marcando mais recentemente = maior prob Over
            home_improvement = (home_trend / home_general) if home_general > 0 else 1.0
            away_improvement = (away_trend / away_general) if away_general > 0 else 1.0
            
            avg_improvement = (home_improvement + away_improvement) / 2
            
            # Ajusta baseline baseado na melhora
            prob = self.baseline_over_rate * avg_improvement
            
            return min(prob, 0.95)
            
        except Exception as e:
            logger.error(f"Erro ao calcular tendência ofensiva: {e}")
            return self.baseline_over_rate
    
    def _calculate_season_phase_adjustment(
        self,
        match_context: Optional[Dict]
    ) -> float:
        """
        Ajusta baseado na fase da temporada
        Início: times mais cautelosos
        Final: times mais agressivos (necessidade de pontos)
        """
        try:
            if not match_context:
                return self.baseline_over_rate
            
            round_num = match_context.get('round', 20)
            total_rounds = match_context.get('total_rounds', 38)
            
            phase = round_num / total_rounds
            
            # Início (0-0.25): 0.70
            # Meio (0.25-0.75): 0.72
            # Final (0.75-1.0): 0.75
            if phase < 0.25:
                return 0.70
            elif phase < 0.75:
                return 0.72
            else:
                return 0.75
                
        except Exception as e:
            logger.error(f"Erro ao calcular fase da temporada: {e}")
            return self.baseline_over_rate
    
    def _calculate_motivation_factor(
        self,
        match_context: Optional[Dict]
    ) -> float:
        """
        Avalia motivação dos times (título, Europa, rebaixamento)
        Times motivados = mais gols
        """
        try:
            if not match_context:
                return self.baseline_over_rate
            
            home_position = match_context.get('home_position', 10)
            away_position = match_context.get('away_position', 10)
            total_teams = match_context.get('total_teams', 20)
            
            # Times no topo (1-4) ou no fundo (últimos 3) = alta motivação
            high_motivation_positions = list(range(1, 5)) + \
                                       list(range(total_teams - 2, total_teams + 1))
            
            home_motivated = home_position in high_motivation_positions
            away_motivated = away_position in high_motivation_positions
            
            if home_motivated and away_motivated:
                return 0.78  # Ambos motivados = jogo aberto
            elif home_motivated or away_motivated:
                return 0.75  # Um motivado
            else:
                return 0.70  # Jogo morno
                
        except Exception as e:
            logger.error(f"Erro ao calcular motivação: {e}")
            return self.baseline_over_rate
    
    def _calculate_match_importance(
        self,
        match_context: Optional[Dict]
    ) -> float:
        """
        Avalia importância do jogo
        Derby, clássico = mais gols
        """
        try:
            if not match_context:
                return self.baseline_over_rate
            
            is_derby = match_context.get('is_derby', False)
            is_classic = match_context.get('is_classic', False)
            
            if is_derby or is_classic:
                return 0.78
            
            return self.baseline_over_rate
            
        except Exception as e:
            logger.error(f"Erro ao calcular importância: {e}")
            return self.baseline_over_rate
    
    def _calculate_confidence(
        self,
        home_stats: Dict,
        away_stats: Dict,
        h2h_data: Optional[Dict]
    ) -> float:
        """
        Calcula nível de confiança do cálculo (0-100%)
        """
        confidence = 50.0  # Base
        
        try:
            # +20% se tiver dados suficientes dos times
            home_games = home_stats.get('games_played', 0)
            away_games = away_stats.get('games_played', 0)
            
            if home_games >= 10 and away_games >= 10:
                confidence += 20
            elif home_games >= 5 and away_games >= 5:
                confidence += 10
            
            # +15% se tiver H2H recente
            if h2h_data and len(h2h_data.get('matches', [])) >= 3:
                confidence += 15
            elif h2h_data and len(h2h_data.get('matches', [])) >= 1:
                confidence += 7
            
            # +15% se estatísticas forem consistentes
            home_consistency = abs(
                home_stats.get('over_1_5_rate', 0.72) - 
                home_stats.get('recent_over_1_5_rate', 0.72)
            )
            away_consistency = abs(
                away_stats.get('over_1_5_rate', 0.72) - 
                away_stats.get('recent_over_1_5_rate', 0.72)
            )
            
            avg_consistency = (home_consistency + away_consistency) / 2
            if avg_consistency < 0.10:
                confidence += 15
            elif avg_consistency < 0.20:
                confidence += 8
            
            return min(confidence, 100.0)
            
        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 50.0

