"""
Database Manager - Sistema Over 1.5
Gerencia armazenamento de jogos, análises e oportunidades em SQLite
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

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
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO opportunities (
                    match_id, home_team, away_team, league, match_date,
                    our_probability, implied_probability, confidence,
                    over_1_5_odds, edge, expected_value,
                    kelly_stake, recommended_stake, bet_quality, risk_level,
                    probability_breakdown, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                json.dumps(opportunity.get('probability_breakdown', {})),
                opportunity['analyzed_at']
            ))
            
            self.conn.commit()
            logger.info(f"✅ Oportunidade salva: {opportunity['home_team']} vs {opportunity['away_team']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar oportunidade: {e}")
            return False
    
    def save_result(self, result: Dict) -> bool:
        """
        Salva resultado de um jogo
        
        Args:
            result: Dict com dados do resultado
            
        Returns:
            True se salvo com sucesso
        """
        try:
            cursor = self.conn.cursor()
            
            total_goals = result['home_score'] + result['away_score']
            over_1_5_result = 'WON' if total_goals >= 2 else 'LOST'
            
            cursor.execute("""
                INSERT OR REPLACE INTO results (
                    match_id, home_team, away_team,
                    home_score, away_score, total_goals, over_1_5_result,
                    match_date, result_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result['match_id'],
                result['home_team'],
                result['away_team'],
                result['home_score'],
                result['away_score'],
                total_goals,
                over_1_5_result,
                result['match_date'],
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            logger.info(f"✅ Resultado salvo: {result['home_team']} {result['home_score']}-{result['away_score']} {result['away_team']}")
            
            # Atualiza performance se houver oportunidade correspondente
            self._update_performance(result['match_id'], over_1_5_result)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultado: {e}")
            return False
    
    def _update_performance(self, match_id: int, result: str):
        """Atualiza tabela de performance quando resultado é conhecido"""
        try:
            cursor = self.conn.cursor()
            
            # Busca oportunidade correspondente
            cursor.execute("""
                SELECT id, our_probability, kelly_stake, over_1_5_odds, 
                       analyzed_at, match_date
                FROM opportunities
                WHERE match_id = ?
            """, (match_id,))
            
            opp = cursor.fetchone()
            if not opp:
                return
            
            # Calcula P&L
            stake = opp['kelly_stake']
            odds = opp['over_1_5_odds']
            
            if result == 'WON':
                profit_loss = stake * (odds - 1)
            else:
                profit_loss = -stake
            
            # Salva performance
            cursor.execute("""
                INSERT OR REPLACE INTO performance (
                    opportunity_id, match_id, predicted_probability,
                    actual_result, stake, odds, profit_loss,
                    analyzed_at, result_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opp['id'],
                match_id,
                opp['our_probability'],
                result,
                stake,
                odds,
                profit_loss,
                opp['analyzed_at'],
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            logger.info(f"✅ Performance atualizada: Match {match_id} - {result} - P&L: {profit_loss:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar performance: {e}")
    
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
            return [dict(row) for row in rows]
            
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
            return [dict(row) for row in rows]
            
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
            total_bets = cursor.fetchone()['total']
            
            # Apostas ganhas
            cursor.execute("""
                SELECT COUNT(*) as won FROM performance
                WHERE DATE(result_date) >= ? AND actual_result = 'WON'
            """, (start_date,))
            won_bets = cursor.fetchone()['won']
            
            # Profit/Loss total
            cursor.execute("""
                SELECT SUM(profit_loss) as total_pl FROM performance
                WHERE DATE(result_date) >= ?
            """, (start_date,))
            total_pl = cursor.fetchone()['total_pl'] or 0
            
            # ROI
            cursor.execute("""
                SELECT SUM(stake) as total_staked FROM performance
                WHERE DATE(result_date) >= ?
            """, (start_date,))
            total_staked = cursor.fetchone()['total_staked'] or 1
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
            return {}
    
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

