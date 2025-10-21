"""
Telegram Notifier - Sistema Over 1.5
Envia notificações de oportunidades para Telegram
"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Envia notificações via Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Inicializa notificador
        
        Args:
            bot_token: Token do bot do Telegram
            chat_id: ID do chat para enviar mensagens
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)
        
        if self.enabled:
            logger.info("✅ Telegram notificador ativado")
        else:
            logger.warning("⚠️ Telegram desativado (sem token/chat_id)")
    
    def send_message(self, text: str) -> bool:
        """
        Envia mensagem simples
        
        Args:
            text: Texto da mensagem
            
        Returns:
            True se enviado com sucesso
        """
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Mensagem Telegram enviada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Telegram: {e}")
            return False
    
    def notify_opportunity(self, opportunity: Dict) -> bool:
        """
        Notifica nova oportunidade detectada
        
        Args:
            opportunity: Dict com dados da oportunidade
        """
        if not self.enabled:
            return False
        
        try:
            # Formata mensagem
            message = self._format_opportunity_message(opportunity)
            
            # Envia
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Erro ao notificar oportunidade: {e}")
            return False
    
    def notify_daily_summary(self, opportunities: List[Dict], total_analyzed: int) -> bool:
        """
        Envia resumo diário
        
        Args:
            opportunities: Lista de oportunidades encontradas
            total_analyzed: Total de jogos analisados
        """
        if not self.enabled:
            return False
        
        try:
            message = self._format_daily_summary(opportunities, total_analyzed)
            return self.send_message(message)
        except Exception as e:
            logger.error(f"❌ Erro ao enviar resumo: {e}")
            return False
    
    def _format_opportunity_message(self, opp: Dict) -> str:
        """Formata mensagem de oportunidade"""
        
        # Emoji baseado na qualidade
        quality_emoji = {
            'EXCELENTE': '🔥',
            'MUITO BOA': '⭐',
            'BOA': '✅',
            'REGULAR': '📊'
        }
        emoji = quality_emoji.get(opp['bet_quality'], '📊')
        
        # Formata mensagem
        message = f"""
{emoji} <b>OPORTUNIDADE DETECTADA!</b> {emoji}

⚽ <b>{opp['home_team']} vs {opp['away_team']}</b>
🏆 {opp['league']}
📅 {self._format_date(opp['match_date'])}

📊 <b>ANÁLISE:</b>
• Probabilidade Over 1.5: <b>{opp['our_probability']*100:.1f}%</b>
• Odds: <b>{opp['over_1_5_odds']:.2f}</b>
• Expected Value: <b>{opp['expected_value']*100:+.1f}%</b>
• Confiança: <b>{opp['confidence']:.0f}%</b>

💰 <b>RECOMENDAÇÃO:</b>
• Stake: <b>{opp['recommended_stake']:.1f}% do bankroll</b>
• Qualidade: <b>{opp['bet_quality']}</b>
• Risco: <b>{opp['risk_level']}</b>

🎯 Aposte em: <b>OVER 1.5 GOLS</b>
"""
        return message.strip()
    
    def _format_daily_summary(self, opportunities: List[Dict], total: int) -> str:
        """Formata resumo diário"""
        
        count = len(opportunities)
        
        if count == 0:
            message = f"""
📊 <b>RESUMO DIÁRIO</b>

🔍 Jogos analisados: <b>{total}</b>
🎯 Oportunidades encontradas: <b>0</b>

⚠️ Nenhuma oportunidade com valor detectada hoje.
"""
        else:
            message = f"""
📊 <b>RESUMO DIÁRIO</b>

🔍 Jogos analisados: <b>{total}</b>
🎯 Oportunidades encontradas: <b>{count}</b>

"""
            # Adiciona top 3 oportunidades
            top_3 = sorted(opportunities, key=lambda x: x['expected_value'], reverse=True)[:3]
            
            for i, opp in enumerate(top_3, 1):
                emoji = '🔥' if i == 1 else '⭐' if i == 2 else '✅'
                message += f"""
{emoji} <b>#{i} - {opp['home_team']} vs {opp['away_team']}</b>
   EV: {opp['expected_value']*100:+.1f}% | Odds: {opp['over_1_5_odds']:.2f} | {opp['bet_quality']}

"""
        
        return message.strip()
    
    def _format_date(self, date_str: str) -> str:
        """Formata data para exibição"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return date_str
    
    def test_connection(self) -> bool:
        """Testa conexão com Telegram"""
        if not self.enabled:
            logger.warning("⚠️ Telegram não configurado")
            return False
        
        try:
            message = "🤖 <b>Football Value Detector</b>\n\n✅ Sistema iniciado com sucesso!"
            return self.send_message(message)
        except Exception as e:
            logger.error(f"❌ Erro ao testar Telegram: {e}")
            return False
