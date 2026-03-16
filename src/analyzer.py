# src/analyzer.py
import os
import logging
from datetime import datetime
from src.api_client import APIClient
from src.notifier import TelegramNotifier  # Ajuste o caminho se necessário
from football_value_detector.analyzer import ValueDetector

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self):
        # Configurações de API
        api_key = os.getenv("API_FOOTBALL_KEY")
        if not api_key:
            raise ValueError("API_FOOTBALL_KEY não configurada")
        self.client = APIClient(api_key)

        # Configurações de Telegram
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
        
        self.notifier = None
        if enabled and token and chat_id:
            self.notifier = TelegramNotifier(token, chat_id)
            logger.info("✅ Notificador Telegram inicializado.")
        else:
            logger.warning("⚠️ Telegram desativado ou variáveis ausentes.")

        # Detector de Valor
        self.detector = ValueDetector(required_ev=0.05)

    def get_valid_season(self, league_id: int) -> int:
        return 2025

    def run_daily_analysis(self, leagues=None):
        if not leagues:
            leagues = []

        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"📅 Iniciando análise para: {today}")
        
        all_fixtures = []
        opportunities = []

        for league_id in leagues:
            season = self.get_valid_season(league_id)
            fixtures = self.client.get_fixtures(date=today, league_id=league_id, season=season)

            if not fixtures:
                continue

            for f in fixtures:
                all_fixtures.append(f)
                home = f['teams']['home']['name']
                away = f['teams']['away']['name']
                league_name = f['league']['name']
                
                # --- LÓGICA DE ANÁLISE ---
                # Simulando probabilidade de 75% para Over 1.5 (ajuste conforme seu modelo real)
                prob = 0.75 
                odds_mercado = 1.50 # Simulando uma odd média de mercado
                
                analysis = self.detector.detect_value(prob, odds_mercado)

                if analysis['is_value']:
                    opp = {
                        'home_team': home,
                        'away_team': away,
                        'league': league_name,
                        'match_date': f['fixture']['date'],
                        'our_probability': prob,
                        'over_1_5_odds': odds_mercado,
                        'expected_value': analysis['expected_value'],
                        'recommended_stake': analysis['suggested_stake'] * 100,
                        'bet_quality': 'BOA',
                        'risk_level': 'MÉDIO',
                        'confidence': prob * 100,
                        'edge': analysis['expected_value']
                    }
                    opportunities.append(opp)
                    
                    # Envia alerta individual
                    if self.notifier:
                        self.notifier.notify_opportunity(opp)
                        logger.info(f"🚀 Alerta enviado: {home} vs {away}")

        # Envia Resumo Diário
        if self.notifier:
            self.notifier.notify_daily_summary(opportunities, len(all_fixtures))
            logger.info("📊 Resumo diário enviado para o Telegram.")

        if not all_fixtures:
            logger.info("⚠️ Nenhum jogo encontrado hoje.")
