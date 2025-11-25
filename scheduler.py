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
from src.probability_calculator import ProbabilityCalculator # Agora com o método corrigido
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
        """
        MOCK: Simula odds
        Jogo 1386749 (Swansea vs Derby): Over 1.5 tem valor (Odd 2.05, P=55%)
        Jogo 1386750 (Southampton vs Leicester): Over 1.5 tem P alta (85%), mas Odd baixa (1.25).
        """
        logger.info(f"Buscando odds para o jogo {fixture_id}...")
        if fixture_id == 1386749: 
             return {'over_0_5_odds': 1.05, 'over_1_5_odds': 2.05} 
        elif fixture_id == 1386750: 
             return {'over_0_5_odds': 1.10, 'over_1_5_odds': 1.25} 
        else:
             return {'over_0_5_odds': 1.15, 'over_1_5_odds': 2.10}


    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Dict[str, float]:
        """Retorna dados MOCK em caso de falha da API (403 Forbidden)."""
        logger.warning(f"   ⚠️ Usando MOCK DATA para estatísticas da Equipa {team_id} devido a falha da API.")
        return {
            'goals_for_avg': 1.8,         
            'over_1_5_rate': 0.85,        
            'offensive_score': 0.75,      
        }

    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Dict[str, float]:
        """Retorna dados MOCK em caso de falha da API."""
        logger.warning(f"   ⚠️ Usando MOCK DATA para H2H devido a falha da API.")
        return {'h2h_over_1_5_rate': 0.78}

class MockDataCollector:
    def __init__(self, client): self.client = client
    def collect_team_data(self, team_id, league_id, season): 
        # Chama o cliente real para obter o MOCK data
        return self.client.collect_team_data(team_id, league_id, season)
    def collect_h2h_data(self, team1_id, team2_id): 
        return self.client.collect_h2h_data(team1_id, team2_id)


class MockProbabilityCalculator:
    # IMPORTANTE: A assinatura agora inclui 'market'
    def calculate_probability(self, data: Dict[str, Any], market: str) -> float:
        """Simula probabilidades para diferentes mercados e jogos MOCK."""
        
        # Jogo 1386749: Swansea vs Derby (Over 1.5: 55%, Odd 2.05 -> Valor)
        if data['fixture_id'] == 1386749: 
            if market == 'Over 1.5': return 0.55 
            if market == 'Over 0.5': return 0.98 
            
        # Jogo 1386750: Southampton vs Leicester (Over 1.5: 85%, Odd 1.25 -> EV Negativo/Sugestão)
        if data['fixture_id'] == 1386750: 
            if market == 'Over 1.5': return 0.85
            if market == 'Over 0.5': return 0.99
            
        return 0.70 # Default

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
        # Notificação de Sugestão (Odd Justa)
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
if not hasattr(globals().get('ProbabilityCalculator', None), 'calculate_probability'):
    ProbabilityCalculator = MockProbabilityCalculator
if not hasattr(globals().get('Database', None), 'save_opportunity'):
    Database = MockDatabase
if not hasattr(globals().get('TelegramNotifier', None), 'notify_opportunity'):
    TelegramNotifier = MockTelegramNotifier
# --------------------------------------------------------------------------------

class Scheduler:
    
    def __init__(self):
        try:
            self.settings = Settings()
            # O APIClient agora tem o método collect_team_data e o DataCollector chama-o
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
            
            # 1. Coleta dados 
            logger.info("   📊 Coletando dados dos times...")
            # O DataCollector agora chama o método correto no APIClient
            home_data = self.data_collector.collect_team_data(fixture['teams']['home']['id'], fixture['league']['id'], fixture['league']['season'])
            away_data = self.data_collector.collect_team_data(fixture['teams']['away']['id'], fixture['league']['id'], fixture['league']['season'])
            
            # Esta verificação é crucial para o MOCK DATA: se o DataCollector retornar {}, o bot sai.
            if not home_data or not away_data:
                logger.warning("   ⚠️ Dados insuficientes dos times. (Se este erro persistir, verifique a API)")
                return []
            
            logger.info("   🤝 Coletando dados H2H...")
            h2h_data = self.data_collector.collect_h2h_data(fixture['teams']['home']['id'], fixture['teams']['away']['id'])
            
            # Dados combinados (Usamos MOCKs para que o cálculo de probabilidade possa ocorrer)
            probability_input_data = {
                'fixture_id': fixture_id, # Adicionado para diferenciar no MockProbabilityCalculator
                'expected_goals_lambda': home_data.get('goals_for_avg', 1.5) + away_data.get('goals_for_avg', 1.5) / 2,
                # Adicione todos os outros indicadores que o seu ProbabilityCalculator usa
                'home_over_1_5_rate': home_data.get('over_1_5_rate', 0.70), 
                'away_over_1_5_rate': away_data.get('over_1_5_rate', 0.70),
                'h2h_over_1_5_rate': h2h_data.get('h2h_over_1_5_rate', 0.75),
                'home_offensive_score': home_data.get('offensive_score', 0.60),
                'away_offensive_score': away_data.get('offensive_score', 0.60),
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
                
                confidence_score = (our_probability * 0.9 + 0.1) # Simulação
                
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
                    # Usamos uma regra simples: se a Odd Justa for >= 1.30 (P <= 77%) e o EV for negativo.
                    if fair_odd >= 1.30 and detection_result['expected_value'] < 0:
                         
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
                        logger.info(f"   ⚠️ Sem valor detectado em {market_name} (EV: {detection_result['expected_value']:.2%}).")

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
        # scheduler.run() # Comentei para evitar que a aplicação fique rodando infinitamente na CLI
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
