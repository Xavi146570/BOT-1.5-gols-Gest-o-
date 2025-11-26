# src/probability_calculator.py
import math
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("src.probability_calculator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    import sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def poisson_pmf(k: int, mu: float) -> float:
    """Poisson PMF."""
    if mu is None:
        return 0.0
    try:
        return math.exp(-mu) * (mu ** k) / math.factorial(k)
    except Exception:
        return 0.0

def poisson_cdf(k: int, mu: float) -> float:
    """CDF P(X <= k)."""
    s = 0.0
    for i in range(0, k + 1):
        s += poisson_pmf(i, mu)
    return s

def prob_total_over(mu_total: float, line: float) -> float:
    """Probabilidade total > line, assumindo total ~ Poisson(mu_total)."""
    # line pode ser 0.5, 1.5 etc -> converter para inteiro k = floor(line)
    # Prob(Total > line) = 1 - P(Total <= floor(line))
    k = int(math.floor(line))
    cdf = poisson_cdf(k, mu_total)
    return max(0.0, 1.0 - cdf)

def calculate_over_probability(home_stats: Dict[str, Any],
                               away_stats: Dict[str, Any],
                               h2h_stats: Optional[Dict[str, Any]],
                               goal_line: float) -> Tuple[float, float]:
    """
    Retorna (probability, confidence)
    - prob: probabilidade estimada de Over goal_line (ex.: 1.5 -> >1.5)
    - confidence: métrica heurística [0..1] sobre qualidade dos dados
    """
    # Extrair médias de golos por equipa
    try:
        home_gf = home_stats.get('goals_for_avg') if home_stats else None
        away_gf = away_stats.get('goals_for_avg') if away_stats else None

        # Fallback razoável: se faltar, tentar extrair de over rates
        if home_gf is None:
            h_over15 = home_stats.get('over_1_5_rate') if home_stats else None
            if h_over15:
                home_gf = max(0.5, min(2.5, h_over15 * 2.0))
        if away_gf is None:
            a_over15 = away_stats.get('over_1_5_rate') if away_stats else None
            if a_over15:
                away_gf = max(0.5, min(2.5, a_over15 * 2.0))

        # Se ainda None, assume 1.2 padrão conservador
        if home_gf is None:
            home_gf = 1.2
        if away_gf is None:
            away_gf = 1.2

        # Ajuste simples por H2H histórico (média multiplicativa)
        h2h_adj = 1.0
        if h2h_stats and isinstance(h2h_stats, dict):
            h2h_over15 = h2h_stats.get('h2h_over_1_5_rate')
            if h2h_over15:
                # escala 0.8..1.15
                h2h_adj = 0.9 + 0.3 * h2h_over15

        mu_total = (home_gf + away_gf) * h2h_adj

        prob = prob_total_over(mu_total, goal_line)

        # Confiança heurística: mais dados disponíveis -> maior confiança
        conf = 0.5
        available = 0
        for v in [home_stats, away_stats, h2h_stats]:
            if v:
                available += 1
        conf = min(0.99, 0.33 * available + 0.34)  # roughly: 0.34, 0.67, 1.0
        logger.info(f"Prob Over {goal_line}: mu_total={mu_total:.2f} -> prob={prob:.3f} conf={conf:.2f}")
        return prob, conf
    except Exception as e:
        logger.error(f"Erro em calculate_over_probability: {e}")
        return 0.0, 0.0

def calculate_expected_value(prob: float, odds: float) -> float:
    """
    Retorna EV como prob - (1/odds). Ex: prob=0.6, odds=2 -> EV=0.1 (10%)
    """
    try:
        return max(-1.0, prob - (1.0 / odds))
    except Exception:
        return 0.0

def calculate_kelly_criterion(prob: float, odds: float) -> float:
    """
    Kelly fraction (decimal). Simplified formula:
    f* = (bp - q) / b where b = odds - 1, q = 1 - p
    Retorna fração (0..1) - pode ser negativo.
    """
    try:
        b = odds - 1.0
        q = 1.0 - prob
        if b <= 0:
            return 0.0
        f = (b * prob - q) / b
        return max(0.0, f)
    except Exception:
        return 0.0
