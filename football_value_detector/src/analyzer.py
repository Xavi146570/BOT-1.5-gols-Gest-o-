import os
import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self):
        self.api_url = "https://v3.football.api-sports.io/fixtures"
        self.api_key = os.getenv("API_FOOTBALL_KEY")  # variável correta
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "v3.football.api-sports.io"
        }

        # Lista padrão de ligas
        self.default_leagues = [
            39, 140, 61, 78, 135, 94, 88, 203, 179, 144,
            141, 40, 262, 301, 235, 253, 556, 566, 569, 795
        ]

    def run_daily_analysis(self, leagues=None):
        """Busca os jogos da data atual para as ligas especificadas e processa os dados."""

        # Se nenhuma liga for passada, usa todas as suas ligas
        if leagues is None:
            leagues = self.default_leagues

        today_str = datetime.now().strftime("%Y-%m-%d")
        season = datetime.now().year - 1  # API usa temporada iniciada no ano anterior

        logger.info(f"📅 Executando análise para a data: {today_str}")

        any_fixtures = False

        for league_id in leagues:
            try:
                logger.info(f"🔎 Buscando jogos da liga {league_id} | season {season}...")

                params = {
                    "date": today_str,
                    "league": league_id,
                    "season": season
                }

                # Chamada à API
                response = requests.get(self.api_url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                fixtures = data.get("response", [])

                if not fixtures:
                    logger.info(f"⚠️ Nenhum jogo encontrado para liga {league_id}.")
                    continue

                any_fixtures = True
                logger.info(f"✅ {len(fixtures)} jogos encontrados para a liga {league_id}.")

                # Aqui você pode processar/salvar os dados
                # Exemplo: salvar no DB, gerar análises, etc.

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTPError ao buscar fixtures (league={league_id}): {e}")

            except Exception as e:
                logger.error(f"Erro inesperado ao buscar fixtures da liga {league_id}: {e}")

        if not any_fixtures:
            logger.info("⚠️ Nenhum jogo encontrado para nenhuma liga hoje.")

# Execução manual
if __name__ == "__main__":
    analyzer = Analyzer()
    analyzer.run_daily_analysis()
