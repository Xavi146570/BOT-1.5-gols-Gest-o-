"""
Data Collector - Sistema Over 1.5
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DataCollector:
    """Coleta dados para análise"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Dict:
        """Coleta dados de um time"""
        try:
            stats = self.api_client.get_team_statistics(team_id, league_id, season)
            
            if not stats:
                return {}
            
            fixtures = stats.get('fixtures', {})
            goals = stats.get('goals', {})
            
            played = fixtures.get('played', {}).get('total', 0)
            
            if played == 0:
                return {}
            
            goals_for = goals.get('for', {}).get('total', {}).get('total', 0)
            goals_against = goals.get('against', {}).get('total', {}).get('total', 0)
            
            goals_for_avg = goals_for / played if played > 0 else 0
            goals_against_avg = goals_against / played if played > 0 else 0
            
            total_goals_avg = goals_for_avg + goals_against_avg
            over_1_5_rate = min(total_goals_avg / 3.0, 0.95)
            
            return {
                'goals_for_avg': round(goals_for_avg, 2),
                'goals_against_avg': round(goals_against_avg, 2),
                'over_1_5_rate': round(over_1_5_rate, 2),
                'recent_over_1_5_rate': round(over_1_5_rate, 2),
                'games_played': played,
                'recent_goals_avg': round(goals_for_avg, 2)
            }
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados do time: {e}")
            return {}
    
    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Dict:
        """Coleta dados de confrontos diretos"""
        try:
            h2h_fixtures = self.api_client.get_h2h(team1_id, team2_id)
            
            if not h2h_fixtures:
                return {'matches': []}
            
            matches = []
            for fixture in h2h_fixtures[:10]:
                goals = fixture.get('goals', {})
                home_goals = goals.get('home', 0) or 0
                away_goals = goals.get('away', 0) or 0
                
                matches.append({
                    'total_goals': home_goals + away_goals,
                    'date': fixture.get('fixture', {}).get('date')
                })
            
            return {'matches': matches}
            
        except Exception as e:
            logger.error(f"Erro ao coletar H2H: {e}")
            return {'matches': []}
