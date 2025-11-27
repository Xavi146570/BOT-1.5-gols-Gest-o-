import os
import asyncio
import logging
from fastapi import FastAPI
import uvicorn
from src.analyzer import Analyzer

# Configuração de logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
analyzer = Analyzer()

# -------------------------------------------------------------------

# Scheduler diário (1x por dia)

# -------------------------------------------------------------------

async def daily_scheduler():
    # pequena espera após startup
    await asyncio.sleep(5)
    logger.info("⏳ Scheduler diário iniciado (1x por dia).")

    while True:
        try:
            leagues_env = os.getenv("LEAGUES")
            if leagues_env:
                leagues = [int(x.strip()) for x in leagues_env.split(",") if x.strip().isdigit()]
            else:
                leagues = None  # Analyzer usará padrão

            logger.info("🚀 Executando análise diária...")
            analyzer.run_daily_analysis(leagues=leagues)
            logger.info("✅ Análise diária concluída.")
        except Exception as e:
            logger.error(f"Erro no scheduler diário: {e}")

        logger.info("⏳ Próxima execução daqui a 24 horas.")
        await asyncio.sleep(24 * 3600)

# -------------------------------------------------------------------

# Startup da aplicação

# -------------------------------------------------------------------

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(daily_scheduler())

# -------------------------------------------------------------------

# Endpoint manual de trigger

# -------------------------------------------------------------------

@app.get("/run")
async def run_analysis():
    analyzer.run_daily_analysis()
    return {"status": "ok", "message": "Análise diária executada manualmente."}

# -------------------------------------------------------------------

# Execução local direta

# -------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, log_level="info")
