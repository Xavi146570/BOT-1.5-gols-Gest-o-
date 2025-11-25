# -*- coding: utf-8 -*-
import math
from typing import Dict, Any

# ==============================================================================
# PESOS DOS INDICADORES (NOVA VERSÃO: 6 INDICADORES, Antes 9)
# Total deve somar 1.0 (100%)
# Foco em indicadores matemáticos e de força ofensiva para Over 1.5
# ==============================================================================

# Antigos indicadores removidos e pesos redistribuídos:
# - Tendência Ofensiva (8%) -> Adicionado à Força Ofensiva
# - Fase Temporada (8%) -> Adicionado à Motivação
# - Importância (5%) -> Adicionado a Poisson e Taxa Histórica
# ==============================================================================

INDICATOR_WEIGHTS: Dict[str, float] = {
    # PRIMÁRIOS (58%): Foco na Matemática e Histórico Básico
    "poisson_probability": 0.29,     # Base matemática fundamental (+4% redistribuído)
    "historical_rate": 0.19,         # Taxa Histórica da temporada (+4% redistribuído)
    "recent_trend": 0.10,            # Tendência dos últimos 5 jogos (inalterado)

    # SECUNDÁRIOS (30%): Foco na Força Ofensiva
    "h2h_rate": 0.12,                # Confrontos diretos (inalterado)
    "offensive_strength": 0.18,      # Média de Gols Marcados (+8% redistribuído da Tend. Ofensiva)

    # CONTEXTUAIS (12%): Foco na Motivação
    "motivation_factor": 0.12,       # Fator motivacional (título, rebaixamento) (+5% redistribuído de Importância/Fase)
    
    # Total de Pesos: 0.29 + 0.19 + 0.10 + 0.12 + 0.18 + 0.12 = 1.00 (100%)
}


class ProbabilityCalculator:
    """
    Calcula a probabilidade total de Over 1.5 gols (Total de Gols >= 2)
    usando o modelo de Poisson e ajustando com 5 indicadores de ponderação.
    """

    def _calculate_poisson_over_probability(self, lambda_value: float) -> float:
        """
        Calcula P(Over 1.5) = 1 - P(0 Gols) - P(1 Gol)
        P(X=k) = (e^(-λ) * λ^k) / k!

        Para k=0 e k=1:
        P(0) = e^(-λ) * 1 / 1 = e^(-λ)
        P(1) = e^(-λ) * λ / 1 = e^(-λ) * λ

        P(Under 1.5) = P(0) + P(1) = e^(-λ) * (1 + λ)
        P(Over 1.5) = 1 - [e^(-λ) * (1 + λ)]
        """
        try:
            p_under_1_5 = math.exp(-lambda_value) * (1 + lambda_value)
            p_over_1_5 = 1.0 - p_under_1_5
            # Garante que a probabilidade não exceda 100% ou seja negativa
            return max(0.0, min(1.0, p_over_1_5))
        except ValueError:
            return 0.0

    def calculate_probability(self, data: Dict[str, Any]) -> float:
        """
        Calcula a probabilidade final ponderada de Over 1.5.
        
        Args:
            data: Dicionário contendo todos os dados e indicadores necessários.
        
        Returns:
            A probabilidade final (0.0 a 1.0).
        """
        # 1. Indicador base: Probabilidade de Poisson (Requer lambda)
        lambda_value = data.get('expected_goals_lambda', 0.0)
        poisson_prob = self._calculate_poisson_over_probability(lambda_value)
        
        # O modelo exige que os 5 indicadores restantes (0.0 a 1.0) estejam presentes
        try:
            # Indicadores Secundários/Contextuais (devem ser normalizados entre 0 e 1)
            indicators = {
                "poisson_probability": poisson_prob, # Já é um float (0-1)
                "historical_rate": data['home_over_1_5_rate'] * data['away_over_1_5_rate'], # Exemplo de como pode ser um fator composto
                "recent_trend": data['recent_over_1_5_rate'],
                "h2h_rate": data['h2h_over_1_5_rate'],
                "offensive_strength": data['home_offensive_score'] * data['away_offensive_score'], # Fator de força ofensiva
                "motivation_factor": data['combined_motivation_score'], # Fator de motivação (já absorve fase/importância)
            }
        except KeyError as e:
            # Caso falte algum dado essencial para a ponderação
            print(f"ERRO: Dados de indicador em falta: {e}")
            return 0.0 

        final_probability = 0.0
        
        # 2. Ponderação
        for indicator, weight in INDICATOR_WEIGHTS.items():
            # A Taxa Histórica e Força Ofensiva são simplificadas aqui como valores diretos (0-1)
            # Na implementação real, 'indicators[indicator]' deve ser o valor normalizado
            if indicator in indicators:
                final_probability += indicators[indicator] * weight
            else:
                print(f"AVISO: Indicador {indicator} não encontrado na lista de dados. Usando peso zero.")

        # Garante que o resultado final está no range correto
        return max(0.0, min(1.0, final_probability))
