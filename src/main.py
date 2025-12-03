# src/main.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from src.analyzer import Analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("src.main")

app = FastAPI()
scheduler = BackgroundScheduler()
analyzer = Analyzer()

LEAGUES = [
    39, 140, 61, 78, 135, 94, 88, 203, 179, 144,
    141, 40, 262, 301, 235, 253, 556, 566, 569, 795
]

def run_daily():
    try:
        logger.info("🚀 Executando análise diária...")
        analyzer.run_daily_analysis(leagues=LEAGUES)
    except Exception as e:
        logger.error(f"Erro no scheduler diário: {e}")
    finally:
        logger.info("⏳ Próxima execução daqui a 24 horas.")

scheduler.add_job(run_daily, "interval", hours=24)
scheduler.start()
logger.info("⏳ Scheduler diário iniciado (1x por dia).")

@app.get("/")
def root():
    return {"status": "running", "leagues": LEAGUES}
