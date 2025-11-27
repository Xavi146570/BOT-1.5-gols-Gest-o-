# src/analyzer.py
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self, api_client, db, season: int):
        self.api = api_client
        self.db = db
        self.season = season

    # -----------------------------------------------------
    # EXECUTA ANÁLISE DIÁRIA
    # -----------------------------------------------------
    def run_daily_analysis(self, days_to_add: int, leagues: list[int]):
        logger.info("🚀 INICIANDO ANÁLISE DIÁRIA")
        logger.info("============================================================")

        target_date = (datetime.utcnow() + timedelta(days=days_to_add)).date()
        date_str = target_date.strftime("%Y-%m-%d")

        logger.info(f"📅 A data de análise ATUAL é: {date_str} (+{days_to_add} dias)")

        all_fixtures = []

        # -----------------------------------------------------
        # BUSCA FIXTURES LIGA A LIGA
        # -----------------------------------------------------
        for lg in leagues:
            try:
                fixtures = self.api.get_fixtures(date_str, lg, self.season)

                if not fixtures:
                    logger.warning(f"⚠️ Nenhum jogo encontrado na liga {lg}.")
                    continue

                all_fixtures.extend(fixtures)

            except Exception as e:
                logger.error(f"Erro ao buscar liga {lg}: {e}")
                continue

        logger.info(f"📊 Fixtures coletadas: {len(all_fixtures)}")

        if not all_fixtures:
            logger.warning("⚠️ Nenhum jogo encontrado na data. Finalizando análise.")
            return []

        # -----------------------------------------------------
        # PROCESSAR JOGOS (SIMPLIFICADO)
        # -----------------------------------------------------
        opportunities = []

        for fx in all_fixtures:
            try:
                fixture_id = fx["fixture"]["id"]
                teams = fx["teams"]
                home = teams["home"]["name"]
                away = teams["away"]["name"]

                # coleta odds
                odds_data = self.api.get_odds(fixture_id)

                if not odds_data:
                    continue

                # EXEMPLO -> odds over 1.5
                selected = None
                for book in odds_data:
                    try:
                        for mv in book["bookmakers"][0]["bets"]:
                            if mv["name"] == "Goals Over/Under" and mv["id"] == 5:
                                for o in mv["values"]:
                                    if o["value"] == "Over 1.5":
                                        selected = float(o["odd"])
                                        break
                    except:
                        continue

                if not selected:
                    continue

                if selected >= 1.50:  # exemplo de critério
                    opp = {
                        "fixture_id": fixture_id,
                        "home_team": home,
                        "away_team": away,
                        "odd": selected,
                        "league_id": fx["league"]["id"],
                        "league_name": fx["league"]["name"],
                        "date": date_str
                    }

                    opportunities.append(opp)
                    self.db.insert_opportunity(opp)

            except Exception as e:
                logger.error(f"Erro no processamento de fixture: {e}")
                continue

        logger.info(f"🏁 TOTAL OPORTUNIDADES ENCONTRADAS: {len(opportunities)}")
        logger.info("============================================================")

        return opportunities
