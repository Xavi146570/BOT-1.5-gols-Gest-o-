import logging
from datetime import datetime
from src.api_client import APIClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Analyzer:

    # TODAS AS LIGAS FORÇADAS AQUI
    LEAGUES = [
        39, 140, 61, 78, 135, 94, 88, 203, 179, 144,
        141, 40, 262, 301, 235, 253, 556, 566, 569, 795
    ]

    def __init__(self):
        self.client = APIClient()

    def run_daily_analysis(self, leagues=None):

        # GARANTE SEMPRE A LISTA COMPLETA
        if not leagues:
            leagues = self.LEAGUES

        date = datetime.now().strftime("%Y-%m-%d")
        season = datetime.now().year - 1  # API exige season anterior

        logger.info(f"📅 Executando análise para {date} | season={season}")
        logger.info(f"🔢 Total de ligas a consultar: {len(leagues)}")

        found_any = False

        for league in leagues:
            logger.info(f"🔎 Buscando jogos da liga {league}...")
            fixtures = self.client.get_fixtures(date, league, season)

            if not fixtures:
                logger.info(f"⚠️ Nenhum jogo encontrado para liga {league}.")
                continue

            found_any = True
            logger.info(f"✅ {len(fixtures)} jogos encontrados na liga {league}")

        if not found_any:
            logger.info("⚠️ Nenhuma das ligas retornou jogos hoje.")
