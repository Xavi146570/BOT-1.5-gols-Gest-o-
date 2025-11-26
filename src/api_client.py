from typing import Dict, Any, List, Optional
import requests
import time
import logging
import datetime 

# Configuração básica de log
logger = logging.getLogger('src.api_client')
logger.setLevel(logging.INFO)


class APIClient:
    """
    Cliente para interagir com a API de estatísticas de futebol (API-Sports V3).
    Implementa tratamento de erros e fallback para MOCK DATA em caso de falha.
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
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                
                if response.status_code == 403:
                    logger.error(f"❌ Erro de Autenticação (403 Forbidden). Chave inválida ou expirada.")
                    return None
                
                elif response.status_code == 429:
                    delay = 5 * (attempt + 1)
                    logger.warning(f"⚠️ Rate Limit atingido (429). Tentativa {attempt + 1}/{max_retries}. Esperando {delay}s...")
                    time.sleep(delay)
                    continue

                response.raise_for_status()

                data = response.json()
                
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
        return None


    def _get_fixtures_mock_data(self, date: str) -> List[Dict]:
        """Dados MOCK para simular jogos de um dia."""
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

    def _process_team_stats(self, api_response: List[Dict]) -> Dict[str, float]:
        """
        [MÉTODO CORRIGIDO/REINSERIDO] Processamento MOCK de estatísticas da equipa.
        Isto deve ser substituído pela sua lógica de cálculo de Poisson.
        """
        # Mantendo o MOCK do processamento de estatísticas por enquanto
        if not api_response:
             return {'goals_for_avg': 1.8, 'over_1_5_rate': 0.85, 'offensive_score': 0.75}

        # Simulação de extração de dados da resposta real
        # Na ausência de implementação do Poisson, retornamos valores fixos
        return {
            'goals_for_avg': 1.7,      
            'over_1_5_rate': 0.88,      
            'offensive_score': 0.78 
        }

    # MÉTODOS DE COLETA DE DADOS (USANDO FALLBACK)

    def get_fixtures_by_date(self, date: str, league_id: int) -> List[Dict]:
        """Busca jogos do dia com MOCK DATA como fallback."""
        endpoint = "fixtures"
        # Busca apenas por data e liga (sem 'season' para evitar conflito de época)
        params = {'date': date, 'league': league_id} 
        
        api_response = self._make_request(endpoint, params)
        
        if api_response is None or api_response == []:
            # Caso 1 ou 2: Falha ou 0 resultados. Cai no MOCK.
            if api_response == []:
                logger.info(f"⚠️ A API não tem jogos agendados para a Liga {league_id} na data {date}. Usando MOCK DATA.")
            else:
                 logger.warning(f"⚠️ FALHA CRÍTICA na API para fixtures. Usando MOCK DATA para jogos de {date}.")

            return self._get_fixtures_mock_data(date)
            
        return api_response


    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Dict[str, float]:
        """Coleta dados estatísticos da equipa com MOCK DATA como fallback."""
        endpoint = "teams/statistics"
        # Aqui, 'season' é necessário e é mantido.
        params = {'team': team_id, 'league': league_id, 'season': season} 
        
        api_response = self._make_request(endpoint, params)
        
        if api_response is None or api_response == []:
            logger.warning(f"    ⚠️ Usando MOCK DATA para estatísticas da Equipa {team_id} devido a falha da API ou 0 resultados.")
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

        if api_response is None or api_response == []:
            logger.warning(f"    ⚠️ Usando MOCK DATA para H2H devido a falha da API ou 0 resultados.")
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
