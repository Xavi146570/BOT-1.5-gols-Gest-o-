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
SEASON = int(os.getenv("SEASON", "2024"))

api_client = APIClient(api_key=API_KEY)
db = Database()
analyzer = Analyzer(api_client, db, season=SEASON)

app = FastAPI(title="Football Value Detector")

@app.get("/", tags=["status"])
def index():
    ops = db.list_opportunities(limit=50)
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
# ✔️ CORRIGIDO — SCHEDULER 100% COMPATÍVEL COM RENDER
# -------------------------------------------------------------------

async def background_scheduler():
    """Loop assíncrono que roda continuamente em background."""
    await asyncio.sleep(5)  # espera 5s para garantir inicialização completa
    logger.info("🔄 Background scheduler iniciado.")

    while True:
        try:
            days_to_add = int(os.getenv("DAYS_TO_ADD", "5"))
            leagues_env = os.getenv("LEAGUES")
            if leagues_env:
                leagues = [int(x.strip()) for x in leagues_env.split(",") if x.strip().isdigit()]
            else:
                leagues = TOP_20_LEAGUES

            logger.info("🚀 Executando análise automática...")
            analyzer.run_daily_analysis(days_to_add=days_to_add, leagues=leagues)
            logger.info("✅ Análise automática concluída.")

        except Exception as e:
            logger.error(f"Erro no scheduler: {e}")

        # intervalo de repetição
        interval_hours = float(os.getenv("ANALYSIS_INTERVAL_HOURS", "4"))
        await asyncio.sleep(interval_hours * 3600)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(background_scheduler())


# -------------------------------------------------------------------
# ✔️ EXECUÇÃO LOCAL (Render ignora esta parte)
# -------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, log_level="info")
