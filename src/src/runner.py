import os
import logging
import datetime
from api_client import APIClient  
from probability_calculator import BettingCalculator 

# --- Configuração de Logging ---
logger = logging.getLogger('runner')
logger.setLevel(logging.INFO)

# --- Variável de Ambiente OBRIGATÓRIA ---
API_KEY_NAME = "API_FOOTBALL_KEY" 

def get_utc_today():
    """
    Render utiliza UTC.
    Esta função garante que a data usada na busca nunca fique no passado.
    """
    return datetime.datetime.utcnow().date()


def main():
    """
    Função principal que carrega a chave da API e inicia o processo de análise.
    Busca jogos de hoje +5 dias (garante jogos futuros).
    """

    # 1. Tenta carregar a chave da API da variável de ambiente
    api_key = os.getenv(API_KEY_NAME)

    if not api_key:
        logger.error(f"❌ ERRO CRÍTICO: Variável de ambiente '{API_KEY_NAME}' não encontrada ou vazia.")
        api_key = "" 
    else:
        logger.info("🔑 Chave da API carregada com sucesso do ambiente.")
        

    # ---------------------------------------------------------------------
    # 2. CALCULA A DATA DE BUSCA (CORRIGIDO PARA UTC)
    # ---------------------------------------------------------------------
    today_utc = get_utc_today()
    days_to_add = 5

    target_date = (today_utc + datetime.timedelta(days=days_to_add)).strftime("%Y-%m-%d")
    
    # LOG CRÍTICO
    logger.info("============================================================")
    logger.info(f"📅 Hoje (UTC): {today_utc}")
    logger.info(f"📅 Data de análise definida: {target_date} (+{days_to_add} dias)")
    logger.info("============================================================")
    

    # 3. Inicializa o cliente e a calculadora
    client = APIClient(api_key=api_key)
    calculator = BettingCalculator()

    league_id = 138  # Championship
    
    # ---------------------------------------------------------------------
    # 4. Busca jogos futuros
    # ---------------------------------------------------------------------
    fixtures = client.get_fixtures_by_date(date=target_date, league_id=league_id)
    
    if not fixtures:
        logger.warning(f"⚠️ Nenhum jogo encontrado para {target_date}. Finalizando.")
        return

    opportunities = []

    # ---------------------------------------------------------------------
    # 5. LOOP PRINCIPAL DE ANÁLISE
    # ---------------------------------------------------------------------
    for i, fixture in enumerate(fixtures, 1):

        try:
            fixture_id = int(fixture['fixture']['id'])
            home_id = int(fixture['teams']['home']['id'])
            away_id = int(fixture['teams']['away']['id'])
        except:
            logger.error(f"❌ Erro ao extrair IDs. Pulando este jogo.")
            continue

        # NÃO ANALISAR JOGOS QUE JÁ ACONTECERAM (proteção extra)
        fixture_date_str = fixture['fixture']['date'][:10]
        try:
            fixture_date = datetime.datetime.strptime(fixture_date_str, "%Y-%m-%d").date()
            if fixture_date < today_utc:
                logger.warning(f"⚠️ Jogo ignorado (data passada): {fixture_date}")
                continue
        except:
            pass
        
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        
        logger.info(f"\n--- Analisando jogo {i}/{len(fixtures)} ---")
        logger.info(f"⚽ {home_team} vs {away_team}")
        logger.info(f"   Liga: Championship | ID: {fixture_id}")
        logger.info(f"   📊 Coletando dados dos times...")
        
        # Coleta de dados
        home_stats = client.collect_team_data(home_id, league_id, season=2024)
        away_stats = client.collect_team_data(away_id, league_id, season=2024)
        
        if not home_stats or not away_stats:
            logger.warning("⚠️ Dados insuficientes. Pulando jogo.")
            continue
            
        logger.info(f"   🤝 Coletando dados H2H...")
        h2h_stats = client.collect_h2h_data(home_id, away_id)
        
        logger.info(f"   💰 Buscando odds...")
        odds = client.get_odds(fixture_id)  # MOCK
        
        # ---------------------------------------------------------------------
        # 6. CÁLCULOS PARA OVER 0.5 e 1.5
        # ---------------------------------------------------------------------
        for goal_line in [0.5, 1.5]:

            prob, conf = calculator.calculate_over_probability(home_stats, away_stats, h2h_stats, goal_line)
            odds_key = f'over_{int(goal_line*10)}_odds'
            market_odds = odds.get(odds_key)
            
            if not market_odds or market_odds <= 1.0:
                continue

            ev = calculator.calculate_expected_value(prob, market_odds)
            kelly = calculator.calculate_kelly_criterion(prob, market_odds)
            
            logger.info(f"   🧮 Calculando probabilidades...")
            logger.info(f"   📈 Probabilidade Over {goal_line}: {prob*100:.1f}%")
            logger.info(f"   🎯 Confiança: {conf*100:.0f}%")
            logger.info(f"   💵 Odds Over {goal_line}: {market_odds:.2f}")

            if ev > 0.05:
                logger.info(f"   ✅ VALOR DETECTADO em Over {goal_line}!")
                logger.info(f"   💵 EV: {ev*100:.2f}%")
                logger.info(f"   📊 Kelly Pura (F): {kelly:.2f}%")
                
                opportunities.append({
                    'team1': home_team,
                    'team2': away_team,
                    'league': 'Championship',
                    'market': f'Over {goal_line}',
                    'prob': prob,
                    'odds': market_odds,
                    'ev': ev,
                    'confidence': conf,
                    'kelly': kelly
                })
            else:
                logger.info(f"   ⚠️ Sem valor detectado em Over {goal_line} (EV: {ev*100:.2f}%).")
    

    # ---------------------------------------------------------------------
    # 7. RANKING FINAL
    # ---------------------------------------------------------------------
    opportunities.sort(key=lambda x: x['ev'], reverse=True)
    
    logger.info("\n============================================================")
    logger.info("🎯 OPORTUNIDADES DETECTADAS (RANKED)")
    logger.info("============================================================")
    
    if not opportunities:
        logger.info("Nenhuma oportunidade com valor detectada.")
    else:
        for i, opp in enumerate(opportunities, 1):
            logger.info(f"\n{i}. {opp['team1']} vs {opp['team2']} | Mercado: {opp['market']}")
            logger.info(f"   Liga: {opp['league']}")
            logger.info("   ---")
            logger.info(f"   Probabilidade: {opp['prob']*100:.1f}%")
            logger.info(f"   Odds Mercado: {opp['odds']:.2f}")
            logger.info(f"   Expected Value: {opp['ev']*100:.2f}%")
            logger.info(f"   Confiança: {opp['confidence']*100:.0f}%")
            logger.info(f"   Kelly Pura (F): {opp['kelly']:.2f}%")

    logger.info("\n============================================================")
    logger.info("✅ ANÁLISE CONCLUÍDA")
    logger.info(f"🎯 Oportunidades encontradas: {len(opportunities)}")
    logger.info("============================================================")


if __name__ == '__main__':
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    main()
