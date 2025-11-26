import os
import logging
import datetime
# Importa do mesmo diretório src
from api_client import APIClient  
# Assume que a lógica de cálculo está em probability_calculator.py
from probability_calculator import BettingCalculator 

# --- Configuração de Logging ---
logger = logging.getLogger('runner')
logger.setLevel(logging.INFO)

# --- Variável de Ambiente OBRIGATÓRIA ---
API_KEY_NAME = "API_FOOTBALL_KEY" 

def main():
    """
    Função principal que carrega a chave da API e inicia o processo de análise.
    Busca jogos da data de amanhã, para garantir que as odds ainda estão disponíveis.
    """
    
    # 1. Tenta carregar a chave da API da variável de ambiente
    api_key = os.getenv(API_KEY_NAME)

    if not api_key:
        logger.error(f"❌ ERRO CRÍTICO: Variável de ambiente '{API_KEY_NAME}' não encontrada ou vazia.")
        api_key = "" 
    else:
        logger.info("🔑 Chave da API carregada com sucesso do ambiente.")
        
    
    # 2. CALCULA A DATA DE BUSCA
    # Opção 2 (Recomendada): Data de AMANHÃ, para ter tempo para analisar e apostar.
    target_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"📅 A data de análise foi definida para: {target_date}")
    
    
    # 3. Inicializa o cliente e a calculadora
    client = APIClient(api_key=api_key)
    calculator = BettingCalculator()

    # --- FLUXO PRINCIPAL DE ANÁLISE ---
    
    league_id = 138 # Championship
    
    # Busca jogos da data dinâmica
    fixtures = client.get_fixtures_by_date(date=target_date, league_id=league_id)
    
    if not fixtures:
        logger.warning(f"Nenhum jogo encontrado para {target_date} ou MOCK DATA indisponível. Finalizando.")
        return

    opportunities = []

    for i, fixture in enumerate(fixtures, 1):
        fixture_id = fixture['fixture']['id']
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        home_id = fixture['teams']['home']['id']
        away_id = fixture['teams']['away']['id']
        
        logger.info(f"\n--- Analisando jogo {i}/{len(fixtures)} ---")
        logger.info(f"⚽ {home_team} vs {away_team}")
        logger.info(f"   Liga: Championship | ID: {fixture_id}")
        logger.info(f"   📊 Coletando dados dos times...")
        
        # Coleta de dados (Real ou Mock, se a API falhar)
        home_stats = client.collect_team_data(home_id, league_id, season=2024)
        away_stats = client.collect_team_data(away_id, league_id, season=2024)
        logger.info(f"   🤝 Coletando dados H2H...")
        h2h_stats = client.collect_h2h_data(home_id, away_id)
        logger.info(f"   💰 Buscando odds...")
        odds = client.get_odds(fixture_id) # Este ainda é um MOCK
        
        # CÁLCULOS (Manter MOCK por enquanto, até implementarmos Poisson)
        
        for goal_line in [0.5, 1.5]:
            # Usa o calculate_over_probability da classe BettingCalculator
            prob, conf = calculator.calculate_over_probability(home_stats, away_stats, h2h_stats, goal_line)
            odds_key = f'over_{int(goal_line*10)}_odds'
            market_odds = odds.get(odds_key)
            
            if market_odds and market_odds > 1.0:
                ev = calculator.calculate_expected_value(prob, market_odds)
                kelly = calculator.calculate_kelly_criterion(prob, market_odds)
                
                logger.info(f"   🧮 Calculando probabilidades...")
                logger.info(f"   📈 Probabilidade Over {goal_line}: {prob*100:.1f}%")
                logger.info(f"   🎯 Confiança: {conf*100:.0f}%")
                logger.info(f"   💵 Odds Over {goal_line}: {market_odds:.2f}")

                if ev > 0.05: # Filtro de EV > 5%
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
        
        # (Lógica para salvar oportunidades no banco deve vir aqui)
    
    # --- RANKING E RESUMO ---
    
    opportunities.sort(key=lambda x: x['ev'], reverse=True)
    
    logger.info("\n============================================================")
    logger.info("🎯 OPORTUNIDADES DETECTADAS (RANKED)")
    logger.info("============================================================")
    
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
    # Adicionar o manipulador de log para garantir que as mensagens de data apareçam
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()
