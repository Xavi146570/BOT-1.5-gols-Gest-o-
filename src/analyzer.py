# src/analyzer.py
import logging
from datetime import datetime
from src.api_client import APIClient

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self):
        # Usa a API key correta do ambiente
        api_key = os.getenv("API_SPORTS_KEY")
        self.client = APIClient(api_key)

    def get_valid_season(self, league_id: int) -> int:
        """
        A API-Sports geralmente tem season última = ano-1.
        Ex: em 2025, season válida = 2024.
        """
        this_year = datetime.now().year
        return this_year - 1  # mais seguro para todas as ligas

    def run_daily_analysis(self, leagues=None):
        if leagues is None:
            leagues = [795]  # default

        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"📅 Executando análise para a data: {today}")

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

            # Aqui adicionas o processamento real
            # ...

        if not found_any:
            logger.info("⚠️ Nenhum jogo encontrado para nenhuma liga hoje.")
