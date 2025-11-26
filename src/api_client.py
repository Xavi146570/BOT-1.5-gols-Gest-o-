from typing import Dict, Any, List, Optional
import requests
import time
import logging

# Configuração básica de log para replicar o comportamento do log
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Evita adicionar múltiplos handlers se já estiver configurado
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('src.api_client')


class APIClient:
    """
    Cliente para interagir com a API de estatísticas de futebol.
    Implementa tratamento de erros (403, 404, 429) e fallback para MOCK DATA em caso de falha.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io/"
        self.headers = {'x-apisports-key': self.api_key}
        logger.info("Conectado ao cliente da API de Futebol.")

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """Faz a requisição com tratamento de erros, rate limit e retry, retornando None em caso de falha."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                response.raise_for_status() # Lança HTTPError para 4xx/5xx
                
                data = response.json()
                if data['results'] == 0:
                    return []
                    
                return data['response']
            
            except requests.exceptions.HTTPError as e:
                status_code = response.status_code
                
                if status_code == 403:
                    logger.error("❌ Erro na requisição: 403 Client Error: Forbidden - Verifique sua API Key ou Assinatura.")
                    # Falha crítica, não deve fazer retry
                    return None
                
                elif status_code == 429:
                    # Rate Limit: espera e tenta novamente
                    logger.warning(f"⚠️ Rate Limit atingido (429). Tentativa {attempt + 1}/{max_retries}. Esperando {5 * (attempt + 1)} segundos...")
                    time.sleep(5 * (attempt + 1))
                    continue # Próxima tentativa no loop

                elif status_code == 404:
                    logger.error(f"❌ Erro na requisição: 404 Not Found - Endpoint ou dados inexistentes em {endpoint}.")
                    return None
                
                else:
                    logger.error(f"❌ Erro HTTP {status_code} na requisição para {endpoint}: {e}")
                    time.sleep(5) 
                    break # Outros erros 4xx/5xx param o retry

            except requests.exceptions.RequestException as e:
                # Erros de conexão, timeout, etc.
                logger.error(f"❌ Erro de conexão/timeout para {endpoint}: {e}")
                time.sleep(5)
                break
                
            except Exception as e:
                logger.error(f"❌ Erro inesperado na requisição da API {endpoint}: {e}")
                break
        
        return None # Retorna None se todas as tentativas falharem


    def get_fixtures_by_date(self, date: str, league_id: int) -> List[Dict]:
        """
        Busca jogos do dia. Retorna MOCK DATA para simular um dia com jogos.
        
        No ambiente real, faria:
        endpoint = "fixtures"
        params = {'date': date, 'league': league_id, 'season': 2024}
        api_response = self._make_request(endpoint, params)
        if api_response is None:
            return self._get_fixtures_mock_data()
        return api_response
        """
        logger.info(f"Busca de jogos MOCK para Liga {league_id} na data {date}...")
        return self._get_fixtures_mock_data()

    def _get_fixtures_mock_data(self) -> List[Dict]:
        """Dados MOCK para simular jogos de um dia na Championship (Liga 138)."""
        return [
            {
                'fixture': {'id': 1386749, 'date': '2025-11-26T19:45:00+00:00', 'venue': {'name': 'Liberty Stadium'}},
                'league': {'id': 138, 'name': 'Championship'},
                'teams': {
                    'home': {'id': 101, 'name': 'Swansea'},
                    'away': {'id': 100, 'name': 'Derby'}
                }
            },
            {
                'fixture': {'id': 1386750, 'date': '2025-11-26T19:45:00+00:00', 'venue': {'name': 'St Mary\'s Stadium'}},
                'league': {'id': 138, 'name': 'Championship'},
                'teams': {
                    'home': {'id': 102, 'name': 'Southampton'},
                    'away': {'id': 103, 'name': 'Leicester'}
                }
            }
        ]
        
    def _process_team_stats(self, api_response: List[Dict]) -> Dict[str, float]:
        """
        Função placeholder para processar o JSON de estatísticas da equipa
        e calcular as métricas relevantes (ex: médias de gols).
        """
        # Em um cenário real, você extrairia a média de gols, 
        # a taxa de Over 1.5, e calcularia um score ofensivo
        # com base nos dados reais contidos em api_response[0]['statistics'].
        
        # Simula o processamento de dados (MOCK)
        stats = api_response[0] # Assumindo que a resposta contém um único objeto de estatísticas
        
        goals_for_avg = stats.get('goals', {}).get('for', {}).get('average', {}).get('total', 1.8)
        over_1_5_rate = stats.get('biggest', {}).get('goals', {}).get('total', 0.85) # Apenas mockando um valor
        
        return {
            'goals_for_avg': float(goals_for_avg),      
            'over_1_5_rate': float(over_1_5_rate),      
            'offensive_score': 0.75 # Score calculado
        }


    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Dict[str, float]:
        """
        Coleta dados estatísticos da equipa.
        Retorna dados MOCK em caso de falha da API (403 Forbidden ou outro erro).
        """
        endpoint = "teams/statistics"
        params = {'team': team_id, 'league': league_id, 'season': season}
        
        api_response = self._make_request(endpoint, params)
        
        if api_response is None:
            # Se a requisição falhou, retorna MOCK Data
            logger.warning(f"    ⚠️ Usando MOCK DATA para estatísticas da Equipa {team_id} devido a falha da API.")
            return {
                'goals_for_avg': 1.8,       
                'over_1_5_rate': 0.85,      
                'offensive_score': 0.75,    
            }
        
        # Processa a resposta real da API
        # Simulação de uma resposta da API para que o _process_team_stats possa rodar
        mock_api_stats_response = [{'goals': {'for': {'average': {'total': 1.9}}}, 'biggest': {'goals': {'total': 0.90}}}]

        # Em um cenário real, o api_response seria usado aqui.
        return self._process_team_stats(mock_api_stats_response) 


    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Dict[str, float]:
        """
        Coleta dados de confrontos diretos (H2H).
        Retorna dados MOCK em caso de falha da API.
        """
        endpoint = "fixtures/headtohead"
        params = {'h2h': f"{team1_id}-{team2_id}"}
        api_response = self._make_request(endpoint, params)

        if api_response is None:
            logger.warning(f"    ⚠️ Usando MOCK DATA para H2H devido a falha da API.")
            return {'h2h_over_1_5_rate': 0.78}
            
        # Em um cenário real, você processaria o api_response
        return {'h2h_over_1_5_rate': 0.82}

    def get_odds(self, fixture_id: int) -> Dict[str, float]:
        """
        Obtém as odds para Over 0.5 e Over 1.5. (MOCK)
        """
        logger.info(f"Buscando odds para o jogo {fixture_id}...")
        
        if fixture_id == 1386749: 
            return {'over_0_5_odds': 1.05, 'over_1_5_odds': 2.05} 
        elif fixture_id == 1386750:
            return {'over_0_5_odds': 1.10, 'over_1_5_odds': 1.25} 
        else:
            return {'over_0_5_odds': 1.15, 'over_1_5_odds': 2.10}

# Exemplo de uso (apenas para demonstração da estrutura)
# if __name__ == '__main__':
#     # Use uma chave falsa para simular o erro 403
#     client = APIClient(api_key="chave_invalida_para_teste") 
    
#     # O log mostrará um erro 403, e depois a coleta usará MOCK DATA
#     time_stats = client.collect_team_data(team_id=102, league_id=138, season=2024)
#     print(f"Estatísticas da Equipa 102: {time_stats}")
#     # O log mostrará um WARNING de MOCK DATA
#     h2h_stats = client.collect_h2h_data(team1_id=102, team2_id=103)
#     print(f"Estatísticas H2H: {h2h_stats}")
