"""
API Client - Sistema Over 1.5
"""

import logging
import time
import requests
from typing import Dict, List

logger = logging.getLogger(__name__)


class APIClient:
    """Cliente para API-Football"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://v3.football.api-sports.io'
        self.headers = {'x-apisports-key': api_key}
        self.last_request_time = 0
        self.min_delay = 2
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        self._rate_limit()
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro na requisição: {e}")
            return {}
    
    def get_fixtures_by_date(self, date: str, league_id: int) -> List[Dict]:
        try:
            data = self._make_request('fixtures', {'date': date, 'league': league_id})
            return data.get('response', [])
        except Exception as e:
            logger.error(f"Erro ao buscar fixtures: {e}")
            return []
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Dict:
        try:
            data = self._make_request('teams/statistics', {
                'team': team_id,
                'league': league_id,
                'season': season
            })
            return data.get('response', {})
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {}
    
    def get_h2h(self, team1_id: int, team2_id: int) -> List[Dict]:
        try:
            data = self._make_request('fixtures/headtohead', {
                'h2h': f"{team1_id}-{team2_id}",
                'last': 10
            })
            return data.get('response', [])
        except Exception as e:
            logger.error(f"Erro ao buscar H2H: {e}")
            return []
    
    def get_odds(self, fixture_id: int) -> Dict:
        try:
            data = self._make_request('odds', {'fixture': fixture_id, 'bet': 5})
            
            if not data.get('response'):
                return {}
            
            for bookmaker in data['response'][0].get('bookmakers', []):
                for bet in bookmaker.get('bets', []):
                    if bet.get('name') == 'Goals Over/Under':
                        for value in bet.get('values', []):
                            if value.get('value') == 'Over 1.5':
                                return {'over_1_5_odds': float(value.get('odd'))}
            return {}
        except Exception as e:
            logger.error(f"Erro ao buscar odds: {e}")
            return {}
