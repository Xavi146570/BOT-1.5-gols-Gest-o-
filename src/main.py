# src/main.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from src.analyzer import Analyzer
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("src.main")

app = FastAPI()
scheduler = BackgroundScheduler()
analyzer = Analyzer()

LEAGUES = [
    94,  # Portugal - Primeira Liga
    88,  # Holanda - Eredivisie
    89,  # Holanda - Eerste Divisie (Jong AZ vs Maastricht)
    78,  # Alemanha - Bundesliga
    40,  # Inglaterra - Championship
]

def run_daily():
    try:
        logger.info("🚀 Iniciando análise diária...")
        analyzer.run_daily_analysis(leagues=LEAGUES)
        logger.info("✅ Análise concluída.")
    except Exception as e:
        logger.error(f"❌ Erro no scheduler diário: {e}")
    finally:
        logger.info("⏳ Próxima execução daqui a 24 horas.")

# ✅ Executa imediatamente ao arrancar
run_daily()

# ✅ Agenda para repetir a cada 24 horas
scheduler.add_job(run_daily, "interval", hours=24)
scheduler.start()
logger.info("⏳ Scheduler diário iniciado (1x por dia).")

@app.get("/")
def root():
    return {
        "status": "running",
        "leagues": LEAGUES,
        "timestamp": datetime.now().isoformat()
    }
