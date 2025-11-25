# -*- coding: utf-8 -*-
from typing import Dict, Any

# ==============================================================================
# CRITÉRIOS DE DETECÇÃO DE VALOR AJUSTADOS PARA OVER 1.5
# Estes parâmetros controlam o rigor da filtragem de oportunidades (EV+)
# ==============================================================================

# Ajuste do Range de Odds: Aumentado de 1.10 para 1.35 para focar em retornos
# mais significativos e evitar odds com baixo EV potencial.
MIN_PROBABILITY: float = 0.65  # Probabilidade mínima do nosso sistema (65%)
MIN_ODDS: float = 1.35         # Odds Mínimas Requeridas (AUMENTADO de 1.10 para 1.35)
MAX_ODDS: float = 2.50         # Odds Máximas Requeridas (Acima disso, o risco é muito alto para Over 1.5)
MIN_EXPECTED_VALUE: float = 0.05  # Valor Esperado Mínimo de +5%
MIN_CONFIDENCE_SCORE: float = 0.60 # Pontuação de Confiança da Análise Mínima (60%)


class ValueDetector:
    """
    Classe responsável por aplicar os critérios e determinar se uma aposta
    no mercado Over 1.5 Gols tem Valor Esperado Positivo (EV+).
    """

    def calculate_expected_value(self, our_probability: float, market_odds: float) -> float:
        """
        Calcula o Valor Esperado (EV)
        Fórmula: EV = (Probabilidade * Odds) - 1
        """
        return (our_probability * market_odds) - 1.0

    def detect_value(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica todos os filtros para encontrar oportunidades de EV+.
        
        Args:
            game_data: Dicionário contendo 'our_probability' e 'over_1_5_odds'.
            
        Returns:
            Dicionário com o resultado da detecção (True/False) e métricas.
        """
        
        our_probability = game_data.get('our_probability', 0.0)
        market_odds = game_data.get('over_1_5_odds', 0.0)
        confidence_score = game_data.get('confidence_score', 0.0) # Assume-se que o sistema calcula a confiança

        # 1. Filtragem por Range de Odds
        if not (MIN_ODDS <= market_odds <= MAX_ODDS):
            return {"is_value": False, "reason": "Odds fora do range [1.35 - 2.50]"}

        # 2. Filtragem por Probabilidade Mínima do Sistema
        if our_probability < MIN_PROBABILITY:
            return {"is_value": False, "reason": "Probabilidade abaixo do mínimo (65%)"}

        # 3. Filtragem por Confiança Mínima
        if confidence_score < MIN_CONFIDENCE_SCORE:
            return {"is_value": False, "reason": "Confiança da análise abaixo do mínimo (60%)"}

        # 4. Cálculo e Filtragem do Expected Value (EV)
        expected_value = self.calculate_expected_value(our_probability, market_odds)
        
        if expected_value < MIN_EXPECTED_VALUE:
            return {"is_value": False, "reason": f"EV abaixo do mínimo (+{MIN_EXPECTED_VALUE*100:.0f}%)"}
            
        # 5. Oportunidade de Valor Encontrada
        return {
            "is_value": True,
            "expected_value": expected_value,
            "suggested_stake": self._calculate_stake(our_probability, market_odds, expected_value) # Função fictícia
        }

    # Função placeholder para o Kelly Criterion (A ser implementada)
    def _calculate_stake(self, prob, odds, ev):
        """Calcula a stake usando uma fração do Kelly Criterion."""
        # Fórmula simplificada: (Odds * Probabilidade - 1) / (Odds - 1)
        kelly_fraction = max(0.0, (prob * odds - 1) / (odds - 1))
        # Para evitar volatilidade excessiva, usamos uma fração (ex: 1/4)
        return kelly_fraction * 0.25 # Retorna a porcentagem do bankroll a apostar
