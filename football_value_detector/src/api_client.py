"""
Cliente para API Football (api-sports.io)
Gerencia requisições com rate limiting e tratamento de erros
"""

import requests
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Faz requisição à API com tratamento de erros
        
        Args:
            endpoint: Endpoint da API (ex: '/fixtures')
            params: Parâmetros da query string
            
        Returns:
            Response JSON ou None em caso de erro
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
            logger.error(f"Erro na requisição para {endpoint}: {e}")
            return None
    
    def get_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Busca dados de um fixture específico"""
        data = self._make_request('/fixtures', params={'id': fixture_id})
        return data[0] if data else None
    
    def get_fixtures_by_date(self, date: str, league_id: int = None) -> List[Dict]:
        """
        Busca fixtures por data
        
        Args:
            date: Data no formato YYYY-MM-DD
            league_id: ID da liga (opcional)
        """
        params = {'date': date}
        if league_id:
            params['league'] = league_id
        
        data = self._make_request('/fixtures', params=params)
        return data if data else []
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Optional[Dict]:
        """Busca estatísticas de um time em uma liga/temporada"""
        params = {
            'team': team_id,
            'league': league_id,
            'season': season
        }
        data = self._make_request('/teams/statistics', params=params)
        return data[0] if data else None
    
    def get_h2h(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict]:
        """Busca histórico de confrontos diretos"""
        params = {
            'h2h': f"{team1_id}-{team2_id}",
            'last': last
        }
        data = self._make_request('/fixtures/headtohead', params=params)
        return data if data else []
    
    def get_odds(self, fixture_id: int, bookmakers: List[str] = None) -> List[Dict]:
        """
        Busca odds de um fixture (OVER 1.5)
        
        Args:
            fixture_id: ID do jogo
            bookmakers: Lista de bookmakers (ex: ['Bet365', '1xBet'])
            
        Returns:
            Lista com odds de cada bookmaker
        """
        params = {
            'fixture': fixture_id,
            'bet': 5  # Bet ID 5 = Goals Over/Under
        }
        
        data = self._make_request('/odds', params=params)
        
        if not data:
            return []
        
        odds_list = []
        
        for fixture_odds in data:
            bookmaker_data = fixture_odds.get('bookmakers', [])
            
            for bookmaker in bookmaker_data:
                bookmaker_name = bookmaker.get('name')
                
                # Filtra bookmakers se especificado
                if bookmakers and bookmaker_name not in bookmakers:
                    continue
                
                # Busca odds para Over/Under 1.5
                for bet in bookmaker.get('bets', []):
                    if bet.get('name') == 'Goals Over/Under':
                        for value in bet.get('values', []):
                            if value.get('value') == '1.5':
                                odds_list.append({
                                    'bookmaker': bookmaker_name,
                                    'over_odds': float(value.get('odd', 0)),
                                    'under_odds': None  # API não retorna under na mesma estrutura
                                })
                            elif value.get('value') == 'Under 1.5':
                                # Pega Under 1.5 se vier separado
                                if odds_list and odds_list[-1]['bookmaker'] == bookmaker_name:
                                    odds_list[-1]['under_odds'] = float(value.get('odd', 0))
        
        # Garante que temos both sides (over e under)
        # Para Over/Under, se temos um lado, calculamos o outro
        for odds in odds_list:
            if odds['over_odds'] and not odds['under_odds']:
                # Estima under baseado em over (simplificado)
                # Odds<span class="cursor">█</span>
