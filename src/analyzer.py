# src/analyzer.py
import os
import logging
from datetime import datetime
from src.api_client import APIClient

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self):
        api_key = os.getenv("API_FOOTBALL_KEY")
        if not api_key:
            raise ValueError("API_FOOTBALL_KEY não configurada")
        self.client = APIClient(api_key)

    def get_valid_season(self, league_id: int) -> int:
        # Mantemos 2025 pois os logs mostraram que está a funcionar
        return 2025

    def run_daily_analysis(self, leagues=None):
        if not leagues:
            leagues = []

        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"📅 Executando análise para a data: {today}")
        
        found_any = False

        for league_id in leagues:
            season = self.get_valid_season(league_id)
            logger.info(f"🔎 Buscando jogos da liga {league_id}...")

            fixtures = self.client.get_fixtures(
                date=today,
                league_id=league_id,
                season=season
            )

            if not fixtures:
                continue

            found_any = True
            logger.info(f"✅ {len(fixtures)} jogos encontrados para liga {league_id}:")
            
            # 🔥 NOVO: Listar os jogos encontrados nos logs
            for f in fixtures:
                home = f['teams']['home']['name']
                away = f['teams']['away']['name']
                status = f['fixture']['status']['long']
                hora = f['fixture']['date']
                logger.info(f"   ⚽ {home} vs {away} | Status: {status} | Hora: {hora}")
                
                # TODO: Aqui deve entrar a chamada para o Notificador
                # self.notifier.send_message(...)

        if not found_any:
            logger.info("⚠️ Nenhuma liga retornou jogos hoje.")
