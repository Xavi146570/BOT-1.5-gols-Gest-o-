import logging
from typing import Dict, Any, List

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

    def detect_value(self, probability: float, market_odds: float) -> Dict[str, Any]:
        """
        Calcula o Expected Value (EV) e determina se há valor.
        
        Args:
            probability (float): A probabilidade calculada pelo nosso modelo (0.0 a 1.0).
            market_odds (float): As odds oferecidas pela casa de apostas.
            
        Returns:
            Dict: Dicionário contendo resultados da detecção, incluindo EV e Kelly.
        """
        # ... (Mantido o código de detecção anterior)
        fair_odd = self.calculate_fair_odd(probability)
        expected_value = (probability * market_odds) - 1
        is_value = expected_value > self.required_ev
        
        if market_odds > 1.0:
            pure_kelly_fraction = expected_value / (market_odds - 1)
        else:
            pure_kelly_fraction = 0.0
            
        suggested_stake = min(self.max_kelly_fraction, max(0.0, pure_kelly_fraction))
        
        logger.debug(f"Prob: {probability:.3f}, Odds: {market_odds:.2f}, EV: {expected_value:.2f}, Kelly: {pure_kelly_fraction:.2f}")

        return {
            'is_value': is_value,
            'expected_value': expected_value,
            'fair_odd': fair_odd,
            'pure_kelly_fraction': pure_kelly_fraction,
            'suggested_stake': suggested_stake 
        }

    def rank_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rankea as oportunidades com base no Expected Value (EV) e na Confiança.
        Oportunidades com maior EV são priorizadas, seguidas pela maior confiança.
        
        Args:
            opportunities (List[Dict]): Lista de dicionários de oportunidades.
            
        Returns:
            List[Dict]: Lista classificada de oportunidades.
        """
        if not opportunities:
            return []
        
        # Classifica por EV (decrescente) e depois por Confiança (decrescente)
        # Multiplicamos por -1 para obter a classificação decrescente
        return sorted(
            opportunities, 
            key=lambda x: (x['expected_value'] * -1, x['confidence'] * -1)
        )
