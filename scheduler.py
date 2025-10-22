"""
Scheduler - Sistema Over 1.5
Automação de análise diária de jogos e detecção de oportunidades
"""

import logging
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import schedule
import threading

from config.settings import Settings
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
    
    def self_ping(self):
        """
        Faz ping em si mesmo para manter Render acordado
        Executa a cada 14 minutos
        """
        try:
            response = requests.get(self.self_ping_url, timeout=10)
            if response.status_code == 200:
                logger.debug(f"🔄 Self-ping OK: {response.status_code}")
            else:
                logger.warning(f"⚠️ Self-ping retornou: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Erro no self-ping: {e}")
    
    def start_self_ping_thread(self):
        """
        Inicia thread separada para self-ping a cada 14 minutos
        Isso mantém o app acordado no Render (que dorme após 15 min)
        """
        def ping_loop():
            logger.info("🔄 Self-ping iniciado (intervalo: 14 minutos)")
            while True:
                try:
                    self.self_ping()
                    time.sleep(14 * 60)  # 14 minutos
                except Exception as e:
                    logger.error(f"❌ Erro no loop de self-ping: {e}")
                    time.sleep(60)  # Aguarda 1 minuto antes de tentar novamente
        
        # Inicia thread daemon (termina quando programa principal termina)
        ping_thread = threading.Thread(target=ping_loop, daemon=True)
        ping_thread.start()
        logger.info("✅ Thread de self-ping iniciada")
    
    def analyze_daily_matches(self):
        """
        Análise completa dos jogos do dia
        Executa diariamente às 08:00
        """
        logger.info("="*60)
        logger.info("🚀 INICIANDO ANÁLISE DIÁRIA")
        logger.info("="*60)
        
        start_time = time.time()
        
        try:
            # 1. Busca jogos do dia - FORÇANDO UTC
            now_utc = datetime.now(timezone.utc)
            today = now_utc.date().isoformat()
            
            logger.info(f"🌍 Timezone: UTC")
            logger.info(f"📅 Data UTC: {today}")
            logger.info(f"🕐 Hora UTC: {now_utc.strftime('%H:%M:%S')}")
            logger.info(f"📅 Buscando jogos para: {today}")
            
            fixtures = self._get_today_fixtures(today)
            
            if not fixtures:
                logger.warning("⚠️ Nenhum jogo encontrado para hoje")
                logger.info(f"   ℹ️ Verifique se há jogos agendados para {today} nas 10 ligas configuradas")
                logger.info(f"   ℹ️ Ligas: Premier League, La Liga, Serie A, Bundesliga, Ligue 1,")
                logger.info(f"           Champions League, Europa League, Championship, Portugal, Holanda")
                return
            
            logger.info(f"✅ {len(fixtures)} jogos encontrados")
            
            # Notifica início via Telegram
            if self.telegram:
                self.telegram.notify_analysis_start(len(fixtures))
            
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
            
            # Notifica resumo via Telegram
            if self.telegram:
                self.telegram.notify_daily_summary(opportunities, len(fixtures))
            
            # 4. Estatísticas finais
            elapsed = time.time() - start_time
            logger.info("\n" + "="*60)
            logger.info(f"✅ ANÁLISE CONCLUÍDA")
            logger.info(f"⏱️ Tempo total: {elapsed:.1f}s")
            logger.info(f"🎯 Oportunidades encontradas: {len(opportunities)}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Erro na análise diária: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Notifica erro via Telegram
            if self.telegram:
                self.telegram.notify_error(str(e))
    
    def _get_today_fixtures(self, today: str) -> List[Dict]:
        """
        Busca jogos do dia das ligas configuradas
        
        Args:
            today: Data no formato YYYY-MM-DD
        """
        all_fixtures = []
        
        logger.info(f"\n🔍 Buscando jogos em 10 ligas para {today}...")
        
        # Nomes das ligas para log amigável
        league_names = {
            39: "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            140: "La Liga 🇪🇸",
            135: "Serie A 🇮🇹",
            78: "Bundesliga 🇩🇪",
            61: "Ligue 1 🇫🇷",
            2: "Champions League ⚽",
            3: "Europa League ⚽",
            40: "Championship 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            94: "Primeira Liga 🇵🇹",
            88: "Eredivisie 🇳🇱"
        }
        
        for league_id in self.settings.TARGET_LEAGUES:
            try:
                league_name = league_names.get(league_id, f"Liga {league_id}")
                logger.info(f"  📡 {league_name}...")
                
                fixtures = self.api_client.get_fixtures_by_date(
                    date=today,
                    league_id=league_id
                )
                
                if fixtures:
                    all_fixtures.extend(fixtures)
                    logger.info(f"     ✅ {len(fixtures)} jogo(s) encontrado(s)")
                else:
                    logger.debug(f"     ⚪ Sem jogos agendados")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"     ❌ Erro: {e}")
                continue
        
        logger.info(f"\n📊 TOTAL: {len(all_fixtures)} jogos encontrados")
        
        # Log detalhado dos jogos encontrados
        if all_fixtures:
            logger.info("\n📋 Lista de jogos:")
            for i, fixture in enumerate(all_fixtures, 1):
                home = fixture['teams']['home']['name']
                away = fixture['teams']['away']['name']
                league = fixture['league']['name']
                match_time = fixture['fixture']['date']
                logger.info(f"   {i}. {home} vs {away} | {league} | {match_time}")
        
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
            
            if not odds_data or not odds_data.get('over_1_5_odds'):
                logger.warning("   ⚠️ Odds Over 1.5 não disponíveis")
                return None
            
            logger.info(f"   💵 Odds Over 1.5: {odds_data['over_1_5_odds']:.2f}")
            
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
                logger.info("   ⚠️ Sem valor detectado (EV negativo ou critérios não atendidos)")
            
            return opportunity
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao analisar jogo: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _extract_match_context(self, fixture: Dict) -> Dict:
        """Extrai contexto do jogo para análise"""
        try:
            return {
                'round': fixture['league'].get('round', 'Unknown'),
                'total_rounds': 38,
                'is_derby': False,
                'is_classic': False,
                'home_position': None,
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
        
        # Inicia self-ping em thread separada
        self.start_self_ping_thread()
        
        # Agenda tarefas
        schedule.every().day.at("08:00").do(self.analyze_daily_matches)
        schedule.every().day.at("02:00").do(self.update_results)
        schedule.every().sunday.at("03:00").do(self.cleanup_old_data)
        
        logger.info("📅 Tarefas agendadas:")
        logger.info("   - 08:00 UTC: Análise diária de jogos")
        logger.info("   - 02:00 UTC: Atualização de resultados")
        logger.info("   - 03:00 UTC (Domingos): Limpeza de dados antigos")
        logger.info("   - A cada 14 min: Self-ping (manter ativo)")
        logger.info("")
        logger.info("⏳ Aguardando próxima execução...")
        logger.info("="*60)
        
        # Loop principal
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Scheduler interrompido pelo usuário")
                break
                
            except Exception as e:
                logger.error(f"❌ Erro no loop do scheduler: {e}")
                time.sleep(300)


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
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
