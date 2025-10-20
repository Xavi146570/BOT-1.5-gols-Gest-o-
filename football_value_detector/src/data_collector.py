"""
Data Collector - Coleta e processa dados para análise Over 1.5
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DataCollector:
    """Coleta dados de times, H2H e contexto para análise"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def collect_team_stats(self, home_team_id: int, away_team_id: int,
                          league_id: int, season: int) -> Dict:
        """
        Coleta estatísticas dos times
        
        Returns:
            Dict com dados processados para ambos os times
        """
        logger.info(f"Coletando stats: Home {home_team_id} vs Away {away_team_id}")
        
        # Busca stats dos times
        home_stats = self.api_client.get_team_statistics(home_team_id, league_id, season)
        away_stats = self.api_client.get_team_statistics(away_team_id, league_id, season)
        
        if not home_stats or not away_stats:
            logger.warning("Stats incompletas, usando valores padrão")
            return self._get_default_team_data()
        
        # Processa dados
        team_data = {
            # Médias de gols
            'home_goals_scored_avg': self._safe_float(home_stats, ['goals', 'for', 'average', 'home'], 1.5),
            'home_goals_conceded_avg': self._safe_float(home_stats, ['goals', 'against', 'average', 'home'], 1.5),
            'away_goals_scored_avg': self._safe_float(away_stats, ['goals', 'for', 'average', 'away'], 1.5),
            'away_goals_conceded_avg': self._safe_float(away_stats, ['goals', 'against', 'average', 'away'], 1.5),
            
            # Taxa Over 1.5 (inverso do Under 1.5)
            'home_over_1_5_rate': 1 - self._calculate_under_rate(home_stats, 'home'),
            'away_over_1_5_rate': 1 - self._calculate_under_rate(away_stats, 'away'),
            
            # Força dos times (win rate)
            'home_strength': self._calculate_strength(home_stats, 'home'),
            'away_strength': self._calculate_strength(away_stats, 'away'),
            
            # Jogos recentes (últimos 5)
            'home_recent_goals': self._extract_recent_goals(home_stats, 5),
            'away_recent_goals': self._extract_recent_goals(away_stats, 5),
        }
        
        logger.info(f"Home avg goals: {team_data['home_goals_scored_avg']:.2f} | "
                   f"Away avg goals: {team_data['away_goals_scored_avg']:.2f}")
        
        return team_data
    
    def collect_h2h(self, home_team_id: int, away_team_id: int) -> Dict:
        """Coleta histórico de confrontos diretos"""
        logger.info(f"Coletando H2H: {home_team_id} vs {away_team_id}")
        
        h2h_matches = self.api_client.get_h2h(home_team_id, away_team_id, last=10)
        
        if not h2h_matches:
            logger.warning("Sem dados H2H, usando padrão")
            return {'over_1_5_rate': 0.70, 'avg_goals': 2.5, 'sample_size': 0}
        
        total_goals_list = []
        over_count = 0
        
        for match in h2h_matches:
            home_goals = match.get('goals', {}).get('home', 0)
            away_goals = match.get('goals', {}).get('away', 0)
            total = home_goals + away_goals
            
            total_goals_list.append(total)
            if total > 1:  # Over 1.5
                over_count += 1
        
        over_rate = over_count / len(h2h_matches) if h2h_matches else 0.70
        avg_goals = sum(total_goals_list) / len(total_goals_list) if total_goals_list else 2.5
        
        logger.info(f"H2H: {len(h2h_matches)} jogos | Over 1.5: {over_rate:.1%} | Avg: {avg_goals:.2f} gols")
        
        return {
            'over_1_5_rate': over_rate,
            'avg_goals': avg_goals,
            'sample_size': len(h2h_matches)
        }
    
    def collect_context(self, fixture_data: Dict) -> Dict:
        """Coleta dados contextuais do jogo"""
        try:
            fixture_date = fixture_data['fixture']['date']
            league_round = fixture_data.get('league', {}).get('round', 'Regular Season')
            
            # Extrai rodada (ex: "Regular Season - 15" -> 15)
            round_num = self._extract_round_number(league_round)
            
            context = {
                'date': fixture_date,
                'round': round_num,
                'is_playoff': 'playoff' in league_round.lower() or 'final' in league_round.lower(),
                'season_phase': self._determine_season_phase(round_num)
            }
            
            logger.info(f"Contexto: Rodada {round_num} | Fase: {context['season_phase']}")
            
            return context
            
        except Exception as e:
            logger.error(f"Erro coletando contexto: {e}")
            return {'round': 15, 'is_playoff': False, 'season_phase': 'mid'}
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _safe_float(self, data: Dict, keys: List[str], default: float) -> float:
        """Navega dict de forma segura e retorna float"""
        try:
            value = data
            for key in keys:
                value = value[key]
            return float(value) if value is not None else default
        except (KeyError, TypeError, ValueError):
            return default
    
    def _calculate_under_rate(self, stats: Dict, venue: str) -> float:
        """Calcula taxa de Under 1.5 de um time"""
        try:
            # Tenta extrair de fixtures (se API fornece breakdown)
            fixtures = stats.get('fixtures', {})
            played = fixtures.get('played', {}).get(venue, 0)
            
            if played == 0:
                return 0.30  # Default: 30% Under (70% Over)
            
            # Estima Under baseado em média de gols
            avg_goals = self._safe_float(stats, ['goals', 'for', 'average', venue], 1.5)
            avg_conceded = self._safe_float(stats, ['goals', 'against', 'average', venue], 1.5)
            avg_total = avg_goals + avg_conceded
            
            # Heurística: avg < 1.5 gols → alta chance Under
            if avg_total <= 1.0:
                return 0.60
            elif avg_total <= 1.5:
                return 0.40
            elif avg_total <= 2.0:
                return 0.30
            else:
                return 0.20
            
        except Exception as e:
            logger.warning(f"Erro calculando under rate: {e}")
            return 0.30
    
    def _calculate_strength(self, stats: Dict, venue: str) -> float:
        """Calcula força do time (0-1) baseado em win rate"""
        try:
            fixtures = stats.get('fixtures', {})
            wins = fixtures.get('wins', {}).get(venue, 0)
            played = fixtures.get('played', {}).get(venue, 1)
            
            return wins / played if played > 0 else 0.5
            
        except Exception:
            return 0.5
    
    def _extract_recent_goals(self, stats: Dict, num_games: int = 5) -> List[int]:
        """Extrai gols dos últimos jogos (simplificado)"""
        # API Football não fornece breakdown por jogo em /teams/statistics
        # Usamos média para simular últimos jogos
        try:
            avg = self._safe_float(stats, ['goals', 'for', 'average', 'total'], 1.5)
            # Simula últimos 5 jogos com variação
            return [int(avg)] * num_games
        except Exception:
            return [1, 2, 1, 2, 1]  # Default
    
    def _extract_round_number(self, round_str: str) -> int:
        """Extrai número da rodada de string"""
        try:
            # Ex: "Regular Season - 15" -> 15
            parts = round_str.split('-')
            if len(parts) > 1:
                return int(parts[-1].strip())
            return 15  # Default meio de temporada
        except Exception:
            return 15
    
    def _determine_season_phase(self, round_num: int) -> str:
        """Determina fase da temporada"""
        if round_num <= 10:
            return 'early'
        elif round_num <= 28:
            return 'mid'
        else:
            return 'late'
    
    def _get_default_team_data(self) -> Dict:
        """Retorna dados padrão quando API falha"""
        return {
            'home_goals_scored_avg': 1.5,
            'home_goals_conceded_avg': 1.5,
            'away_goals_scored_avg': 1.5,
            'away_goals_conceded_avg': 1.5,
            'home_over_1_5_rate': 0.70,  # 70% Over 1.5 (padrão)
            'away_over_1_5_rate': 0.70,
            'home_strength': 0.5,
            'away_strength': 0.5,
            'home_recent_goals': [1, 2, 1, 2, 1],
            'away_recent_goals': [1, 2, 1, 2, 1],
        }

