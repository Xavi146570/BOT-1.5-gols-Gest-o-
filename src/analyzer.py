# src/analyzer.py
import os
import logging
from datetime import datetime
from src.api_client import APIClient

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)


class Analyzer:

    # LISTA DEFINITIVA DAS 20 LIGAS
    LEAGUES = [
        39, 140, 61, 78, 135,
        94, 88, 203, 179, 144,
        141, 40, 262, 301, 235,
        253, 556, 566, 569, 795
    ]

    def __init__(self):
        api_key = os.getenv("API_SPORTS_KEY")  # pega chave certa
        self.client = APIClient(api_key)

    def get_valid_season(self, league_id: int) -> int:
        this_year = datetime.now().year
        return this_year - 1

    # >>>>> AQUI GARANTO QUE SEMPRE USA AS 20 LIGAS, SEM EXCEÇÃO <<<<<
    def run_daily_analysis(self, leagues=None):

        # ignorar parâmetro, sempre usar a lista completa
        leagues = self.LEAGUES

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
