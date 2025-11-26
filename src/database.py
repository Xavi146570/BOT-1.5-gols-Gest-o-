import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class Database:
    """Gerencia banco de dados SQLite"""
    
    def __init__(self, db_path: str = "football_value.db"):
        """
        Inicializa conexão com banco de dados
        
        Args:
            db_path: Caminho do arquivo SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Conecta ao banco de dados"""
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row
            logger.info(f"✅ Conectado ao banco: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")
            raise
    
    def _create_tables(self):
        """Cria tabelas do banco de dados"""
        try:
            cursor = self.conn.cursor()
            
            # Tabela de oportunidades detectadas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    league TEXT NOT NULL,
                    match_date TEXT NOT NULL,
                    
                    our_probability REAL NOT NULL,
                    implied_probability REAL NOT NULL,
                    confidence REAL NOT NULL,
                    
                    over_1_5_odds REAL NOT NULL,
                    edge REAL NOT NULL,
                    expected_value REAL NOT NULL,
                    
                    kelly_stake REAL NOT NULL,
                    recommended_stake REAL NOT NULL,
                    bet_quality TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    
                    probability_breakdown TEXT,
                    
                    analyzed_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(match_id)
                )
            """)
            
            # Tabela de resultados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    
                    home_score INTEGER,
                    away_score INTEGER,
                    total_goals INTEGER,
                    over_1_5_result TEXT,
                    
                    match_date TEXT NOT NULL,
                    result_updated_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(match_id)
                )
            """)
            
            # Tabela de performance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opportunity_id INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    
                    predicted_probability REAL NOT NULL,
                    actual_result TEXT NOT NULL,
                    
                    stake REAL NOT NULL,
                    odds REAL NOT NULL,
                    profit_loss REAL NOT NULL,
                    
                    analyzed_at TEXT NOT NULL,
                    result_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id),
                    UNIQUE(match_id)
                )
            """)
            
            # Índices para performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_opportunities_match_date 
                ON opportunities(match_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_opportunities_quality 
                ON opportunities(bet_quality)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_match_date 
                ON results(match_date)
            """)
            
            self.conn.commit()
            logger.info("✅ Tabelas criadas/verificadas com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    def save_opportunity(self, opportunity: Dict) -> bool:
        """
        Salva oportunidade detectada
        
        Args:
            opportunity: Dict com dados da oportunidade
            
        Returns:
            True se salvo com sucesso
        """
        # Lista de chaves obrigatórias (NOT NULL no SQLite, exceto breakdown)
        required_keys = [
            'match_id', 'home_team', 'away_team', 'league', 'match_date',
            'our_probability', 'implied_probability', 'confidence',
            'over_1_5_odds', 'edge', 'expected_value',
            'kelly_stake', 'recommended_stake', 'bet_quality', 'risk_level',
            'analyzed_at'
        ]
        
        # --- CORREÇÃO: VERIFICAÇÃO DE CHAVES OBRIGATÓRIAS ---
        missing_keys = [key for key in required_keys if key not in opportunity]
        if missing_keys:
            logger.error(f"❌ Erro ao salvar oportunidade: Faltam chaves obrigatórias: {', '.join(missing_keys)}. Oportunidade não salva.")
            # Loga a oportunidade para debug.
            logger.debug(f"Dados recebidos: {opportunity}")
            return False
        # -----------------------------------------------------

        try:
            cursor = self.conn.cursor()
            
            # Monta a tupla de valores a ser inserida
            values = (
                opportunity['match_id'],
                opportunity['home_team'],
                opportunity['away_team'],
                opportunity['league'],
                opportunity['match_date'],
                opportunity['our_probability'],
                opportunity['implied_probability'],
                opportunity['confidence'],
                opportunity['over_1_5_odds'],
                opportunity['edge'],
                opportunity['expected_value'],
                opportunity['kelly_stake'],
                opportunity['recommended_stake'],
                opportunity['bet_quality'],
                opportunity['risk_level'],
                # probability_breakdown é opcional e usa .get() com fallback
                json.dumps(opportunity.get('probability_breakdown', {})),
                opportunity['analyzed_at']
            )

            cursor.execute("""
                INSERT OR REPLACE INTO opportunities (
                    match_id, home_team, away_team, league, match_date,
                    our_probability, implied_probability, confidence,
                    over_1_5_odds, edge, expected_value,
                    kelly_stake, recommended_stake, bet_quality, risk_level,
                    probability_breakdown, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)
            
            self.conn.commit()
            logger.info(f"✅ Oportunidade salva: {opportunity['home_team']} vs {opportunity['away_team']}")
            return True
            
        except Exception as e:
            # Mantém o log de exceção genérica caso seja um erro SQLite ou de tipo
            logger.error(f"❌ Erro ao salvar oportunidade: {e}")
            return False
    
    def get_today_opportunities(self) -> List[Dict]:
        """Retorna oportunidades do dia"""
        try:
            cursor = self.conn.cursor()
            today = datetime.now().date().isoformat()
            
            cursor.execute("""
                SELECT * FROM opportunities
                WHERE DATE(match_date) = ?
                ORDER BY expected_value DESC
            """, (today,))
            
            rows = cursor.fetchall()
            # Converte a coluna probability_breakdown de JSON string para Dict
            return [{**dict(row), 'probability_breakdown': json.loads(row['probability_breakdown']) if row['probability_breakdown'] else {}} for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar oportunidades do dia: {e}")
            return []
    
    def get_upcoming_opportunities(self, days: int = 3) -> List[Dict]:
        """
        Retorna oportunidades dos próximos N dias
        
        Args:
            days: Número de dias à frente
        """
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
            # Converte a coluna probability_breakdown de JSON string para Dict
            return [{**dict(row), 'probability_breakdown': json.loads(row['probability_breakdown']) if row['probability_breakdown'] else {}} for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar oportunidades futuras: {e}")
            return []
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """
        Retorna estatísticas de performance dos últimos N dias
        
        Args:
            days: Período de análise em dias
        """
        try:
            cursor = self.conn.cursor()
            start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            
            # Total de apostas
            cursor.execute("""
                SELECT COUNT(*) as total FROM performance
                WHERE DATE(result_date) >= ?
            """, (start_date,))
            row = cursor.fetchone()
            total_bets = row['total'] if row else 0
            
            # Apostas ganhas
            cursor.execute("""
                SELECT COUNT(*) as won FROM performance
                WHERE DATE(result_date) >= ? AND actual_result = 'WON'
            """, (start_date,))
            row = cursor.fetchone()
            won_bets = row['won'] if row else 0
            
            # Profit/Loss total
            cursor.execute("""
                SELECT SUM(profit_loss) as total_pl FROM performance
                WHERE DATE(result_date) >= ?
            """, (start_date,))
            row = cursor.fetchone()
            total_pl = row['total_pl'] if row and row['total_pl'] else 0
            
            # ROI
            cursor.execute("""
                SELECT SUM(stake) as total_staked FROM performance
                WHERE DATE(result_date) >= ?
            """, (start_date,))
            row = cursor.fetchone()
            total_staked = row['total_staked'] if row and row['total_staked'] else 1
            roi = (total_pl / total_staked) * 100 if total_staked > 0 else 0
            
            # Win rate
            win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
            
            return {
                'period_days': days,
                'total_bets': total_bets,
                'won_bets': won_bets,
                'lost_bets': total_bets - won_bets,
                'win_rate': round(win_rate, 2),
                'total_profit_loss': round(total_pl, 2),
                'total_staked': round(total_staked, 2),
                'roi': round(roi, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
            return {
                'period_days': days,
                'total_bets': 0,
                'won_bets': 0,
                'lost_bets': 0,
                'win_rate': 0,
                'total_profit_loss': 0,
                'total_staked': 0,
                'roi': 0
            }
    
    def clear_old_data(self, days: int = 90):
        """
        Remove dados antigos (mantém últimos N dias)
        
        Args:
            days: Dias de histórico para manter
        """
        try:
            cursor = self.conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            
            # Remove oportunidades antigas
            cursor.execute("""
                DELETE FROM opportunities
                WHERE DATE(match_date) < ?
            """, (cutoff_date,))
            
            deleted_opps = cursor.rowcount
            
            # Remove resultados antigos
            cursor.execute("""
                DELETE FROM results
                WHERE DATE(match_date) < ?
            """, (cutoff_date,))
            
            deleted_results = cursor.rowcount
            
            self.conn.commit()
            logger.info(f"✅ Limpeza concluída: {deleted_opps} oportunidades, {deleted_results} resultados removidos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar dados antigos: {e}")
    
    def close(self):
        """Fecha conexão com banco de dados"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Conexão com banco fechada")
