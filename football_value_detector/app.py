"""
Flask Web Application - Sistema Over 1.5
Interface web para visualizar oportunidades e estatísticas
"""

import logging
from flask import Flask, render_template_string, jsonify
from datetime import datetime, timedelta
import os

from config.settings import Settings
from src.database import Database

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa Flask
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Inicializa componentes
settings = Settings()
db = Database()


# ==================== ROTAS HTML ====================

@app.route('/')
def index():
    """Página inicial com dashboard"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/health')
def health():
    """Health check para Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Football Value Detector Over 1.5'
    })


# ==================== ROTAS API ====================

@app.route('/api/opportunities/today')
def api_today_opportunities():
    """Retorna oportunidades do dia"""
    try:
        opportunities = db.get_today_opportunities()
        
        return jsonify({
            'success': True,
            'count': len(opportunities),
            'opportunities': opportunities,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades do dia: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/opportunities/upcoming')
def api_upcoming_opportunities():
    """Retorna oportunidades dos próximos 3 dias"""
    try:
        opportunities = db.get_upcoming_opportunities(days=3)
        
        return jsonify({
            'success': True,
            'count': len(opportunities),
            'opportunities': opportunities,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades futuras: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats/performance')
def api_performance_stats():
    """Retorna estatísticas de performance"""
    try:
        stats_7d = db.get_performance_stats(days=7)
        stats_30d = db.get_performance_stats(days=30)
        
        return jsonify({
            'success': True,
            'last_7_days': stats_7d,
            'last_30_days': stats_30d,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== TEMPLATE HTML ====================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Football Value Detector - Over 1.5</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.2em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            color: #333;
            font-size: 2.5em;
            font-weight: bold;
        }
        
        .stat-value.positive {
            color: #10b981;
        }
        
        .stat-value.negative {
            color: #ef4444;
        }
        
        .opportunities-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .section-title {
            color: #333;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .opportunity-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
            transition: transform 0.2s;
        }
        
        .opportunity-card:hover {
            transform: translateX(5px);
        }
        
        .match-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .teams {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        .league {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .match-date {
            color: #667eea;
            font-weight: bold;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .metric {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 8px;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.8em;
            margin-bottom: 5px;
        }
        
        .metric-value {
            color: #333;
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .quality-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .quality-EXCELENTE {
            background: #10b981;
            color: white;
        }
        
        .quality-MUITO_BOA {
            background: #3b82f6;
            color: white;
        }
        
        .quality-BOA {
            background: #8b5cf6;
            color: white;
        }
        
        .quality-REGULAR {
            background: #f59e0b;
            color: white;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.2em;
        }
        
        .error {
            background: #fee;
            color: #c00;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .empty {
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.1em;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            margin: 20px auto;
            display: block;
            transition: background 0.3s;
        }
        
        .refresh-btn:hover {
            background: #764ba2;
        }
        
        footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚽ Football Value Detector</h1>
            <p class="subtitle">Sistema de Detecção de Valor em Apostas Over 1.5</p>
        </header>
        
        <div class="stats-grid" id="statsGrid">
            <div class="loading">Carregando estatísticas...</div>
        </div>
        
        <div class="opportunities-section">
            <h2 class="section-title">📊 Oportunidades de Hoje</h2>
            <button class="refresh-btn" onclick="loadData()">🔄 Atualizar Dados</button>
            <div id="todayOpportunities">
                <div class="loading">Carregando oportunidades...</div>
            </div>
        </div>
        
        <div class="opportunities-section">
            <h2 class="section-title">📅 Próximos 3 Dias</h2>
            <div id="upcomingOpportunities">
                <div class="loading">Carregando oportunidades...</div>
            </div>
        </div>
        
        <footer>
            <p>🚀 Powered by Football Value Detector | Over 1.5 Goals System</p>
            <p>Última atualização: <span id="lastUpdate"></span></p>
        </footer>
    </div>
    
    <script>
        function formatDate(dateStr) {
            const date = new Date(dateStr);
            return date.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        function formatPercent(value) {
            return (value * 100).toFixed(1) + '%';
        }
        
        function renderStats(data) {
            const stats = data.last_7_days;
            const html = `
                <div class="stat-card">
                    <div class="stat-label">Total de Apostas (7d)</div>
                    <div class="stat-value">${stats.total_bets || 0}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Win Rate (7d)</div>
                    <div class="stat-value ${stats.win_rate >= 70 ? 'positive' : ''}">${stats.win_rate || 0}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">ROI (7d)</div>
                    <div class="stat-value ${stats.roi > 0 ? 'positive' : 'negative'}">${stats.roi || 0}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Profit/Loss (7d)</div>
                    <div class="stat-value ${stats.total_profit_loss > 0 ? 'positive' : 'negative'}">
                        ${stats.total_profit_loss > 0 ? '+' : ''}${(stats.total_profit_loss || 0).toFixed(2)}u
                    </div>
                </div>
            `;
            document.getElementById('statsGrid').innerHTML = html;
        }
        
        function renderOpportunity(opp) {
            return `
                <div class="opportunity-card">
                    <div class="match-info">
                        <div>
                            <div class="teams">${opp.home_team} vs ${opp.away_team}</div>
                            <div class="league">${opp.league}</div>
                            <span class="quality-badge quality-${opp.bet_quality.replace(' ', '_')}">${opp.bet_quality}</span>
                        </div>
                        <div class="match-date">${formatDate(opp.match_date)}</div>
                    </div>
                    
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-label">Probabilidade</div>
                            <div class="metric-value">${formatPercent(opp.our_probability)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Odds Over 1.5</div>
                            <div class="metric-value">${opp.over_1_5_odds.toFixed(2)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Expected Value</div>
                            <div class="metric-value" style="color: #10b981">${formatPercent(opp.expected_value)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Stake Recomendado</div>
                            <div class="metric-value">${opp.recommended_stake.toFixed(1)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Confiança</div>
                            <div class="metric-value">${opp.confidence.toFixed(0)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Risco</div>
                            <div class="metric-value">${opp.risk_level}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        async function loadData() {
            try {
                // Carrega estatísticas
                const statsRes = await fetch('/api/stats/performance');
                const statsData = await statsRes.json();
                if (statsData.success) {
                    renderStats(statsData);
                }
                
                // Carrega oportunidades de hoje
                const todayRes = await fetch('/api/opportunities/today');
                const todayData = await todayRes.json();
                if (todayData.success) {
                    const container = document.getElementById('todayOpportunities');
                    if (todayData.count === 0) {
                        container.innerHTML = '<div class="empty">Nenhuma oportunidade detectada para hoje</div>';
                    } else {
                        container.innerHTML = todayData.opportunities.map(renderOpportunity).join('');
                    }
                }
                
                // Carrega oportunidades futuras
                const upcomingRes = await fetch('/api/opportunities/upcoming');
                const upcomingData = await upcomingRes.json();
                if (upcomingData.success) {
                    const container = document.getElementById('upcomingOpportunities');
                    if (upcomingData.count === 0) {
                        container.innerHTML = '<div class="empty">Nenhuma oportunidade detectada para os próximos dias</div>';
                    } else {
                        container.innerHTML = upcomingData.opportunities.map(renderOpportunity).join('');
                    }
                }
                
                document.getElementById('lastUpdate').textContent = new Date().toLocaleString('pt-BR');
                
            } catch (error) {
                console.error('Erro ao carregar dados:', error);
                document.getElementById('todayOpportunities').innerHTML = 
                    '<div class="error">Erro ao carregar dados. Tente novamente.</div>';
            }
        }
        
        // Carrega dados ao abrir página
        loadData();
        
        // Atualiza automaticamente a cada 5 minutos
        setInterval(loadData, 5 * 60 * 1000);
    </script>
</body>
</html>
"""


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

