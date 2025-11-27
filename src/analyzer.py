# src/analyzer.py
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger("src.analyzer")
logger.setLevel(logging.INFO)

class Analyzer:
    def __init__(self, api_client, db, season: int | None = None):
        self.api = api_client
        self.db = db
        self.env_season = season  # season fornecida via env, pode ser None

    # -----------------------------------------------------
    # calcula season a usar com base na data alvo
    # temporada representada pelo ano de início (ex: 2025 para 2025/26)
    # -----------------------------------------------------
    @staticmethod
    def season_for_date(target_date: datetime.date) -> int:
        # se mês >= 7 (jul), temporada começa no ano corrente, senão no ano anterior
        if target_date.month >= 7:
            return target_date.year
        return target_date.year - 1

    # -----------------------------------------------------
    # EXECUTA ANÁLISE: tenta várias datas até encontrar jogos
    # -----------------------------------------------------
    def run_daily_analysis(self, days_to_add: int = 0, leagues: list[int] | None = None):
        logger.info("🚀 INICIANDO ANÁLISE DIÁRIA")
        logger.info("============================================================")

        max_ahead = int(os.getenv("MAX_DAYS_AHEAD", "7"))
        leagues_to_use = leagues if leagues else getattr(self.api, "TOP_20_LEAGUES", [])

        found_any = False
        all_opportunities = []

        # Tenta offsets 0..max_ahead (inclusive)
        for offset in range(0, max_ahead + 1):
            target_date = (datetime.utcnow() + timedelta(days=days_to_add + offset)).date()
            date_str = target_date.strftime("%Y-%m-%d")

            logger.info(f"📅 Tentativa para data: {date_str} (+{days_to_add + offset} dias)")

            season = self.env_season if self.env_season else self.season_for_date(target_date)
            logger.info(f"   usando season: {season}")

            fixtures_for_date = []

            # buscar fixtures por liga
            for lg in leagues_to_use:
                try:
                    fixtures = self.api.get_fixtures(date_str, lg, season)
                    if not fixtures:
                        logger.debug(f"   ⚠️ Nenhum jogo encontrado na liga {lg} para {date_str}.")
                        continue
                    # alguns endpoints retornam dict/obj com key 'response', normalizado no client
                    if isinstance(fixtures, list):
                        fixtures_for_date.extend(fixtures)
                    else:
                        # se for dict com 'response' ou similar
                        try:
                            fixtures_for_date.extend(fixtures)
                        except Exception:
                            continue
                except Exception as e:
                    logger.error(f"Erro ao buscar fixtures para liga {lg}: {e}")
                    continue

            logger.info(f"   Fixtures encontradas nesta data: {len(fixtures_for_date)}")

            if not fixtures_for_date:
                # tentar próxima data no loop
                logger.info("   Sem fixtures nesta data — tentando próxima data.")
                continue

            # processa fixtures encontradas (nesta data) e marca found_any True
            found_any = True

            for fx in fixtures_for_date:
                try:
                    fixture_id = None
                    try:
                        fixture_id = int(fx.get("fixture", {}).get("id") or fx.get("id") or fx.get("fixture_id"))
                    except Exception:
                        fixture_id = fx.get("fixture", {}).get("id") if isinstance(fx.get("fixture"), dict) else None

                    if not fixture_id:
                        logger.debug("   Ignorando fixture sem id válido.")
                        continue

                    # nomes das equipas
                    teams = fx.get("teams") or {}
                    home = teams.get("home", {}).get("name") or teams.get("home")
                    away = teams.get("away", {}).get("name") or teams.get("away")

                    league_name = fx.get("league", {}).get("name") if fx.get("league") else None
                    league_id = fx.get("league", {}).get("id") if fx.get("league") else None

                    # odds
                    odds_resp = self.api.get_odds(fixture_id)
                    over_15 = None
                    if odds_resp:
                        over_15 = self.api.extract_over_1_5(odds_resp)

                    if not over_15:
                        logger.debug(f"   Odds Over 1.5 não encontradas para fixture {fixture_id}.")
                        continue

                    # critério simples: aceitar odds >= 1.20 (ajustável via env)
                    threshold = float(os.getenv("ODDS_THRESHOLD", "1.20"))
                    if over_15 < threshold:
                        logger.debug(f"   Odd {over_15} < threshold {threshold} para fixture {fixture_id}. Ignorando.")
                        continue

                    # compor oportunidade
                    opp = {
                        "fixture_id": fixture_id,
                        "team1": home,
                        "team2": away,
                        "league": league_name or f"league_{league_id}",
                        "market": "Over 1.5",
                        "prob": None,
                        "odds": over_15,
                        "ev": None,
                        "confidence": None,
                        "kelly": None,
                        "date": date_str
                    }

                    # salvar no DB: compatível com métodos save_opportunity ou insert_opportunity
                    try:
                        if hasattr(self.db, "save_opportunity"):
                            # save_opportunity(fixture_id, team1, team2, league, market, prob, odds, ev, confidence, kelly)
                            self.db.save_opportunity(
                                fixture_id,
                                home or "",
                                away or "",
                                opp["league"],
                                opp["market"],
                                opp["prob"] or 0.0,
                                opp["odds"],
                                opp["ev"] or 0.0,
                                opp["confidence"] or 0.0,
                                opp["kelly"] or 0.0
                            )
                        elif hasattr(self.db, "insert_opportunity"):
                            self.db.insert_opportunity(opp)
                        else:
                            logger.warning("DB não possui método de salvamento conhecido. Oportunidade não persistida.")
                    except Exception as e:
                        logger.error(f"Erro ao salvar oportunidade no DB: {e}")

                    all_opportunities.append(opp)

                except Exception as e:
                    logger.error(f"Erro no processamento de fixture {fx}: {e}")
                    continue

            # após processar uma data com fixtures, paramos a varredura
            if found_any:
                logger.info(f"✅ Encontradas fixtures e processadas para {date_str}. Parando varredura de datas.")
                break

        if not found_any:
            logger.warning("⚠️ Nenhum jogo encontrado em todo o intervalo verificado.")
        else:
            logger.info(f"🏁 Total oportunidades encontradas neste ciclo: {len(all_opportunities)}")

        logger.info("============================================================")
        return all_opportunities
