# src/database.py
import sqlite3
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("src.database")
logger.setLevel(logging.INFO)
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

DB_FILE = "football_value.db"

CREATE_OPPORTUNITIES = """
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_id INTEGER,
    team1 TEXT,
    team2 TEXT,
    league TEXT,
    market TEXT,
    prob REAL,
    odds REAL,
    ev REAL,
    confidence REAL,
    kelly REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class Database:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()
        logger.info(f"✅ Conectado ao banco: {self.db_path}")

    def _ensure_schema(self):
        cur = self.conn.cursor()
        cur.execute(CREATE_OPPORTUNITIES)
        self.conn.commit()
        logger.info("✅ Tabelas criadas/verificadas com sucesso")

    def save_opportunity(self, fixture_id: int, team1: str, team2: str, league: str,
                         market: str, prob: float, odds: float, ev: float, confidence: float, kelly: float):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO opportunities
            (fixture_id, team1, team2, league, market, prob, odds, ev, confidence, kelly)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fixture_id, team1, team2, league, market, prob, odds, ev, confidence, kelly))
        self.conn.commit()
        logger.info(f"✅ Oportunidade salva: {team1} vs {team2}")

    def list_opportunities(self, limit: int = 100) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM opportunities ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self.conn.close()
