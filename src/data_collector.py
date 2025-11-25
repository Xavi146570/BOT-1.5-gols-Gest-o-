import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Presume-se que o APIClient e o Settings são importados
# from src.api_client import APIClient 
# from config.settings import Settings 

class DataCollector:
    """
    Responsável por orquestrar a coleta de dados brutos e processá-los
    para gerar indicadores que serão usados no cálculo de probabilidades.
    """
    
    def __init__(self, api_client: Any):
        self.client = api_client
        # self.settings = Settings() # Se necessário
        
    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Dict[str, float]:
        """
        Coleta dados brutos de estatísticas de uma equipe e retorna indicadores chave.
        
        Args:
            team_id (int): ID da equipa.
            league_id (int): ID da liga.
            season (int): Temporada atual.
            
        Returns:
            Dict: Dicionário de indicadores processados.
        """
        try:
            # CORREÇÃO: Chama o método com o nome correto que existe no APIClient
            # Este método no APIClient agora inclui o fallback de MOCK DATA em caso de 403
            raw_stats = self.client.collect_team_data(team_id, league_id, season)
            
            if not raw_stats:
                logger.warning(f"Não foi possível obter dados brutos para o time {team_id}. Retornando dados mínimos.")
                return {} # Retorna vazio, o Scheduler irá tratar isto.
            
            # --- Lógica de Processamento de Dados REAIS da API (Substitua pela sua) ---
            
            # Exemplo de processamento (MOCK/Placeholder)
            processed_data = {
                'goals_for_avg': raw_stats.get('goals_for_avg', 1.5),
                'over_1_5_rate': raw_stats.get('over_1_5_rate', 0.70),
                'offensive_score': raw_stats.get('offensive_score', 0.60),
            }
            
            return processed_data
        
        except Exception as e:
            logger.error(f"Erro ao coletar dados do time: {e}")
            return {}

    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Dict[str, float]:
        """
        Coleta dados de confrontos diretos (Head-to-Head) e retorna indicadores chave.
        
        Returns:
            Dict: Dicionário de indicadores H2H processados.
        """
        try:
            # CORREÇÃO: Chama o método com o nome correto que existe no APIClient
            raw_h2h = self.client.collect_h2h_data(team1_id, team2_id)
            
            if not raw_h2h:
                logger.warning(f"Não foi possível obter dados H2H para os times {team1_id}-{team2_id}. Retornando dados mínimos.")
                return {}
            
            # --- Lógica de Processamento de Dados REAIS da API (Substitua pela sua) ---

            processed_data = {
                'h2h_over_1_5_rate': raw_h2h.get('h2h_over_1_5_rate', 0.75)
            }
            
            return processed_data
        
        except Exception as e:
            logger.error(f"Erro ao coletar dados H2H: {e}")
            return {}
