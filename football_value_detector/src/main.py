# src/main.py
import os
import logging
from flask import Flask, jsonify
from threading import Timer
from src.api_client import APIClient, TOP_20_LEAGUES
from src.database import Database
from src.analyzer import Analyzer
from src.utils import get_utc_today_plus_days

# Logging
logger = logging.getLogger("__main__")
logger.setLevel(logging.INFO)
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

# Config via env
API_KEY = os.getenv("API_FOOTBALL_KEY", "")
# optionally provide season via env
SEASON = int(os.getenv("SEASON", "2024"))

# Inicializar componentes
api_client = APIClient(api_key=API_KEY)
db = Database()
analyzer = Analyzer(api_client, db, season=SEASON)

# Flask app para expor resultados simples
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    ops = db.list_opportunities(limit=50)
    return jsonify({"status": "ok", "opportunities": ops})

# Runner: executa análise inicial e agenda análises periódicas
def run_analysis_cycle():
    try:
        # default days_to_add = +5 (você pode alterar)
        days_to_add = int(os.getenv("DAYS_TO_ADD", "5"))
        leagues_env = os.getenv("LEAGUES")  # form: "39,140,78"
        if leagues_env:
            leagues = [int(x.strip()) for x in leagues_env.split(",") if x.strip().isdigit()]
        else:
            leagues = TOP_20_LEAGUES

        analyzer.run_daily_analysis(days_to_add=days_to_add, leagues=leagues)
    except Exception as e:
        logger.error(f"Erro no ciclo de análise: {e}")
    finally:
        # agendar próxima execução (ex.: cada 4 horas)
        interval_hours = float(os.getenv("ANALYSIS_INTERVAL_HOURS", "4"))
        logger.info(f"Próxima análise em {interval_hours} horas.")
        Timer(interval_hours * 3600, run_analysis_cycle).start()

if __name__ == "__main__":
    # start initial analysis (blocking quick) then flask
    logger.info("✅ Scheduler inicializado com sucesso")
    logger.info("🚀 Executando análise inicial...")
    run_analysis_cycle()

    # Run Flask (prod: use gunicorn or outro WSGI)
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
