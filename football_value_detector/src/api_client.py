import os
import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class APIClient:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")

        if not self.api_key:
            logger.warning("⚠️ API key não encontrada. Defina API_FOOTBALL_KEY.")

        self.session = requests.Session()
        self.session.headers.update({
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "v3.football.api-sports.io"
        })

    def get_fixtures(self, date: str, league: int, season: int):
        url = f"{self.BASE_URL}/fixtures"
        params = {"date": date, "league": league, "season": season}

        try:
            logger.info(f"Buscando fixtures para {date} | league={league} | season={season}")
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json().get("response", [])
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ERROR league={league}: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar fixtures league={league}: {e}")
            return []
