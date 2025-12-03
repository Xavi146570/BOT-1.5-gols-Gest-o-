import os
import asyncio
import logging
from fastapi import FastAPI
import uvicorn
from src.analyzer import Analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
analyzer = Analyzer()

async def daily_scheduler():
    await asyncio.sleep(5)
    logger.info("⏳ Scheduler diário iniciado.")

    while True:
        try:
            logger.info("🚀 Executando análise diária automática...")
            analyzer.run_daily_analysis()
            logger.info("✅ Análise diária concluída.")
        except Exception as e:
            logger.error(f"Erro no scheduler: {e}")

        logger.info("⏳ Próxima execução em 24 horas.")
        await asyncio.sleep(24 * 3600)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(daily_scheduler())

@app.get("/run")
async def run_analysis():
    analyzer.run_daily_analysis()
    return {"status": "ok", "message": "Análise executada manualmente."}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, log_level="info")
