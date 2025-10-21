"""
Scheduler - Sistema Over 1.5
Automação de análise diária de jogos e detecção de oportunidades
"""
from src.telegram_notifier import TelegramNotifier
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict
import schedule

from config.settings import Settings
from src.api_client import APIClient
from src.data_collector import DataCollector
from src.probability_calculator import ProbabilityCalculator
from src.value_detector import ValueDetector
from src.database import Database

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


class Scheduler:
    """Gerencia automação de análises diárias"""
    
    def __init__(self):
        """Inicializa componentes do sistema"""
        try:
            self.settings = Settings()
            self.api_client = APIClient(self.settings.API_FOOTBALL_KEY)
            self.data_collector = DataCollector(self.api_client)
            self.probability_calculator = ProbabilityCalculator()
            self.value_detector = ValueDetector()
            self.db = Database()
                        # Telegram
            if self.settings.TELEGRAM_ENABLED:
                self.telegram = TelegramNotifier(
                    bot_token=self.settings.TELEGRAM_BOT_TOKEN,
                    chat_id=self.settings.TELEGRAM_CHAT_ID
                )
                self.telegram.test_connection()
            else:
                self.telegram = None
                logger.warning("⚠️ Telegram desativado")

            
            logger.info("✅ Scheduler inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Scheduler: {e}")
            raise
    
    def analyze_daily_matches(self):
        """
        Análise completa dos jogos do dia
        Executa diariamente às 08:00
        """
        logger.info("="*60)
        logger.info("🚀 INICIANDO ANÁLISE DIÁRIA")
        logger.info("="*60)
                    # TODO: Implementar notificações Telegram no futuro
# if self.telegram and len(fixtures) > 0:
#     self.telegram.notify_daily_summary(opportunities, len(fixtures))

        start_time = time.time()
        
        try:
            # 1. Busca jogos do dia
            today = datetime.now().date().isoformat()
            logger.info(f"📅 Buscando jogos para: {today}")
            
            fixtures = self._get_today_fixtures()
            
            if not fixtures:
                logger.warning("⚠️ Nenhum jogo encontrado para hoje")
                return
            
            logger.info(f"✅ {len(fixtures)} jogos encontrados")
            
            # 2. Analisa cada jogo
            opportunities = []
            for i, fixture in enumerate(fixtures, 1):
                logger.info(f"\n--- Analisando jogo {i}/{len(fixtures)} ---")
                
                opportunity = self._analyze_fixture(fixture)
                
                if opportunity:
                    opportunities.append(opportunity)
                    # Salva no banco
                    self.db.save_opportunity(opportunity)
                                        # Notifica via Telegram
                    if self.telegram:
                        self.telegram.notify_opportunity(opportunity)
                
                # Rate limiting - aguarda entre requisições
                time.sleep(2)
            
            # 3. Rankeia e exibe resultados
            if opportunities:
                ranked = self.value_detector.rank_opportunities(opportunities)
                self._display_results(ranked)
            else:
                logger.warning("⚠️ Nenhuma oportunidade com valor detectada")
            
            # 4. Estatísticas finais
            elapsed = time.time() - start_time
            logger.info("\n" + "="*60)
            logger.info(f"✅ ANÁLISE CONCLUÍDA")
            logger.info(f"⏱️ Tempo total: {elapsed:.1f}s")
            logger.info(f"🎯 Oportunidades encontradas: {len(opportunities)}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Erro na análise diária: {e}")
            # ADICIONE: Notifica erro
        if self.telegram:
            self.telegram.notify_error(str(e))
    
    def _get_today_fixtures(self) -> List[Dict]:
        """Busca jogos do dia das ligas configuradas"""
        all_fixtures = []
        
        for league_id in self.settings.TARGET_LEAGUES:
            try:
                logger.info(f"Buscando jogos da liga {league_id}...")
                
                fixtures = self.api_client.get_fixtures_by_date(
                    date=datetime.now().date().isoformat(),
                    league_id=league_id
                )
                
                if fixtures:
                    all_fixtures.extend(fixtures)
                    logger.info(f"  ✅ {len(fixtures)} jogos encontrados")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"  ❌ Erro ao buscar jogos da liga {league_id}: {e}")
                continue
        
        return all_fixtures
    
    def _analyze_fixture(self, fixture: Dict) -> Dict:
        """
        Analisa um jogo completo
        
        Returns:
            Dict com oportunidade ou None
        """
        try:
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            fixture_id = fixture['fixture']['id']
            league_name = fixture['league']['name']
            
            logger.info(f"⚽ {home_team} vs {away_team}")
            logger.info(f"   Liga: {league_name} | ID: {fixture_id}")
            
            # 1. Coleta dados dos times
            logger.info("   📊 Coletando dados dos times...")
            
            home_data = self.data_collector.collect_team_data(
                team_id=fixture['teams']['home']['id'],
                league_id=fixture['league']['id'],
                season=fixture['league']['season']
            )
            
            away_data = self.data_collector.collect_team_data(
                team_id=fixture['teams']['away']['id'],
                league_id=fixture['league']['id'],
                season=fixture['league']['season']
            )
            
            if not home_data or not away_data:
                logger.warning("   ⚠️ Dados insuficientes dos times")
                return None
            
            # 2. Coleta H2H
            logger.info("   🤝 Coletando dados H2H...")
            h2h_data = self.data_collector.collect_h2h_data(
                team1_id=fixture['teams']['home']['id'],
                team2_id=fixture['teams']['away']['id']
            )
            
            # 3. Calcula probabilidade
            logger.info("   🧮 Calculando probabilidades...")
            probability_data = self.probability_calculator.calculate_probability(
                home_stats=home_data,
                away_stats=away_data,
                h2h_data=h2h_data,
                match_context=self._extract_match_context(fixture)
            )
            
            logger.info(f"   📈 Probabilidade Over 1.5: {probability_data['probability']:.1%}")
            logger.info(f"   🎯 Confiança: {probability_data['confidence']:.0f}%")
            
            # 4. Busca odds
            logger.info("   💰 Buscando odds...")
            odds_data = self.api_client.get_odds(fixture_id)
            
            if not odds_data:
                logger.warning("   ⚠️ Odds não disponíveis")
                return None
            
            # 5. Detecta valor
            logger.info("   🔍 Detectando valor...")
            
            match_data = {
                'fixture_id': fixture_id,
                'home_team': home_team,
                'away_team': away_team,
                'league': league_name,
                'date': fixture['fixture']['date']
            }
            
            opportunity = self.value_detector.analyze_match(
                match_data=match_data,
                probability_data=probability_data,
                odds_data=odds_data
            )
            
            if opportunity:
                logger.info(f"   ✅ VALOR DETECTADO!")
                logger.info(f"   💵 EV: {opportunity['expected_value']:.2%}")
                logger.info(f"   📊 Stake: {opportunity['recommended_stake']:.1f}%")
                logger.info(f"   ⭐ Qualidade: {opportunity['bet_quality']}")
            else:
                logger.info("   ⚠️ Sem valor detectado")
            
            return opportunity
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao analisar jogo: {e}")
            return None
    
    def _extract_match_context(self, fixture: Dict) -> Dict:
        """Extrai contexto do jogo para análise"""
        try:
            return {
                'round': fixture['league'].get('round', 'Unknown'),
                'total_rounds': 38,  # Padrão para ligas principais
                'is_derby': False,  # TODO: implementar detecção
                'is_classic': False,  # TODO: implementar detecção
                'home_position': None,  # TODO: buscar tabela
                'away_position': None,
                'total_teams': 20
            }
        except Exception:
            return {}
    
    def _display_results(self, opportunities: List[Dict]):
        """Exibe resumo das oportunidades encontradas"""
        logger.info("\n" + "="*60)
        logger.info("🎯 OPORTUNIDADES DETECTADAS")
        logger.info("="*60)
        
        for i, opp in enumerate(opportunities, 1):
            logger.info(f"\n{i}. {opp['home_team']} vs {opp['away_team']}")
            logger.info(f"   Liga: {opp['league']}")
            logger.info(f"   Data: {opp['match_date']}")
            logger.info(f"   ---")
            logger.info(f"   Probabilidade: {opp['our_probability']:.1%}")
            logger.info(f"   Odds Over 1.5: {opp['over_1_5_odds']:.2f}")
            logger.info(f"   Expected Value: {opp['expected_value']:.2%}")
            logger.info(f"   Stake Recomendado: {opp['recommended_stake']:.1f}%")
            logger.info(f"   Qualidade: {opp['bet_quality']}")
            logger.info(f"   Risco: {opp['risk_level']}")
            logger.info(f"   Confiança: {opp['confidence']:.0f}%")
    
    def update_results(self):
        """
        Atualiza resultados dos jogos finalizados
        Executa diariamente às 02:00
        """
        logger.info("="*60)
        logger.info("🔄 ATUALIZANDO RESULTADOS")
        logger.info("="*60)
        
        try:
            # Busca oportunidades dos últimos 2 dias sem resultado
            yesterday = (datetime.now() - timedelta(days=2)).date().isoformat()
            
            # TODO: Implementar busca de oportunidades pendentes
            # TODO: Para cada oportunidade, buscar resultado via API
            # TODO: Atualizar banco de dados com resultados
            
            logger.info("✅ Resultados atualizados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar resultados: {e}")
    
    def cleanup_old_data(self):
        """
        Remove dados antigos do banco
        Executa semanalmente aos domingos às 03:00
        """
        logger.info("="*60)
        logger.info("🧹 LIMPANDO DADOS ANTIGOS")
        logger.info("="*60)
        
        try:
            self.db.clear_old_data(days=90)
            logger.info("✅ Limpeza concluída")
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")
    
    def run(self):
        """Inicia scheduler com tarefas agendadas"""
        logger.info("="*60)
        logger.info("🤖 SCHEDULER INICIADO")
        logger.info("="*60)
        
        # Agenda tarefas
        schedule.every().day.at("08:00").do(self.analyze_daily_matches)
        schedule.every().day.at("02:00").do(self.update_results)
        schedule.every().sunday.at("03:00").do(self.cleanup_old_data)
        
        logger.info("📅 Tarefas agendadas:")
        logger.info("   - 08:00: Análise diária de jogos")
        logger.info("   - 02:00: Atualização de resultados")
        logger.info("   - 03:00 (Domingos): Limpeza de dados antigos")
        logger.info("")
        logger.info("⏳ Aguardando próxima execução...")
        logger.info("="*60)
        
        # Loop principal
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada 1 minuto
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Scheduler interrompido pelo usuário")
                break
                
            except Exception as e:
                logger.error(f"❌ Erro no loop do scheduler: {e}")
                time.sleep(300)  # Aguarda 5 minutos antes de tentar novamente


def main():
    """Função principal"""
    try:
        scheduler = Scheduler()
        
        # Executa análise imediatamente na primeira vez
        logger.info("🚀 Executando análise inicial...")
        scheduler.analyze_daily_matches()
        
        # Inicia scheduler
        scheduler.run()
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

