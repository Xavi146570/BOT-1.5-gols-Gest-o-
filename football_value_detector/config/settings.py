"""
Configurações centralizadas do sistema
"""

import os
from typing import List


class Config:
    """Classe de configuração principal"""
    
    # API Football
    API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
    API_FOOTBALL_BASE_URL = 'https://v3.football.api-sports.io'
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/football_value.db')
    
    # Value Detection - OVER 1.5
    MIN_EV_THRESHOLD = float(os.getenv('MIN_EV_THRESHOLD', '0.05'))
    MIN_CONFIDENCE_SCORE = float(os.getenv('MIN_CONFIDENCE_SCORE', '60'))
    
    # Ligas prioritárias
    PRIORITY_LEAGUES_STR = os.getenv('PRIORITY_LEAGUES', '39,140,135,78,61')
    PRIORITY_LEAGUES: List[int] = [int(x.strip()) for x in PRIORITY_LEAGUES_STR.split(',') if x.strip()]
    
    # Rate Limiting
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', '450'))
    API_REQUESTS_PER_MINUTE = API_RATE_LIMIT / (24 * 60)
    
    # Bookmakers
    PRIORITY_BOOKMAKERS = ['Bet365', '1xBet', 'Betfair', 'William Hill', 'Pinnacle']
    
    @classmethod
    def validate(cls):
        """Valida configurações essenciais"""
        errors = []
        
        if not cls.API_FOOTBALL_KEY:
            errors.append("API_FOOTBALL_KEY não configurada")
        
        if cls.MIN_EV_THRESHOLD < 0 or cls.MIN_EV_THRESHOLD > 1:
            errors.append("MIN_EV_THRESHOLD deve estar entre 0 e 1")
        
        if not cls.PRIORITY_LEAGUES:
            errors.append("PRIORITY_LEAGUES não configurada")
        
        if errors:
            raise ValueError(f"Erros de configuração: {', '.join(errors)}")
        
        return True
