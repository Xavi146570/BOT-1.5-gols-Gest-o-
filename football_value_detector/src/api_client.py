# src/api_client.py
"""
Cliente para API Football (api-sports.io)
Gerencia requisições com rate limiting e tratamento de erros
"""

import requests
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Assumindo que você definiu TOP_20_LEAGUES em algum lugar que o Analyzer importa.
# Se TOP_20_LEAGUES estiver neste arquivo, defina-a aqui.
# Exemplo (se for necessário aqui):
# TOP_20_LEAGUES = [39, 140, 61, 78, 135, 94, 88, 203, 179, 144, 141, 40, 262, 301, 235, 253, 556, 566, 569, 795]


class FootballAPIClient:
    """Cliente para API Football com rate limiting"""
    
    def __init__(self, api_key: str, base_url: str = 'https://v3.football.api-sports.io'):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'x-apisports-key': api_key
        })
        
        # Rate limiting (450 requests/dia = ~0.31 req/min)
        self.last_request_time = 0
        self.min_request_interval = 2  # 2 segundos entre requests
        
    def _rate_limit(self):
        """Implementa rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limit: Dormindo por {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[List[Dict]]:
        """
        Faz requisição à API com tratamento de erros
        
        Args:
            endpoint: Endpoint da API (ex: '/fixtures')
            params: Parâmetros da query string
            
        Returns:
            Lista de Responses JSON ou None em caso de erro
        """
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errors'):
                logger.error(f"API retornou erros: {data['errors']}")
                return None
            
            return data.get('response', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {endpoint} com params {params}: {e}")
            return None
    
    def get_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Busca dados de um fixture específico"""
        data = self._make_request('/fixtures', params={'id': fixture_id})
        return data[0] if data else None
    
    # --------------------------------------------------------------------------
    # FUNÇÃO CORRIGIDA: Agora espera uma lista e itera sobre ela.
    # --------------------------------------------------------------------------
    def get_fixtures_by_date(self, date: str, leagues: Optional[List[int]] = None) -> List[Dict]:
        """
        Busca fixtures por data e lista de ligas, iterando sobre cada liga.
        
        Args:
            date: Data no formato YYYY-MM-DD
            leagues: Lista de IDs das ligas (opcional)
        """
        all_fixtures = []
        
        if not leagues:
            logger.info(f"Buscando todos os fixtures para {date} sem filtro de liga.")
            params = {'date': date}
            data = self._make_request('/fixtures', params=params)
            return data if data else []
        
        for league_id in leagues:
            params = {'date': date, 'league': league_id, 'season': 2024}
            logger.info(f"Buscando fixtures para {date} | league={league_id}")
            
            data = self._make_request('/fixtures', params=params)
            
            if data:
                all_fixtures.extend(data)
                
        return all_fixtures
    # --------------------------------------------------------------------------
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Optional[Dict]:
        """Busca estatísticas de um time em uma liga/temporada"""
        params = {
            'team': team_id,
            'league': league_id,
            'season': season
        }
        data = self._make_request('/teams/statistics', params=params)
        return data[0] if data else None
    
    # Adicionando um wrapper para o Analyzer usar
    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Optional[Dict]:
        """Wrapper para get_team_statistics usado no Analyzer"""
        return self.get_team_statistics(team_id, league_id, season)

    def collect_h2h_data(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict]:
        """Wrapper para get_h2h usado no Analyzer"""
        return self.get_h2h(team1_id, team2_id, last)
    
    def get_h2h(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict]:
        """Busca histórico de confrontos diretos"""
        params = {
            'h2h': f"{team1_id}-{team2_id}",
            'last': last
        }
        data = self._make_request('/fixtures/headtohead', params=params)
        return data if data else []
    
    def get_odds(self, fixture_id: int, bookmakers: List[str] = None) -> Dict[str, float]:
        """
        Busca odds de um fixture (OVER 0.5 e OVER 1.5) e retorna um dicionário otimizado.
        """
        params = {
            'fixture': fixture_id,
            'bet': 5  # Bet ID 5 = Goals Over/Under
        }
        
        data = self._make_request('/odds', params=params)
        
        if not data:
            return {}
        
        # Simplifica o retorno para um dicionário de odds (Ex: {'over_15_odds': 2.05, 'over_05_odds': 1.10})
        optimized_odds: Dict[str, float] = {}
        
        # Define os alvos de linha de gol que o Analyzer espera
        goal_lines = {
            '0.5': 'over_5_odds', 
            '1.5': 'over_15_odds'
        }

        for fixture_odds in data:
            bookmaker_data = fixture_odds.get('bookmakers', [])
            
            for bookmaker in bookmaker_data:
                bookmaker_name = bookmaker.get('name')
                
                # Se bookmakers for especificado, filtramos. Caso contrário, pegamos o primeiro que tiver dados.
                if bookmakers and bookmaker_name not in bookmakers:
                    continue
                
                for bet in bookmaker.get('bets', []):
                    if bet.get('name') == 'Goals Over/Under':
                        for value in bet.get('values', []):
                            line = value.get('value')
                            odd = float(value.get('odd', 0))

                            if line in goal_lines and odd > 1.0:
                                # Armazena a melhor odd encontrada para esta linha (poderia ser o MAX, mas vamos pegar o primeiro para simplificar)
                                # A chave 'over_X_odds' deve corresponder ao que é esperado no Analyzer
                                if goal_lines[line] not in optimized_odds:
                                    optimized_odds[goal_lines[line]] = odd
                                
                                # Se já encontramos todas as odds necessárias, podemos sair
                                if all(key in optimized_odds for key in goal_lines.values()):
                                    return optimized_odds

                # Sai do loop do bookmaker depois de processar o primeiro (ou o filtrado) para evitar excesso de dados.
                if optimized_odds:
                    return optimized_odds
                    
        return optimized_odds

# --------------------------------------------------------------------------
# FIM DO ARQUIVO src/api_client.py
# --------------------------------------------------------------------------
