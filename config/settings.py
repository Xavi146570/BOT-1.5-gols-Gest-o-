"""
Settings - Configurações centralizadas do sistema
"""

import os
from dotenv import load_dotenv


class Settings:
    """Configurações do sistema"""
    
    def __init__(self):
        """Carrega configurações de variáveis de ambiente"""
        load_dotenv()
        
        # API Football
        self.API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
        if not self.API_FOOTBALL_KEY:
            raise ValueError("API_FOOTBALL_KEY não configurada")
        
        # Database
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'football_value.db')
        
        # Ligas para análise (IDs da API-Football)
        # ✅ CONFIGURAÇÃO IDEAL: 10 LIGAS
        self.TARGET_LEAGUES = [
            # === TOP 5 LIGAS EUROPEIAS ===
            39,   # 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Inglaterra)
            140,  # 🇪🇸 La Liga (Espanha)
            135,  # 🇮🇹 Serie A (Itália)
            78,   # 🇩🇪 Bundesliga (Alemanha)
            61,   # 🇫🇷 Ligue 1 (França)
            
            # === COMPETIÇÕES UEFA ===
            2,    # ⚽ UEFA Champions League
            3,    # ⚽ UEFA Europa League
            
            # === SEGUNDA DIVISÃO (Alto Volume) ===
            40,   # 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (Inglaterra - 2ª Divisão)
            
            # === OUTRAS LIGAS EUROPEIAS OFENSIVAS ===
            94,   # 🇵🇹 Primeira Liga (Portugal)
            88    # 🇳🇱 Eredivisie (Holanda)
        ]
        
        # Rate limiting
        self.REQUESTS_PER_DAY = 100
        self.REQUEST_DELAY = 2  # segundos entre requisições
        
        # Telegram
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        self.TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true'
