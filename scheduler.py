"""
Scheduler - Sistema de Multi-Market Value Detection (Over 0.5 e Over 1.5 Gols)
Agora calcula e notifica a "Odd Justa" mesmo quando o EV é negativo.
"""

import logging
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Union 
import schedule
import threading

# Importações dos Módulos do Projeto (Classes Mocked ou Reais)
from config.settings import Settings
# Presume que APIClient fornece odds para 0.5 e 1.5
from src.api_client import APIClient 
from src.data_collector import DataCollector
from src.probability_calculator import ProbabilityCalculator 
from src.value_detector import ValueDetector
from src.database import Database
from src.telegram_notifier import TelegramNotifier

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Classes MOCK para garantir que o código seja runnable (Ajuste para suas classes reais)
class MockSettings:
    API_FOOTBALL_KEY = "YOUR_KEY"
    TARGET_LEAGUES = [39, 140, 135, 78, 61, 2, 3, 40, 94, 88]
    TELEGRAM_ENABLED = False
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None

class MockAPIClient:
    def __init__(self, key): pass
    def get_fixtures_by_date(self, date, league_id): return []
    def get_odds(self, fixture_id):
        return {'over_0_5_odds': 1.15, 'over_1_5_odds': 2.10}
    def collect_team_data(self, team_id, league_id, season): 
        # Simula dados insuficientes para forçar o log antigo
        return {} 
    def collect_h2h_data(self, team1_id, team2_id): return {}

class MockDataCollector:
    def __init__(self, client): self.client = client
    def collect_team_data(self, team_id, league_id, season): 
        return {'goals_for_avg': 1.5, 'over_1_5_rate': 0.8, 'offensive_score': 0.7}
    def collect_h2h_data(self, team1_id, team2_id): 
        return {'over_1_5_rate': 0.75}

class MockDatabase:
    def save_opportunity(self, opp): logger.info(f"💾 Salvando oportunidade: {opp['home_team']} vs {opp['away_team']} ({opp['market']})")
    def clear_old_data(self, days): pass

class MockTelegramNotifier:
    def __init__(self, bot_token, chat_id): pass
    def notify_analysis_start(self, count): pass
    def notify_opportunity(self, opp): 
        # Notificação de Valor
        logger.info(f"📢 NOTIFICAÇÃO: Valor ENCONTRADO em {opp['home_team']} vs {opp['away_team']} ({opp['market']})")
    def notify_suggestion(self, opp):
        # Notificação de Sugestão
        logger.info(f"💡 SUGESTÃO: Odd Justa {opp['fair_odd']:.2f} (Mercado: {opp['market_odds']:.2f})")
    def notify_daily_summary(self, opps, total): pass
    def notify_error(self, error): pass

# Substitui as classes reais para que o código seja runnable
if not hasattr(globals().get('Settings', None), 'API_FOOTBALL_KEY'):
    Settings = MockSettings
if not hasattr(globals().get('APIClient', None), 'get_fixtures_by_date'):
    APIClient = MockAPIClient
if not hasattr(globals().get('DataCollector', None), 'collect_team_data'):
    DataCollector = MockDataCollector
if not hasattr(globals().get('Database', None), 'save_opportunity'):
    Database = MockDatabase
if not hasattr(globals().get('TelegramNotifier', None), 'notify_opportunity'):
    TelegramNotifier = MockTelegramNotifier
# --------------------------------------------------------------------------------

class Scheduler:
    # ... (Restante do __init__ e self_ping permanece igual)
    def __init__(self):
        try:
            self.settings = Settings()
            self.api_client = APIClient(self.settings.API_FOOTBALL_KEY)
            self.data_collector = DataCollector(self.api_client) 
            self.probability_calculator = ProbabilityCalculator()
            self.value_detector = ValueDetector()
            self.db = Database()
            
            # Inicializa Telegram (se configurado)
            self.telegram = None
            if self.settings.TELEGRAM_ENABLED:
                if self.settings.TELEGRAM_BOT_TOKEN and self.settings.TELEGRAM_CHAT_ID:
                    self.telegram = TelegramNotifier(
                        bot_token=self.settings.TELEGRAM_BOT_TOKEN,
                        chat_id=self.settings.TELEGRAM_CHAT_ID
                    )
                else:
                    logger.warning("⚠️ Telegram habilitado mas credenciais faltando")
            
            # URL para self-ping (detecta automaticamente no Render)
            import os
            render_service = os.getenv('RENDER_SERVICE_NAME', 'football-value-detector-1-5-gols')
            self.self_ping_url = f"https://{render_service}.onrender.com/health"
            
            logger.info("✅ Scheduler inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Scheduler: {e}")
            raise

    # Métodos self_ping e start_self_ping_thread omitidos por brevidade

    def analyze_daily_matches(self):
        # ... (Mantido igual, mas usando MOCK fixtures para o exemplo)
        logger.info("="*60)
        logger.info("🚀 INICIANDO ANÁLISE DIÁRIA")
        logger.info("="*60)
        
        start_time = time.time()
        
        try:
            # 1. Busca jogos do dia - FORÇANDO UTC
            now_utc = datetime.now(timezone.utc)
            today = now_utc.date().isoformat()
            
            # MOCK: Para simular os jogos que o seu log encontrou
            fixtures = [
                {'fixture': {'id': 1386749, 'date': f"{today}T20:45:00+00:00"}, 
                 'teams': {'home': {'name': 'Swansea', 'id': 100}, 'away': {'name': 'Derby', 'id': 101}}, 
                 'league': {'name': 'Championship', 'id': 40, 'season': 2024}},
                {'fixture': {'id': 1386750, 'date': f"{today}T20:45:00+00:00"}, 
                 'teams': {'home': {'name': 'Southampton', 'id': 102}, 'away': {'name': 'Leicester', 'id': 103}}, 
                 'league': {'name': 'Championship', 'id': 40, 'season': 2024}}
            ]
            
            if not fixtures:
                logger.warning("⚠️ Nenhum jogo encontrado para hoje")
                return
            
            logger.info(f"✅ {len(fixtures)} jogos encontrados")
            
            if self.telegram:
                self.telegram.notify_analysis_start(len(fixtures))
            
            opportunities = []
            for i, fixture in enumerate(fixtures, 1):
                logger.info(f"\n--- Analisando jogo {i}/{len(fixtures)} ---")
                
                new_opportunities = self._analyze_fixture(fixture)
                
                for opportunity in new_opportunities:
                    opportunities.append(opportunity)
                    self.db.save_opportunity(opportunity)
                    
                    if self.telegram:
                        # Oportunidade Pura é notificada aqui
                        self.telegram.notify_opportunity(opportunity) 
                
                time.sleep(2)
            
            if opportunities:
                ranked = self.value_detector.rank_opportunities(opportunities)
                self._display_results(ranked)
            else:
                logger.warning("⚠️ Nenhuma oportunidade com valor detectada")
            
            elapsed = time.time() - start_time
            logger.info("\n" + "="*60)
            logger.info(f"✅ ANÁLISE CONCLUÍDA")
            logger.info(f"⏱️ Tempo total: {elapsed:.1f}s")
            logger.info(f"🎯 Oportunidades encontradas: {len(opportunities)}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Erro na análise diária: {e}")
            
    
    def _get_today_fixtures(self, today: str) -> List[Dict]:
        all_fixtures = []
        # ... (Lógica de busca omitida por brevidade)
        return all_fixtures # Retorna lista real de fixtures na sua implementação

    def _analyze_fixture(self, fixture: Dict) -> List[Dict[str, Any]]:
        """
        Analisa um jogo completo, verificando múltiplos mercados.
        
        Returns:
            List[Dict]: Lista de oportunidades encontradas.
        """
        opportunities_list = []
        
        try:
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            fixture_id = fixture['fixture']['id']
            league_name = fixture['league']['name']
            
            logger.info(f"⚽ {home_team} vs {away_team}")
            logger.info(f"   Liga: {league_name} | ID: {fixture_id}")
            
            # 1. Coleta dados (Usando MOCKs para simular dados do seu LOG)
            logger.info("   📊 Coletando dados dos times...")
            home_data = self.data_collector.collect_team_data(fixture['teams']['home']['id'], fixture['league']['id'], fixture['league']['season'])
            away_data = self.data_collector.collect_team_data(fixture['teams']['away']['id'], fixture['league']['id'], fixture['league']['season'])
            
            if not home_data or not away_data:
                logger.warning("   ⚠️ Dados insuficientes dos times. (Se este erro persistir, verifique a API)")
                return []
            
            logger.info("   🤝 Coletando dados H2H...")
            h2h_data = self.data_collector.collect_h2h_data(fixture['teams']['home']['id'], fixture['teams']['away']['id'])
            
            # MOCK de Indicadores (A sua lógica real deve gerar isto)
            probability_input_data = {
                'expected_goals_lambda': 1.5,
                'home_over_1_5_rate': 0.5, 
                'away_over_1_5_rate': 0.5,
                'recent_over_1_5_rate': 0.5,
                'h2h_over_1_5_rate': 0.5,
                'home_offensive_score': 0.5,
                'away_offensive_score': 0.5,
                'combined_motivation_score': 0.5,
            }
            
            # 2. Busca odds para ambos os mercados
            logger.info("   💰 Buscando odds...")
            odds_data = self.api_client.get_odds(fixture_id)
            
            # Definir a lista de mercados a analisar
            markets_to_analyze = {}
            if odds_data.get('over_0_5_odds'):
                 markets_to_analyze['Over 0.5'] = odds_data['over_0_5_odds']
            if odds_data.get('over_1_5_odds'):
                 markets_to_analyze['Over 1.5'] = odds_data['over_1_5_odds']

            # Se nenhum mercado tiver odds, sai
            if not markets_to_analyze:
                 logger.warning("   ⚠️ Nenhuma Odd Over/Under encontrada na API.")
                 return []
            
            logger.info("   🧮 Calculando probabilidades...")

            # 3. Itera sobre cada mercado
            for market_name, market_odds in markets_to_analyze.items():
                
                # Calcula a probabilidade específica para o mercado
                our_probability = self.probability_calculator.calculate_probability(
                    data=probability_input_data,
                    market=market_name
                )
                
                confidence_score = (our_probability * 0.9 + 0.1)
                
                logger.info(f"   📈 Probabilidade {market_name}: {our_probability:.1%}")
                logger.info(f"   🎯 Confiança: {confidence_score*100:.0f}%")
                logger.info(f"   💵 Odds {market_name}: {market_odds:.2f}")
                
                # 4. Detecta valor (Este método retorna a fair_odd SEMPRE)
                detection_result = self.value_detector.detect_value(our_probability, market_odds)
                
                # Odd Justa calculada
                fair_odd = detection_result['fair_odd']
                
                if detection_result['is_value']:
                    # =========================================================
                    # NOTIFICAÇÃO DE VALOR (Aposta com EV Positivo)
                    # =========================================================
                    logger.info(f"   ✅ VALOR DETECTADO em {market_name}!")
                    logger.info(f"   💵 EV: {detection_result['expected_value']:.2%}")
                    logger.info(f"   📊 Kelly Pura (F): {detection_result['pure_kelly_fraction']:.2f}%")

                    opportunity = {
                        'fixture_id': fixture_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': league_name,
                        'match_date': fixture['fixture']['date'],
                        'market': market_name, 
                        'our_probability': our_probability,
                        'market_odds': market_odds,
                        'expected_value': detection_result['expected_value'],
                        'recommended_stake': detection_result['suggested_stake'] * 100, 
                        'pure_kelly_fraction': detection_result['pure_kelly_fraction'] * 100, 
                        'bet_quality': 'High',
                        'risk_level': 'Medium',
                        'confidence': confidence_score * 100
                    }
                    opportunities_list.append(opportunity)

                else:
                    # =========================================================
                    # MODO SUGESTÃO (EV Negativo, mas informa Odd Justa)
                    # =========================================================
                    # A Odd do mercado é MUITO inferior à Odd Justa?
                    # Usamos uma margem de segurança (ex: 20% de diferença) para notificar
                    
                    if fair_odd > 1.0 and market_odds < fair_odd * 0.8:
                         
                        logger.info(f"   💡 SUGESTÃO: Odd Justa {market_name}: {fair_odd:.2f}. EV Negativo.")

                        # Notifica o Telegram com a sugestão de valor (Odd Justa)
                        if self.telegram and hasattr(self.telegram, 'notify_suggestion'):
                             suggestion_data = {
                                'home_team': home_team, 
                                'away_team': away_team, 
                                'market': market_name, 
                                'market_odds': market_odds, 
                                'fair_odd': fair_odd
                             }
                             self.telegram.notify_suggestion(suggestion_data)
                    else:
                        logger.info(f"   ⚠️ Sem valor detectado em {market_name} (EV: {detection_result['expected_value']:.2%}). Odd Justa próxima da Odd de Mercado.")

            return opportunities_list
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao analisar jogo: {e}")
            return []
    
    # Métodos _display_results, update_results, cleanup_old_data, run, main omitidos por brevidade
    def _display_results(self, opportunities: List[Dict]):
        """Exibe resumo das oportunidades encontradas"""
        logger.info("\n" + "="*60)
        logger.info("🎯 OPORTUNIDADES DETECTADAS")
        logger.info("="*60)
        
        for i, opp in enumerate(opportunities, 1):
            logger.info(f"\n{i}. {opp['home_team']} vs {opp['away_team']} | Mercado: {opp['market']}")
            logger.info(f"   Liga: {opp['league']}")
            logger.info(f"   ---")
            logger.info(f"   Probabilidade: {opp['our_probability']:.1%}")
            logger.info(f"   Odds Mercado: {opp['market_odds']:.2f}")
            logger.info(f"   Expected Value: {opp['expected_value']:.2%}")
            logger.info(f"   Kelly Pura (F): {opp['pure_kelly_fraction']:.2f}%") 

    def update_results(self): pass
    def cleanup_old_data(self): pass
    def run(self): pass
    
def main():
    try:
        scheduler = Scheduler()
        logger.info("🚀 Executando análise inicial...")
        scheduler.analyze_daily_matches()
        scheduler.run()
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
