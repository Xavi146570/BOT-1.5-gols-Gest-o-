"""
Configurações Centralizadas - Sistema Over 1.5
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configurações do sistema"""
    
    # API Football
    API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
    API_FOOTBALL_BASE_URL = 'https://v3.football.api-sports.io'
    
    # Ligas para análise
    TARGET_LEAGUES = [
        39,   # Premier League
        140,  # La Liga
        135,  # Serie A
        78,   # Bundesliga
        61    # Ligue 1
    ]
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'football_value.db')
    
    # Flask
    PORT = int(os.getenv('PORT', 10000))
    
    # Rate Limiting
    REQUESTS_PER_MINUTE = 30
    DELAY_BETWEEN_REQUESTS = 2
    
     # Telegram
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        self.TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true'
