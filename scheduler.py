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
        """
        MOCK: Simula odds
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
    # A assinatura inclui 'market'
    def calculate_probability(self, data: Dict[str, Any], market: str) -> float:
        """Simula probabilidades para diferentes mercados e jogos MOCK."""
        
        # Jogo 1386749: Swansea vs Derby (Over 1.5: 55%, Odd 2.05 -> Valor. No mock data, vamos fazer 88.8% para EV alto)
        if data['fixture_id'] == 1386749: 
            if market == 'Over 1.5': return 0.888 # 88.8% (EV: 81.94% com odd 2.05)
            if market == 'Over 0.5': return 0.985 # 98.5% (EV: 3.43% com odd 1.05)
            
        # Jogo 1386750: Southampton vs Leicester (Over 1.5: 88.8%, Odd 1.25 -> EV 10.94%)
        if data['fixture_id'] == 1386750: 
            if market == 'Over 1.5': return 0.888 
            if market == 'Over 0.5': return 0.985
            
        return 0.70 # Default

class MockValueDetector:
    """Mock da classe ValueDetector, corrigida para aceitar 2 argumentos posicionais e adicionar rank_opportunities."""
    def detect_value(self, probability: float, market_odds: float) -> Dict[str, Any]:
        fair_odd = 1 / probability
        expected_value = (probability * market_odds) - 1
        is_value = expected_value > 0.05 # Simula o requisito de EV
        
        if market_odds > 1.0:
            pure_kelly_fraction = expected_value / (market_odds - 1)
        else:
            pure_kelly_fraction = 0.0

        suggested_stake = min(0.1, max(0.0, pure_kelly_fraction))

        return {
            'is_value': is_value,
            'expected_value': expected_value,
            'fair_odd': fair_odd,
            'pure_kelly_fraction': pure_kelly_fraction,
            'suggested_stake': suggested_stake 
        }

    def rank_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mock: Classifica por expected_value decrescente."""
        if not opportunities:
            return []
        
        # Classifica por EV (decrescente) e depois por Confiança (decrescente)
        return sorted(
            opportunities, 
            key=lambda x: (x['expected_value'] * -1, x['confidence'] * -1)
        )

class MockDatabase:
    # Oportunidades agora devem usar 'match_id' e ter 'implied_probability'
    def save_opportunity(self, opp): 
        if 'implied_probability' not in opp:
             logger.error("❌ Erro ao salvar oportunidade: 'implied_probability'")
             return
        logger.info(f"💾 Salvando oportunidade: {opp.get('home_team')} vs {opp.get('away_team')} ({opp.get('market')})")

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
# Uso do MockValueDetector corrigido
if not hasattr(globals().get('ValueDetector', None), 'detect_value'):
    ValueDetector = MockValueDetector
if not hasattr(globals().get('Database', None), 'save_opportunity'):
    Database = MockDatabase
if not hasattr(globals().get('TelegramNotifier', None), 'notify_opportunity'):
    TelegramNotifier = MockTelegramNotifier
# --------------------------------------------------------------------------------

class Scheduler:
    
    def __init__(self):
        try:
            self.settings = Settings()
            self.api_client = APIClient(self.settings.API_FOOTBALL_KEY)
            self.data_collector = DataCollector(self.api_client) 
            self.probability_calculator = ProbabilityCalculator()
            # Esta classe agora inclui rank_opportunities
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
                    # A chamada para save_opportunity espera 'implied_probability'
                    self.db.save_opportunity(opportunity)
                    
                    if self.telegram:
                        # Oportunidade Pura é notificada aqui
                        self.telegram.notify_opportunity(opportunity) 
                
                time.sleep(2)
            
            if opportunities:
                # O método rank_opportunities agora existe
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
            # Esta linha será o último ponto de erro se houver problemas na lógica acima
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
            home_data = self.data_collector.collect_team_data(fixture['teams']['home']['id'], fixture['league']['id'], fixture['league']['season'])
            away_data = self.data_collector.collect_team_data(fixture['teams']['away']['id'], fixture['league']['id'], fixture['league']['season'])
            
            if not home_data or not away_data:
                logger.warning("   ⚠️ Dados insuficientes dos times. (Se este erro persistir, verifique a API)")
                return []
            
            logger.info("   🤝 Coletando dados H2H...")
            h2h_data = self.data_collector.collect_h2h_data(fixture['teams']['home']['id'], fixture['teams']['away']['id'])
            
            probability_input_data = {
                'fixture_id': fixture_id,
                'expected_goals_lambda': home_data.get('goals_for_avg', 1.5) + away_data.get('goals_for_avg', 1.5) / 2,
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
            
            markets_to_analyze = {}
            if odds_data.get('over_0_5_odds'):
                 markets_to_analyze['Over 0.5'] = odds_data['over_0_5_odds']
            if odds_data.get('over_1_5_odds'):
                 markets_to_analyze['Over 1.5'] = odds_data['over_1_5_odds']

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
                
                # 4. Detecta valor
                detection_result = self.value_detector.detect_value(our_probability, market_odds)
                fair_odd = detection_result['fair_odd']
                
                # NOVO: Calcula a probabilidade implícita do mercado (1 / Odds)
                implied_probability = 1 / market_odds
                
                if detection_result['is_value']:
                    # =========================================================
                    # NOTIFICAÇÃO DE VALOR (Aposta com EV Positivo)
                    # =========================================================
                    logger.info(f"   ✅ VALOR DETECTADO em {market_name}!")
                    logger.info(f"   💵 EV: {detection_result['expected_value']:.2%}")
                    logger.info(f"   📊 Kelly Pura (F): {detection_result['pure_kelly_fraction']:.2f}%")

                    opportunity = {
                        # Corrigido na iteração anterior
                        'match_id': fixture_id, 
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': league_name,
                        'match_date': fixture['fixture']['date'],
                        'market': market_name, 
                        'our_probability': our_probability,
                        'market_odds': market_odds,
                        # NOVO CAMPO REQUERIDO PELO BANCO DE DADOS
                        'implied_probability': implied_probability, 
                        'expected_value': detection_result['expected_value'],
                        'recommended_stake': detection_result['suggested_stake'] * 100, 
                        'pure_kelly_fraction': detection_result['pure_kelly_fraction'] * 100, 
                        'bet_quality': 'High',
                        'risk_level': 'Medium',
                        'confidence': confidence_score * 100 # Adicionamos o score de confiança aqui
                    }
                    opportunities_list.append(opportunity)

                else:
                    # =========================================================
                    # MODO SUGESTÃO (EV Negativo, mas informa Odd Justa)
                    # =========================================================
                    if fair_odd >= 1.30 and detection_result['expected_value'] < 0:
                         
                        logger.info(f"   💡 SUGESTÃO: Odd Justa {market_name}: {fair_odd:.2f}. EV Negativo.")

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
    
    # ... (Restante da classe Scheduler, incluindo _display_results, run, main)
    def _display_results(self, opportunities: List[Dict]):
        """Exibe resumo das oportunidades encontradas (agora rankeadas)"""
        logger.info("\n" + "="*60)
        logger.info("🎯 OPORTUNIDADES DETECTADAS (RANKED)")
        logger.info("="*60)
        
        for i, opp in enumerate(opportunities, 1):
            logger.info(f"\n{i}. {opp['home_team']} vs {opp['away_team']} | Mercado: {opp['market']}")
            logger.info(f"   Liga: {opp['league']}")
            logger.info(f"   ---")
            logger.info(f"   Probabilidade: {opp['our_probability']:.1%}")
            logger.info(f"   Odds Mercado: {opp['market_odds']:.2f}")
            logger.info(f"   Expected Value: {opp['expected_value']:.2%}") # Alterado para %
            logger.info(f"   Confiança: {opp['confidence']:.0f}%")
            logger.info(f"   Kelly Pura (F): {opp['pure_kelly_fraction']:.2f}%") 

    def update_results(self): pass
    def cleanup_old_data(self): pass
    def run(self): pass
    
def main():
    try:
        scheduler = Scheduler()
        logger.info("🚀 Executando análise inicial...")
        scheduler.analyze_daily_matches()
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
