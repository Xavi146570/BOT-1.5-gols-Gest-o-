import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ValueDetector:
    """
    Calcula o valor esperado (Expected Value - EV) e a fração Kelly 
    para determinar se uma aposta tem valor.
    """
    
    def __init__(self, required_ev: float = 0.05, max_kelly_fraction: float = 0.1):
        """
        Inicializa o detector.
        Args:
            required_ev (float): Valor esperado mínimo (e.g., 0.05 = 5%).
            max_kelly_fraction (float): Fração máxima de Kelly para stake sugerida.
        """
        self.required_ev = required_ev
        self.max_kelly_fraction = max_kelly_fraction
    
    def calculate_fair_odd(self, probability: float) -> float:
        """Calcula a Odd Justa (Fair Odd) com base na probabilidade."""
        if probability <= 0:
            return float('inf')
        return 1 / probability

    # CORRIGIDO: O método agora aceita 'probability' e 'market_odds'
    def detect_value(self, probability: float, market_odds: float) -> Dict[str, Any]:
        """
        Calcula o Expected Value (EV) e determina se há valor.
        
        Args:
            probability (float): A probabilidade calculada pelo nosso modelo (0.0 a 1.0).
            market_odds (float): As odds oferecidas pela casa de apostas.
            
        Returns:
            Dict: Dicionário contendo resultados da detecção, incluindo EV e Kelly.
        """
        fair_odd = self.calculate_fair_odd(probability)
        
        # 1. Expected Value (EV)
        # EV = (P * Odd) - 1
        expected_value = (probability * market_odds) - 1
        
        # 2. Critério de Valor
        is_value = expected_value > self.required_ev
        
        # 3. Kelly Criterion (Fração Otimizada)
        # F = (P * Odd - 1) / (Odd - 1)
        if market_odds > 1.0:
            pure_kelly_fraction = expected_value / (market_odds - 1)
        else:
            pure_kelly_fraction = 0.0
            
        # Limita a stake sugerida à fração Kelly máxima definida
        suggested_stake = min(self.max_kelly_fraction, max(0.0, pure_kelly_fraction))
        
        logger.debug(f"Prob: {probability:.3f}, Odds: {market_odds:.2f}, EV: {expected_value:.2f}, Kelly: {pure_kelly_fraction:.2f}")

        return {
            'is_value': is_value,
            'expected_value': expected_value,
            'fair_odd': fair_odd,
            'pure_kelly_fraction': pure_kelly_fraction,
            'suggested_stake': suggested_stake 
        }
