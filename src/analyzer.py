# src/analyzer.py
import os
import logging
from datetime import datetime
from src.api_client import APIClient

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self):
        api_key = os.getenv("API_FOOTBALL_KEY")  # ✅ Corrigido: era API_SPORTS_KEY
        if not api_key:
            raise ValueError("API_FOOTBALL_KEY não configurada")
        self.client = APIClient(api_key)

    def get_valid_season(self, league_id: int) -> int:
        this_year = datetime.now().year
        return this_year - 1

    def run_daily_analysis(self, leagues=None):
        if not leagues:
            leagues = []

        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"📅 Executando análise para a data: {today}")
        logger.info(f"🔢 Total de ligas para consultar: {len(leagues)}")

        found_any = False

        for league_id in leagues:
            season = self.get_valid_season(league_id)

            logger.info(f"🔎 Buscando jogos da liga {league_id} | season {season}...")

            fixtures = self.client.get_fixtures(
                date=today,
                league_id=league_id,
                season=season
            )

            if not fixtures:
                logger.info(f"⚠️ Nenhum jogo encontrado para liga {league_id}.")
                continue

            found_any = True
            logger.info(f"✅ {len(fixtures)} jogos encontrados para liga {league_id}.")

        if not found_any:
            logger.info("⚠️ Nenhuma liga retornou jogos hoje.")
