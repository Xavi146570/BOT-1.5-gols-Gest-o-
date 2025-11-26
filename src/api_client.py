from typing import Dict, Any, List, Optional
import requests
import time
import logging
import datetime # Importado para uso no MOCK DATA

# Configuração básica de log
logger = logging.getLogger('src.api_client')
logger.setLevel(logging.INFO)


class APIClient:
    """
    Cliente para interagir com a API de estatísticas de futebol (API-Sports V3).
    Implementa tratamento de erros (403, 404, 429) e fallback para MOCK DATA em caso de falha.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io/"
        self.headers = {'x-apisports-key': self.api_key}
        logger.info("Conectado ao cliente da API de Futebol e cabeçalho de autenticação configurado.")

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """Faz a requisição com tratamento de erros (incluindo 403 Forbidden e 429 Rate Limit) e retry."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}{endpoint}"
                
                # NOVO LOG: Mostra os parâmetros de busca
                logger.debug(f"🔍 Enviando requisição para {endpoint} com Parâmetros: {params}")

                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                
                # Tratamento de Erro HTTP
                if response.status_code == 403:
                    logger.error(f"❌ Erro de Autenticação (403 Forbidden). Chave inválida ou expirada.")
                    return None
                
                elif response.status_code == 429:
                    delay = 5 * (attempt + 1)
                    logger.warning(f"⚠️ Rate Limit atingido (429). Tentativa {attempt + 1}/{max_retries}. Esperando {delay}s...")
                    time.sleep(delay)
                    continue

                response.raise_for_status() # Lança HTTPError para outros 4xx/5xx

                data = response.json()
                
                # Verifica se a API retornou um erro interno (ex: erro de parâmetro)
                if data.get('errors'):
                    logger.error(f"❌ Erro da API na resposta: {data['errors']}")
                    return None

                if data['results'] == 0:
                    logger.info(f"✅ Requisição bem-sucedida, mas 0 resultados encontrados para {endpoint}.")
                    return []
                    
                logger.info(f"✅ Sucesso: {data['results']} resultados obtidos para {endpoint}.")
                return data['response']
            
            except requests.exceptions.HTTPError as e:
                logger.error(f"❌ Erro HTTP {response.status_code} na requisição para {endpoint}: {e}")
                break
            
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Erro de conexão/timeout para {endpoint}: {e}")
                time.sleep(5)
                break
                
            except Exception as e:
                logger.error(f"❌ Erro inesperado na requisição da API {endpoint}: {e}")
                break
        
        logger.error("❌ Todas as tentativas de requisição falharam.")
        return None # Retorna None se todas as tentativas falharem


    def _get_fixtures_mock_data(self, date: str) -> List[Dict]:
        """
        Dados MOCK para simular jogos de um dia. 
        O campo 'date' é dinâmico, baseado no input.
        """
        # Usamos o 'date' de entrada para simular a hora do jogo (ex: 19:45:00)
        fixture_date_time = f"{date}T19:45:00+00:00"
        
        return [
            {
                'fixture': {'id': 1386749, 'date': fixture_date_time, 'venue': {'name': 'Liberty Stadium'}},
                'league': {'id': 138, 'name': 'Championship'},
                'teams': {
                    'home': {'id': 101, 'name': 'Swansea'},
                    'away': {'id': 100, 'name': 'Derby'}
                }
            },
            {
                'fixture': {'id': 1386750, 'date': fixture_date_time, 'venue': {'name': 'St Mary\'s Stadium'}},
                'league': {'id': 138, 'name': 'Championship'},
                'teams': {
                    'home': {'id': 102, 'name': 'Southampton'},
                    'away': {'id': 103, 'name': 'Leicester'}
                }
            }
        ]

    # ... (restante da classe APIClient omitido por brevidade, mas deve ser mantido)
    # IMPORTANTE: Mantenha todos os outros métodos (como _process_team_stats) do ficheiro original
    
    # MÉTODOS DE COLETA DE DADOS (USANDO FALLBACK)

    def get_fixtures_by_date(self, date: str, league_id: int) -> List[Dict]:
        """Busca jogos do dia com MOCK DATA como fallback. SEM O PARÂMETRO 'SEASON'."""
        endpoint = "fixtures"
        
        # REMOÇÃO DE 'SEASON' PARA EVITAR CONFLITO COM A DATA.
        params = {'date': date, 'league': league_id} 
        
        api_response = self._make_request(endpoint, params)
        
        if api_response is None:
            # Caso 1: Falha grave de requisição (timeout, 403, 5xx)
            logger.warning(f"⚠️ FALHA CRÍTICA na API. Usando MOCK DATA para jogos de {date}.")
            return self._get_fixtures_mock_data(date)
            
        elif api_response == []:
            # Caso 2: API funciona, mas não há jogos nessa data/liga
            logger.info(f"✅ API contactada com sucesso, mas 0 jogos agendados para {date}.")
            return []
            
        return api_response


    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Dict[str, float]:
        """Coleta dados estatísticos da equipa com MOCK DATA como fallback."""
        endpoint = "teams/statistics"
        # Aqui, 'season' é necessário e é mantido.
        params = {'team': team_id, 'league': league_id, 'season': season} 
        
        api_response = self._make_request(endpoint, params)
        
        if api_response is None:
            logger.warning(f"    ⚠️ Usando MOCK DATA para estatísticas da Equipa {team_id} devido a falha da API.")
            return {
                'goals_for_avg': 1.8,       
                'over_1_5_rate': 0.85,      
                'offensive_score': 0.75,    
            }
        
        return self._process_team_stats(api_response) 


    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Dict[str, float]:
        """Coleta dados H2H com MOCK DATA como fallback."""
        endpoint = "fixtures/headtohead"
        params = {'h2h': f"{team1_id}-{team2_id}"}
        api_response = self._make_request(endpoint, params)

        if api_response is None:
            logger.warning(f"    ⚠️ Usando MOCK DATA para H2H devido a falha da API.")
            return {'h2h_over_1_5_rate': 0.78}
            
        # Simulação de processamento H2H
        return {'h2h_over_1_5_rate': 0.82}


    def get_odds(self, fixture_id: int) -> Dict[str, float]:
        """Obtém as odds (MOCK)."""
        logger.info(f"Buscando odds (MOCK) para o jogo {fixture_id}...")
        
        # MOCK de Odds
        if fixture_id == 1386749: 
            return {'over_0_5_odds': 1.05, 'over_1_5_odds': 2.05} 
        elif fixture_id == 1386750:
            return {'over_0_5_odds': 1.10, 'over_1_5_odds': 1.25} 
        else:
            return {'over_0_5_odds': 1.15, 'over_1_5_odds': 2.10}

    # Você precisa incluir aqui os métodos collect_team_data, _process_team_stats, collect_h2h_data
    # e get_odds do seu ficheiro original para a classe funcionar completamente.
    # O código acima apenas mostra as correções essenciais.
