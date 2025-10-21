"""
Telegram Notifier - Sistema Over 1.5
Envia notificações de oportunidades detectadas via Telegram
"""

import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Gerencia notificações via Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Inicializa notificador Telegram
        
        Args:
            bot_token: Token do bot Telegram
            chat_id: ID do chat/grupo para enviar mensagens
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Testa conexão
        if self._test_connection():
            logger.info("✅ Telegram conectado com sucesso")
        else:
            logger.warning("⚠️ Falha ao conectar com Telegram")
    
    def _test_connection(self) -> bool:
        """Testa conexão com Telegram"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao testar Telegram: {e}")
            return False
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envia mensagem para o Telegram
        
        Args:
            text: Texto da mensagem
            parse_mode: Modo de formatação (HTML ou Markdown)
            
        Returns:
            True se enviado com sucesso
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Mensagem Telegram enviada")
                return True
            else:
                logger.error(f"❌ Erro ao enviar Telegram: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exceção ao enviar Telegram: {e}")
            return False
    
    def notify_opportunity(self, opportunity: Dict) -> bool:
        """
        Notifica uma única oportunidade detectada
        
        Args:
            opportunity: Dict com dados da oportunidade
        """
        try:
            # Emojis para qualidade
            quality_emoji = {
                'EXCELENTE': '🌟',
                'MUITO BOA': '⭐',
                'BOA': '✅',
                'REGULAR': '🟡',
                'FRACA': '⚪'
            }
            
            emoji = quality_emoji.get(opportunity['bet_quality'], '⚽')
            
            message = f"""
{emoji} <b>OPORTUNIDADE DETECTADA!</b>

⚽ <b>{opportunity['home_team']} vs {opportunity['away_team']}</b>
🏆 Liga: {opportunity['league']}
📅 Data: {opportunity['match_date'][:16].replace('T', ' ')}

📊 <b>ANÁLISE:</b>
• Probabilidade: <b>{opportunity['our_probability']*100:.1f}%</b>
• Odds Over 1.5: <b>{opportunity['over_1_5_odds']:.2f}</b>
• Expected Value: <b>{opportunity['expected_value']*100:+.1f}%</b>

💰 <b>RECOMENDAÇÃO:</b>
• Stake: <b>{opportunity['recommended_stake']:.1f}%</b> do bankroll
• Qualidade: <b>{opportunity['bet_quality']}</b>
• Risco: <b>{opportunity['risk_level']}</b>
• Confiança: <b>{opportunity['confidence']:.0f}%</b>

🔢 Edge: {opportunity['edge']*100:+.1f}%
            """.strip()
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Erro ao notificar oportunidade: {e}")
            return False
    
    def notify_daily_summary(self, opportunities: List[Dict], total_matches: int) -> bool:
        """
        Envia resumo diário da análise
        
        Args:
            opportunities: Lista de oportunidades detectadas
            total_matches: Total de jogos analisados
        """
        try:
            if not opportunities:
                message = f"""
📊 <b>RESUMO DIÁRIO - Over 1.5</b>

🔍 Jogos analisados: <b>{total_matches}</b>
❌ Nenhuma oportunidade com valor detectada hoje

Critérios aplicados:
• Probabilidade ≥ 65%
• Confiança ≥ 60%
• EV ≥ +5%
                """.strip()
            else:
                # Estatísticas
                avg_ev = sum(o['expected_value'] for o in opportunities) / len(opportunities)
                avg_prob = sum(o['our_probability'] for o in opportunities) / len(opportunities)
                total_stake = sum(o['recommended_stake'] for o in opportunities)
                
                # Distribuição por qualidade
                quality_dist = {}
                for opp in opportunities:
                    q = opp['bet_quality']
                    quality_dist[q] = quality_dist.get(q, 0) + 1
                
                quality_text = '\n'.join(
                    f"  • {q}: {count}x"
                    for q, count in sorted(quality_dist.items())
                )
                
                message = f"""
🎯 <b>RESUMO DIÁRIO - Over 1.5</b>

🔍 Jogos analisados: <b>{total_matches}</b>
✅ Oportunidades detectadas: <b>{len(opportunities)}</b>

📊 <b>ESTATÍSTICAS:</b>
• EV Médio: <b>{avg_ev*100:+.1f}%</b>
• Prob. Média: <b>{avg_prob*100:.1f}%</b>
• Stake Total: <b>{total_stake:.1f}%</b>

🏆 <b>DISTRIBUIÇÃO:</b>
{quality_text}

💡 Detalhes de cada jogo foram enviados acima.
                """.strip()
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Erro ao enviar resumo diário: {e}")
            return False
    
    def notify_analysis_start(self, total_matches: int) -> bool:
        """Notifica início da análise diária"""
        message = f"""
🚀 <b>INICIANDO ANÁLISE DIÁRIA</b>

🔍 {total_matches} jogos encontrados para análise
⏳ Processando...
        """.strip()
        
        return self.send_message(message)
    
    def notify_error(self, error_message: str) -> bool:
        """Notifica erro no sistema"""
        message = f"""
⚠️ <b>ERRO NO SISTEMA</b>

❌ {error_message}

Por favor, verifique os logs.
        """.strip()
        
        return self.send_message(message)
