import os
import logging
from datetime import datetime
import requests

logger = logging.getLogger(**name**)
logger.setLevel(logging.INFO)

class Analyzer:
def **init**(self):
self.api_url = "[https://api-football-v1.p.rapidapi.com/v3/fixtures](https://api-football-v1.p.rapidapi.com/v3/fixtures)"
self.api_key = os.getenv("RAPIDAPI_KEY")
self.headers = {
"X-RapidAPI-Key": self.api_key,
"X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

```
def run_daily_analysis(self, leagues=None):
    """Busca os jogos da data atual para as ligas especificadas e processa os dados."""
    if leagues is None:
        leagues = [795]  # padrão, exemplo de liga

    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"📅 Executando análise para a data atual: {today_str}")

    any_fixtures = False

    for league_id in leagues:
        try:
            logger.info(f"🔎 Buscando jogos da liga {league_id}...")
            params = {
                "date": today_str,
                "league": league_id,
                "season": datetime.now().year
            }
            response = requests.get(self.api_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            fixtures = data.get("response", [])
            if not fixtures:
                logger.info(f"⚠️ Nenhum jogo encontrado para a liga {league_id} hoje.")
                continue

            any_fixtures = True
            logger.info(f"✅ {len(fixtures)} jogos encontrados para a liga {league_id}.")
            # Aqui você processaria os dados dos jogos (ex: salvar no DB, análises, etc.)

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning(f"⚠️ Limite de requests atingido para league={league_id}: {e}")
            else:
                logger.error(f"HTTPError ao buscar fixtures (league={league_id}): {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar fixtures da liga {league_id}: {e}")

    if not any_fixtures:
        logger.info("⚠️ Nenhum jogo encontrado em todo o dia de hoje.")
```

# Exemplo de uso direto

if **name** == "**main**":
analyzer = Analyzer()
analyzer.run_daily_analysis()
