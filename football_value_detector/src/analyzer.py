import logging
from datetime import datetime
from src.api_client import APIClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self):
        self.client = APIClient()

        self.leagues = [
            39, 140, 61, 78, 135, 94, 88, 203, 179, 144,
            141, 40, 262, 301, 235, 253, 556, 566, 569, 795
        ]

    def run_daily_analysis(self, leagues=None):
        if leagues is None:
            leagues = self.leagues

        date = datetime.now().strftime("%Y-%m-%d")
        season = datetime.now().year - 1

        logger.info(f"📅 Executando análise para {date} | season {season}")

        found_any = False

        for league in leagues:
            fixtures = self.client.get_fixtures(date, league, season)

            if not fixtures:
                logger.info(f"⚠️ Nenhum jogo encontrado para liga {league}.")
                continue

            found_any = True
            logger.info(f"✅ {len(fixtures)} jogos encontrados para liga {league}")

        if not found_any:
            logger.info("⚠️ Nenhuma liga retornou jogos hoje.")
