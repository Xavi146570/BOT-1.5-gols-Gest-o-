from typing import Dict, Any, List, Optional
import requests
import time
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Note: 'v3.football' é o endpoint correto, mas pode variar.
        self.base_url = "https://v3.football.api-sports.io/"
        self.headers = {'x-apisports-key': self.api_key}
        logger.info("Conectado ao cliente da API de Futebol.")

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """Faz a requisição com tratamento de erros e rate limit, retornando None em caso de falha."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status() # Lança HTTPError para 4xx/5xx
            
            data = response.json()
            if data['results'] == 0:
                return []
                
            return data['response']
        
        except requests.exceptions.HTTPError as e:
            # Captura 403 Forbidden e 404 Not Found (para endpoints que podem não existir)
            if response.status_code == 403:
                logger.error(f"❌ Erro na requisição: 403 Client Error: Forbidden - Verifique sua API Key ou Assinatura.")
                # Retorna None para sinalizar falha na API e permitir o fallback nos métodos de coleta
                return None 
            elif response.status_code == 404:
                logger.error(f"❌ Erro na requisição: 404 Not Found - Endpoint ou dados inexistentes.")
                return None
            else:
                logger.error(f"❌ Erro HTTP {response.status_code}: {e}")
                time.sleep(5) 
                return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado na requisição da API {endpoint}: {e}")
            return None

    def get_fixtures_by_date(self, date: str, league_id: int) -> List[Dict]:
        """Busca jogos do dia (MOCK)."""
        # MOCK ou implementação real aqui.
        return []

    def get_odds(self, fixture_id: int) -> Dict[str, float]:
        """
        Obtém as odds para Over 0.5 e Over 1.5.
        
        MOCK: Simula odds onde o Over 0.5 tem EV Negativo e o Over 1.5 tem EV Positivo/Neutro.
        """
        logger.info(f"Buscando odds para o jogo {fixture_id}...")
        
        # MOCK de Odds: Over 0.5 com odd baixa e Over 1.5 com odd alta para forçar o teste da Odd Justa
        if fixture_id == 1386749: # Swansea vs Derby
             return {'over_0_5_odds': 1.05, 'over_1_5_odds': 2.05} # Over 1.5 tem chance de valor
        elif fixture_id == 1386750: # Southampton vs Leicester
             return {'over_0_5_odds': 1.10, 'over_1_5_odds': 1.25} # Over 0.5 deve gerar sugestão de Odd Justa
        else:
             return {'over_0_5_odds': 1.15, 'over_1_5_odds': 2.10}


    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Dict[str, float]:
        """
        Coleta dados estatísticos da equipa.
        Retorna dados MOCK em caso de falha da API (403 Forbidden).
        """
        endpoint = "teams/statistics"
        params = {'team': team_id, 'league': league_id, 'season': season}
        
        # Realiza a requisição
        api_response = self._make_request(endpoint, params)
        
        if api_response is None:
            # Se a requisição falhou (ex: 403 Forbidden), retorna MOCK Data
            logger.warning(f"   ⚠️ Usando MOCK DATA para estatísticas da Equipa {team_id} devido a falha da API.")
            return {
                'goals_for_avg': 1.8,         # Média de gols marcados
                'over_1_5_rate': 0.85,        # Taxa de jogos com Over 1.5
                'offensive_score': 0.75,      # Score ofensivo
            }
        
        # Processa a resposta real da API (sua lógica deve estar aqui)
        # return self._process_team_stats(api_response) 
        
        # MOCK de processamento
        return {
            'goals_for_avg': 1.8, 
            'over_1_5_rate': 0.85, 
            'offensive_score': 0.75
        }


    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Dict[str, float]:
        """
        Coleta dados de confrontos diretos (H2H).
        Retorna dados MOCK em caso de falha da API.
        """
        # endpoint = "fixtures/headtohead"
        # params = {'h2h': f"{team1_id}-{team2_id}"}
        # api_response = self._make_request(endpoint, params)

        # MOCK: Falha da API, retorna MOCK Data
        logger.warning(f"   ⚠️ Usando MOCK DATA para H2H devido a falha da API.")
        return {'h2h_over_1_5_rate': 0.78}
