# src/api_client.py
import time
import logging
import requests

logger = logging.getLogger("src.api_client")
logger.setLevel(logging.INFO)

class APIClient:
    BASE_URL = "https://v3.football.api-sports.io"  # ✅ URL correto para API-Sports

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "x-apisports-key": api_key  # ✅ Header correto
        })
        logger.info("Conectado ao cliente da API de Futebol e cabeçalho de autenticação configurado.")

    def safe_request(self, endpoint, params, retries=5):
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(retries):
            response = self.session.get(url, params=params)

            try:
                data = response.json()
            except:
                logger.error("❌ Resposta inválida da API.")
                return None

            # Erro de rate limit
            if "errors" in data and data["errors"]:
                if "rateLimit" in str(data["errors"]):
                    logger.error("⚠️ Rate limit atingido! Esperando 2s...")
                    time.sleep(2)
                    continue

            return data

        logger.error("❌ Falhou após múltiplas tentativas.")
        return None

    def get_fixtures(self, date: str, league_id: int, season: int):
        logger.info(f"Buscando fixtures para {date} | league={league_id} | season={season}")

        params = {
            "date": date,
            "league": league_id,
            "season": season
        }

        data = self.safe_request("fixtures", params)
        time.sleep(0.8)

        if not data or "response" not in data:
            return []

        return data["response"]
