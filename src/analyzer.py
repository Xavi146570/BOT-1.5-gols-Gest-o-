# src/analyzer.py
from typing import List, Dict, Any, Optional
import logging
from .api_client import APIClient, TOP_20_LEAGUES
from .probability_calculator import (
    calculate_over_probability,
    calculate_expected_value,
    calculate_kelly_criterion
)
from .database import Database
from .utils import get_utc_today_plus_days

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

class Analyzer:
    def __init__(self, api_client: APIClient, db: Database, season: int = None):
        self.api = api_client
        self.db = db
        self.season = season or 2024

    def run_daily_analysis(self, days_to_add: int = 0, leagues: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        target_date = get_utc_today_plus_days(days_to_add)
        date_str = target_date.strftime("%Y-%m-%d")
        logger.info("============================================================")
        logger.info("🚀 INICIANDO ANÁLISE DIÁRIA")
        logger.info("============================================================")
        logger.info(f"📅 A data de análise ATUAL é: {date_str} (+{days_to_add} dias)")
        leagues_to_use = leagues if leagues else TOP_20_LEAGUES

        fixtures = self.api.get_fixtures(date_str, league_id, self.season)
        if not fixtures:
            logger.warning(f"Nenhum jogo encontrado para {date_str}. Finalizando.")
            return []

        opportunities = []

        for i, fixture in enumerate(fixtures, 1):
            try:
                fixture_id = int(fixture['fixture']['id'])
                home = fixture['teams']['home']['name']
                away = fixture['teams']['away']['name']
                league_name = fixture.get('league', {}).get('name', 'Unknown')
                league_id = fixture.get('league', {}).get('id')
            except Exception as e:
                logger.error(f"Erro extrair dados da fixture: {e}")
                continue

            logger.info(f"\n--- Analisando jogo {i}/{len(fixtures)} ---")
            logger.info(f"⚽ {home} vs {away}")
            logger.info(f"   Liga: {league_name} | ID: {fixture_id}")
            logger.info("   📊 Coletando dados dos times...")

            home_stats = self.api.collect_team_data(fixture['teams']['home']['id'], league_id, season=self.season)
            away_stats = self.api.collect_team_data(fixture['teams']['away']['id'], league_id, season=self.season)
            h2h_stats = self.api.collect_h2h_data(fixture['teams']['home']['id'], fixture['teams']['away']['id'])
            odds = self.api.get_odds(fixture_id)

            if home_stats is None or away_stats is None:
                logger.warning("   ⚠️ Dados insuficientes dos times. Pulando o jogo.")
                continue

            for goal_line in [0.5, 1.5]:
                prob, conf = calculate_over_probability(home_stats, away_stats, h2h_stats, goal_line)
                odds_key = f'over_{int(goal_line*10)}_odds'
                market_odds = odds.get(odds_key) if isinstance(odds, dict) else None

                if market_odds and market_odds > 1.0:
                    ev = calculate_expected_value(prob, market_odds)
                    kelly = calculate_kelly_criterion(prob, market_odds)
                    logger.info("   🧮 Calculando probabilidades...")
                    logger.info(f"   📈 Probabilidade Over {goal_line}: {prob*100:.1f}%")
                    logger.info(f"   🎯 Confiança: {conf*100:.0f}%")
                    logger.info(f"   💵 Odds Over {goal_line}: {market_odds:.2f}")

                    if ev > 0.05:
                        logger.info(f"   ✅ VALOR DETECTADO em Over {goal_line}!")
                        logger.info(f"   💵 EV: {ev*100:.2f}%")
                        logger.info(f"   📊 Kelly Pura (F): {kelly*100:.2f}%")

                        opportunities.append({
                            'fixture_id': fixture_id,
                            'team1': home,
                            'team2': away,
                            'league': league_name,
                            'market': f'Over {goal_line}',
                            'prob': prob,
                            'odds': market_odds,
                            'ev': ev,
                            'confidence': conf,
                            'kelly': kelly
                        })
                        self.db.save_opportunity(fixture_id, home, away, league_name, f'Over {goal_line}',
                                                 prob, market_odds, ev, conf, kelly)
                    else:
                        logger.info(f"   ⚠️ Sem valor detectado em Over {goal_line} (EV: {ev*100:.2f}%).")
                else:
                    logger.info(f"   ℹ️ Odds Over {goal_line} indisponíveis ou inválidas para este fixture.")

        opportunities.sort(key=lambda x: x['ev'], reverse=True)

        logger.info("\n============================================================")
        logger.info("🎯 OPORTUNIDADES DETECTADAS (RANKED)")
        logger.info("============================================================")
        for idx, opp in enumerate(opportunities, 1):
            logger.info(f"\n{idx}. {opp['team1']} vs {opp['team2']} | Mercado: {opp['market']}")
            logger.info(f"   Liga: {opp['league']}")
            logger.info(f"   Probabilidade: {opp['prob']*100:.1f}%")
            logger.info(f"   Odds Mercado: {opp['odds']:.2f}")
            logger.info(f"   Expected Value: {opp['ev']*100:.2f}%")
            logger.info(f"   Confiança: {opp['confidence']*100:.0f}%")
            logger.info(f"   Kelly Pura (F): {opp['kelly']*100:.2f}%")

        logger.info("\n============================================================")
        logger.info(f"✅ ANÁLISE CONCLUÍDA — Oportunidades encontradas: {len(opportunities)}")
        logger.info("============================================================")
        return opportunities
