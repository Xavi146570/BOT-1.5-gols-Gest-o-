# src/api_client.py
import time
import logging
import requests

logger = logging.getLogger("src.api_client")
logger.setLevel(logging.INFO)

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

    # ---------------------
    # Rate Limit SAFE CALL
    # ---------------------
    def safe_request(self, endpoint, params, retries=5):
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(retries):
            response = self.session.get(url, params=params)
            data = response.json()

            # Se der rate limit
            if "errors" in data and data["errors"]:
                if "rateLimit" in data["errors"]:
                    logger.error(f"⚠️ Rate limit atingido! Esperando 2s antes de tentar novamente...")
                    time.sleep(2)
                    continue  # tenta novamente

            # Qualquer resposta válida
            return data

        logger.error("❌ Falhou após múltiplas tentativas.")
        return None

    # ---------------------
    # FIXTURES
    # ---------------------
    def get_fixtures(self, date: str, league_id: int, season: int):
        logger.info(f"Buscando fixtures para {date} | league={league_id} | season={season}")

        params = {
            "date": date,
            "league": league_id,
            "season": season
        }

        data = self.safe_request("fixtures", params)

        # Delay entre chamadas para evitar RATE LIMIT
        time.sleep(0.8)

        if not data or "response" not in data:
            return []

        return data["response"]
