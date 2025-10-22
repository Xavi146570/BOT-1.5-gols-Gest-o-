"""
API Client - Football API
Cliente para comunicação com API-Football
"""

import logging
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class APIClient:
    """Cliente para API-Football"""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str):
        """
        Inicializa cliente da API
        
        Args:
            api_key: Chave da API Football
        """
        self.api_key = api_key
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': api_key
        }
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 segundo entre requests
    
    def _rate_limit(self):
        """Aplica rate limiting entre requisições"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Faz requisição para a API
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            
        Returns:
            Resposta da API
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errors'):
                logger.error(f"Erro na API: {data['errors']}")
                return {'response': []}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição: {e}")
            return {'response': []}
    
    def _get_current_season(self, date_str: str) -> int:
        """
        Determina a temporada correta baseada na data
        
        Temporadas de futebol vão de agosto a junho:
        - Agosto-Dezembro 2024 = temporada 2024
        - Janeiro-Junho 2025 = temporada 2024
        - Julho-Dezembro 2025 = temporada 2025
        
        Args:
            date_str: Data no formato YYYY-MM-DD
            
        Returns:
            Ano da temporada
        """
        try:
            year = int(date_str.split('-')[0])
            month = int(date_str.split('-')[1])
            
            # Se mês é jan-jun, temporada é ano anterior
            if month <= 6:
                return year - 1
            # Se mês é jul-dez, temporada é ano atual
            else:
                return year
                
        except Exception as e:
            logger.error(f"Erro ao determinar temporada: {e}")
            # Fallback: usa ano atual - 1 se antes de julho
            current_date = datetime.now()
            if current_date.month <= 6:
                return current_date.year - 1
            return current_date.year
    
    def get_fixtures_by_date(
        self,
        date: str,
        league_id: Optional[int] = None,
        season: Optional[int] = None
    ) -> List[Dict]:
        """
        Busca jogos por data
        
        Args:
            date: Data no formato YYYY-MM-DD
            league_id: ID da liga (opcional)
            season: Temporada (opcional, será calculada automaticamente)
            
        Returns:
            Lista de jogos
        """
        # Determina temporada automaticamente se não fornecida
        if season is None:
            season = self._get_current_season(date)
        
        params = {
            'date': date,
            'timezone': 'UTC'
        }
        
        if league_id:
            params['league'] = league_id
            params['season'] = season
        
        logger.debug(f"Buscando jogos: date={date}, league={league_id}, season={season}")
        
        data = self._make_request('fixtures', params)
        fixtures = data.get('response', [])
        
        logger.debug(f"API retornou {len(fixtures)} jogos")
        
        return fixtures
    
    def get_team_statistics(
        self,
        team_id: int,
        league_id: int,
        season: int
    ) -> Optional[Dict]:
        """
        Busca estatísticas de um time
        
        Args:
            team_id: ID do time
            league_id: ID da liga
            season: Temporada
            
        Returns:
            Estatísticas do time
        """
        params = {
            'team': team_id,
            'league': league_id,
            'season': season
        }
        
        data = self._make_request('teams/statistics', params)
        
        if data.get('response'):
            return data['response']
        
        return None
    
    def get_h2h(
        self,
        team1_id: int,
        team2_id: int,
        last: int = 10
    ) -> List[Dict]:
        """
        Busca histórico de confrontos diretos
        
        Args:
            team1_id: ID do primeiro time
            team2_id: ID do segundo time
            last: Número de jogos a buscar
            
        Returns:
            Lista de confrontos
        """
        params = {
            'h2h': f"{team1_id}-{team2_id}",
            'last': last
        }
        
        data = self._make_request('fixtures/headtohead', params)
        return data.get('response', [])
    
    def get_odds(self, fixture_id: int) -> Optional[Dict]:
        """
        Busca odds de um jogo
        
        Args:
            fixture_id: ID do jogo
            
        Returns:
            Dict com odds Over/Under 1.5
        """
        params = {
            'fixture': fixture_id,
            'bet': 5  # Bet ID 5 = Goals Over/Under
        }
        
        data = self._make_request('odds', params)
        
        if not data.get('response'):
            logger.debug(f"Sem odds para fixture {fixture_id}")
            return None
        
        try:
            # Procura pelas odds Over/Under 1.5
            for response in data['response']:
                for bookmaker in response.get('bookmakers', []):
                    for bet in bookmaker.get('bets', []):
                        if bet.get('name') == 'Goals Over/Under':
                            for value in bet.get('values', []):
                                # Procura especificamente por Over 1.5
                                if value.get('value') == 'Over 1.5':
                                    over_odds = float(value.get('odd', 0))
                                    if over_odds > 0:
                                        logger.debug(f"Odds Over 1.5 encontrada: {over_odds}")
                                        return {
                                            'over_1_5_odds': over_odds,
                                            'bookmaker': bookmaker.get('name')
                                        }
            
            logger.debug(f"Odds Over 1.5 não encontrada para fixture {fixture_id}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao processar odds: {e}")
            return None
