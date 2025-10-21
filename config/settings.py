"""
Configurações Centralizadas - Sistema Over 1.5
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configurações do sistema"""
    
    API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
    API_FOOTBALL_BASE_URL = 'https://v3.football.api-sports.io'
    
    TARGET_LEAGUES = [
        39,   # Premier League
        140,  # La Liga
        135,  # Serie A
        78,   # Bundesliga
        61    # Ligue 1
    ]
    
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'football_value.db')
    PORT = int(os.getenv('PORT', 10000))
    REQUESTS_PER_MINUTE = 30
    DELAY_BETWEEN_REQUESTS = 2
