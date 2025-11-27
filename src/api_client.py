# src/api_client.py
import logging
import requests
from datetime import datetime

logger = logging.getLogger("src.api_client")
logger.setLevel(logging.INFO)

TOP_20_LEAGUES = [
    39, 140, 61, 78, 135, 94, 88, 203, 179, 144,
    141, 40, 262, 301, 235, 253, 556, 566, 569, 795
]

class APIClient:
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key or ""
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            })
            logger.info("Conectado ao cliente da API de Futebol e cabeçalho de autenticação configurado.")
        else:
            logger.warning("API key não fornecida. Chamadas à API irão falhar sem chave.")

    # ------------------------------
    # FIXTURES (com season)
    # ------------------------------
    def get_fixtures(self, date: str, league_id: int, season: int):
        """
        date: 'YYYY-MM-DD'
        league_id: int
        season: int
        Retorna lista de fixtures ou [] / None em caso de falha.
        """
        url = f"{self.BASE_URL}/fixtures"
        params = {
            "date": date,
            "league": league_id,
            "season": season
        }

        logger.info(f"Buscando fixtures para {date} | league={league_id} | season={season}")

        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            # API pode devolver {'errors': {...}} ou {'results': 0, 'response': []}
            if isinstance(data, dict) and data.get("errors"):
                logger.error(f"❌ Erros na resposta da API: {data.get('errors')}")
                return None

            # Normaliza
            return data.get("response", [])

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTPError ao buscar fixtures (league={league_id}): {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar fixtures: {e}")
            return None

    # ------------------------------
    # ODDS
    # ------------------------------
    def get_odds(self, fixture_id: int):
        """
        Tenta obter odds para o fixture. Retorna lista (formato API) ou [] / None.
        """
        url = f"{self.BASE_URL}/odds"
        params = {"fixture": fixture_id}

        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict) and data.get("errors"):
                logger.warning(f"⚠️ Erro ao buscar odds para {fixture_id}: {data.get('errors')}")
                return None

            return data.get("response", [])
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTPError ao buscar odds (fixture={fixture_id}): {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar odds: {e}")
            return None

    # ------------------------------
    # Helper: extrai odd Over 1.5 de forma defensiva
    # ------------------------------
    @staticmethod
    def extract_over_1_5(odds_response) -> float | None:
        """
        odds_response: estrutura retornada por get_odds (lista/obj)
        tenta extrair a odd decimal para 'Over 1.5' de forma robusta.
        Retorna float ou None.
        """
        try:
            items = odds_response if isinstance(odds_response, list) else [odds_response]
            for it in items:
                # formatos possíveis: bookmakers -> markets/bets -> values/options
                bookmakers = it.get("bookmakers") or it.get("bookmaker") or []
                # se bookmaker for dict, tente converter para list
                if isinstance(bookmakers, dict):
                    bookmakers = [bookmakers]
                for bk in bookmakers:
                    # mercados podem estar em 'bets' ou 'markets'
                    markets = bk.get("bets") or bk.get("markets") or []
                    if isinstance(markets, dict):
                        markets = [markets]
                    for m in markets:
                        values = m.get("values") or m.get("options") or m.get("outcomes") or []
                        for v in values:
                            label = str(v.get("value", "")).lower()
                            odd = v.get("odd") or v.get("price") or v.get("odds")
                            if odd is None:
                                # às vezes a odd está aninhada
                                odd = v.get("price_decimal") or v.get("decimal")
                            if "1.5" in label and "over" in label:
                                try:
                                    return float(odd)
                                except Exception:
                                    continue
                # alternativamente procurar por markets top-level
                markets_top = it.get("markets") or []
                if isinstance(markets_top, dict):
                    markets_top = [markets_top]
                for m in markets_top:
                    values = m.get("outcomes") or m.get("values") or []
                    for v in values:
                        label = str(v.get("name", "")).lower()
                        odd = v.get("price") or v.get("decimal") or v.get("odd")
                        if "over 1.5" in label:
                            try:
                                return float(odd)
                            except Exception:
                                continue
        except Exception:
            return None
        return None
