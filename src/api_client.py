# src/api_client.py
import logging
import requests
from datetime import datetime

logger = logging.getLogger("src.api_client")
logger.setLevel(logging.INFO)

TOP_20_LEAGUES = [
    39, 140, 61, 78, 135, 94, 88, 203, 179, 144,
    141, 40, 262, 301, 235, 253, 556, 566, 569, 795
]

class APIClient:
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        })
        logger.info("Conectado ao cliente da API de Futebol e cabeçalho de autenticação configurado.")

    # ------------------------------
    # FIXTURES (CORRIGIDO COM season=)
    # ------------------------------
    def get_fixtures(self, date: str, league_id: int, season: int):
        url = f"{self.BASE_URL}/fixtures"
        params = {
            "date": date,
            "league": league_id,
            "season": season
        }

        logger.info(f"Buscando fixtures para {date} | league={league_id} | season={season}")

        try:
            response = self.session.get(url, params=params, timeout=20)
            data = response.json()

            if "errors" in data and data["errors"]:
                logger.error(f"❌ Erros na resposta da API: {data['errors']}")
                return None

            return data.get("response", [])

        except Exception as e:
            logger.error(f"Erro ao buscar fixtures: {e}")
            return None

    # ------------------------------
    # ODDS
    # ------------------------------
    def get_odds(self, fixture_id: int):
        url = f"{self.BASE_URL}/odds"
        params = {"fixture": fixture_id}

        try:
            response = self.session.get(url, params=params, timeout=20)
            data = response.json()

            if "errors" in data and data["errors"]:
                logger.warning(f"⚠️ Erro ao buscar odds para {fixture_id}: {data['errors']}")
                return None

            return data.get("response", [])

        except Exception as e:
            logger.error(f"Erro ao buscar odds: {e}")
            return None
