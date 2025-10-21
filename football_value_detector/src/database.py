"""
Database Manager - Sistema Over 1.5
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)


class Database:
    """Gerencia banco SQLite"""
    
    def __init__(self, db_path: str = "football_value.db"):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"✅ Conectado ao banco: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            raise
    
    def _create_tables(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    league TEXT NOT NULL,
                    match_date TEXT NOT NULL,
                    our_probability REAL NOT NULL,
                    over_1_5_odds REAL NOT NULL,
                    expected_value REAL NOT NULL,
                    bet_quality TEXT NOT NULL,
                    analyzed_at TEXT NOT NULL,
                    UNIQUE(match_id)
                )
            """)
            self.conn.commit()
            logger.info("✅ Tabelas criadas")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    def save_opportunity(self, opportunity: Dict) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO opportunities (
                    match_id, home_team, away_team, league, match_date,
                    our_probability, over_1_5_odds, expected_value,
                    bet_quality, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opportunity['match_id'],
                opportunity['home_team'],
                opportunity['away_team'],
                opportunity['league'],
                opportunity['match_date'],
                opportunity['our_probability'],
                opportunity['over_1_5_odds'],
                opportunity['expected_value'],
                opportunity['bet_quality'],
                opportunity['analyzed_at']
            ))
            self.conn.commit()
            logger.info(f"✅ Oportunidade salva: {opportunity['home_team']} vs {opportunity['away_team']}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar: {e}")
            return False
    
    def get_today_opportunities(self) -> List[Dict]:
        """Retorna oportunidades de hoje"""
        try:
            cursor = self.conn.cursor()
            today = datetime.now().date().isoformat()
            cursor.execute("""
                SELECT * FROM opportunities
                WHERE DATE(match_date) = ?
                ORDER BY expected_value DESC
            """, (today,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar oportunidades: {e}")
            return []
    
    def get_upcoming_opportunities(self, days: int = 3) -> List[Dict]:
        """Retorna oportunidades dos próximos N dias"""
        try:
            cursor = self.conn.cursor()
            start_date = datetime.now().date().isoformat()
            end_date = (datetime.now() + timedelta(days=days)).date().isoformat()
            
            cursor.execute("""
                SELECT * FROM opportunities
                WHERE DATE(match_date) BETWEEN ? AND ?
                ORDER BY match_date ASC, expected_value DESC
            """, (start_date, end_date))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar oportunidades futuras: {e}")
            return []
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """Retorna estatísticas de performance (mock para versão inicial)"""
        try:
            # Retorna estatísticas vazias por enquanto
            # (implementar quando tivermos resultados reais)
            return {
                'period_days': days,
                'total_bets': 0,
                'won_bets': 0,
                'lost_bets': 0,
                'win_rate': 0.0,
                'total_profit_loss': 0.0,
                'total_staked': 0.0,
                'roi': 0.0
            }
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
            return {}
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("✅ Conexão fechada")
