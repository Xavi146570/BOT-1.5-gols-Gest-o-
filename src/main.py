# src/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from src.api_client import APIClient, TOP_20_LEAGUES
from src.database import Database
from src.analyzer import Analyzer

logger = logging.getLogger("__main__")
logger.setLevel(logging.INFO)
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
# SEASON optional; analyzer will infer from date if not provided
SEASON_ENV = os.getenv("SEASON")
SEASON = int(SEASON_ENV) if SEASON_ENV and SEASON_ENV.isdigit() else None

api_client = APIClient(api_key=API_KEY)
db = Database()
analyzer = Analyzer(api_client, db, season=SEASON)

app = FastAPI(title="Football Value Detector")

@app.get("/", tags=["status"])
def index():
    ops = db.list_opportunities(limit=50) if hasattr(db, "list_opportunities") else []
    return JSONResponse({"status": "ok", "opportunities": ops})

@app.get("/run", tags=["admin"])
def run_once():
    try:
        days_to_add = int(os.getenv("DAYS_TO_ADD", "5"))
        leagues_env = os.getenv("LEAGUES")
        if leagues_env:
            leagues = [int(x.strip()) for x in leagues_env.split(",") if x.strip().isdigit()]
        else:
            leagues = TOP_20_LEAGUES
        ops = analyzer.run_daily_analysis(days_to_add=days_to_add, leagues=leagues)
        return JSONResponse({"status": "ok", "found": len(ops)})
    except Exception as e:
        logger.error(f"Erro ao forçar análise: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


# -------------------------------------------------------------------
# Background scheduler SEGURO (1 execução por dia)
# -------------------------------------------------------------------
import asyncio
from datetime import datetime, time, timedelta

scheduler_lock = False  # evita múltiplas execuções no Render


async def run_daily_task():
    """Executa a análise 1x por dia."""
    global scheduler_lock
    if scheduler_lock:
        return  # evita chamadas duplicadas (típico do Render)
    scheduler_lock = True

    try:
        days_to_add = int(os.getenv("DAYS_TO_ADD", "5"))

        leagues_env = os.getenv("LEAGUES")
        if leagues_env:
            leagues = [int(x.strip()) for x in leagues_env.split(",") if x.strip().isdigit()]
        else:
            leagues = TOP_20_LEAGUES

        logger.info("🚀 Execução diária iniciada...")
        analyzer.run_daily_analysis(days_to_add=days_to_add, leagues=leagues)
        logger.info("✅ Execução diária finalizada.")
    except Exception as e:
        logger.error(f"Erro na execução diária: {e}")

    scheduler_lock = False


async def background_scheduler():
    """Agenda a execução para ocorrer 1x por dia às 06:00 UTC."""
    await asyncio.sleep(5)  # garante startup completa

    logger.info("⏳ Scheduler diário iniciado (1x por dia).")

    while True:
        now = datetime.utcnow()
        run_time = time(6, 0)  # 06:00 UTC — horário leve

        today_run = datetime.combine(now.date(), run_time)

        # se já passou hoje → agenda para amanhã
        if now > today_run:
            today_run += timedelta(days=1)

        wait_seconds = (today_run - now).total_seconds()

        logger.info(f"⏳ Próxima execução diária daqui a {wait_seconds/3600:.2f} horas.")

        await asyncio.sleep(wait_seconds)

        await run_daily_task()


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(background_scheduler())


# -------------------------------------------------------------------
# Execução local
# -------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, log_level="info")

