# src/analyzer.py
import os
import logging
from datetime import datetime
from src.api_client import APIClient
from src.telegram_notifier import TelegramNotifier
from src.value_detector import ValueDetector
from src.data_collector import DataCollector
from src.probability_calculator import calculate_over_probability

logger = logging.getLogger("src.analyzer")

class Analyzer:
    def __init__(self):
        api_key = os.getenv("API_FOOTBALL_KEY")
        self.client = APIClient(api_key)
        self.collector = DataCollector(self.client)
        self.detector = ValueDetector(required_ev=0.05)
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.notifier = TelegramNotifier(token, chat_id) if os.getenv("TELEGRAM_ENABLED") == "true" else None

    def run_daily_analysis(self, leagues=None):
        today = datetime.now().strftime("%Y-%m-%d")
        all_fixtures = []
        opportunities = []

        for league_id in leagues:
            fixtures = self.client.get_fixtures(date=today, league_id=league_id, season=2025)
            for f in fixtures:
                all_fixtures.append(f)
                h_id, a_id = f['teams']['home']['id'], f['teams']['away']['id']
                
                # 1. Coleta dados REAIS
                h_stats = self.collector.collect_team_data(h_id, league_id, 2025)
                a_stats = self.collector.collect_team_data(a_id, league_id, 2025)
                h2h = self.collector.collect_h2h_data(h_id, a_id)
                
                # 2. Calcula Probabilidade REAL (Poisson)
                prob, conf = calculate_over_probability(h_stats, a_stats, h2h, 1.5)
                
                # 3. Define Odd (Aqui idealmente buscaria da API, mas usamos 1.45 como base conservadora)
                market_odds = 1.45 
                
                analysis = self.detector.detect_value(prob, market_odds)

                if analysis['is_value'] and prob > 0.65: # Filtro de segurança
                    opp = {
                        'home_team': f['teams']['home']['name'],
                        'away_team': f['teams']['away']['name'],
                        'league': f['league']['name'],
                        'match_date': f['fixture']['date'],
                        'our_probability': prob,
                        'over_1_5_odds': market_odds,
                        'expected_value': analysis['expected_value'],
                        'recommended_stake': analysis['suggested_stake'] * 100,
                        'bet_quality': 'EXCELENTE' if prob > 0.8 else 'BOA',
                        'risk_level': 'BAIXO' if prob > 0.8 else 'MÉDIO',
                        'confidence': conf * 100,
                        'edge': analysis['expected_value']
                    }
                    opportunities.append(opp)
                    if self.notifier: self.notifier.notify_opportunity(opp)

        if self.notifier: self.notifier.notify_daily_summary(opportunities, len(all_fixtures))
