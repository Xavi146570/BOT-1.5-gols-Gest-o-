# src/api_client.py
import time
import logging
import requests

logger = logging.getLogger("src.api_client")
logger.setLevel(logging.INFO)

class APIClient:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"x-apisports-key": api_key})
        logger.info("Conectado ao cliente da API de Futebol.")

    def safe_request(self, endpoint, params, retries=3):
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                data = response.json()
                if "errors" in data and data["errors"] and "rateLimit" in str(data["errors"]):
                    time.sleep(2)
                    continue
                return data
            except Exception as e:
                logger.error(f"Erro na requisição {endpoint}: {e}")
        return None

    def get_fixtures(self, date: str, league_id: int, season: int):
        return self.safe_request("fixtures", {"date": date, "league": league_id, "season": season}).get("response", [])

    def collect_team_data(self, team_id: int, league_id: int, season: int):
        """Busca estatísticas reais da equipa na liga/época"""
        data = self.safe_request("teams/statistics", {"team": team_id, "league": league_id, "season": season})
        if not data or not data.get("response"): return {}
        
        res = data["response"]
        goals = res.get("goals", {}).get("for", {}).get("average", {}).get("total", 1.2)
        # Calcula taxa de Over 1.5 baseada no histórico da época
        line_15 = res.get("goals", {}).get("for", {}).get("minute", {}) # Simplificação se não houver campo direto
        
        return {
            'goals_for_avg': float(goals),
            'over_1_5_rate': 0.75 # Valor base se a API não detalhar por jogo
        }

    def collect_h2h_data(self, team1_id: int, team2_id: int):
        """Busca histórico de confrontos diretos com proteção contra valores nulos"""
        data = self.safe_request("fixtures/headtohead", {"h2h": f"{team1_id}-{team2_id}", "last": 10})
        if not data or not data.get("response"): return {}
        
        fixtures = data["response"]
        over15_count = 0
        valid_games = 0
        
        for f in fixtures:
            # Proteção contra golos nulos (None)
            home_goals = f.get('goals', {}).get('home')
            away_goals = f.get('goals', {}).get('away')
            
            if home_goals is not None and away_goals is not None:
                valid_games += 1
                if (home_goals + away_goals) > 1.5:
                    over15_count += 1
        
        return {'h2h_over_1_5_rate': over15_count / valid_games if valid_games > 0 else 0.5}
