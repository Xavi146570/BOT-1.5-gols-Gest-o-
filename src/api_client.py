# src/api_client.py
from typing import Dict, Any, List, Optional
import requests
import time
import logging

logger = logging.getLogger("src.api_client")
logger.setLevel(logging.INFO)
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

# Lista editável: top 20 ligas (pode alterar)
TOP_20_LEAGUES = [
    39, 140, 135, 78, 61, 2, 3, 45, 71, 94,
    253, 88, 203, 179, 144, 141, 40, 262, 301, 235
]


class APIClient:
    API_BASE = "https://v3.football.api-sports.io/"

    def __init__(self, api_key: str, max_retries: int = 3, timeout: int = 15):
        self.api_key = api_key or ""
        self.headers = {'x-apisports-key': self.api_key} if self.api_key else {}
        self.max_retries = max_retries
        self.timeout = timeout

        if self.api_key:
            logger.info("Conectado ao cliente da API de Futebol e cabeçalho de autenticação configurado.")
        else:
            logger.warning("API_FOOTBALL_KEY não fornecida — chamadas à API irão falhar sem chave.")

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        url = f"{self.API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
                if resp.status_code == 403:
                    logger.error("❌ Erro 403 — chave inválida/sem permissões.")
                    return None
                if resp.status_code == 429:
                    wait = min(60, 2 ** attempt)
                    logger.warning(f"⚠️ Rate limit 429 — tentativa {attempt}/{self.max_retries}. Esperando {wait}s.")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and data.get('errors'):
                    logger.error(f"❌ Erros na resposta da API: {data.get('errors')}")
                    return None
                return data.get('response', data)
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ RequestException para {endpoint}: {e}")
                time.sleep(1 + attempt)
            except Exception as e:
                logger.error(f"❌ Erro inesperado para {endpoint}: {e}")
                break
        logger.error("❌ Todas as tentativas falharam.")
        return None

    # -------------------------
    # Fixtures: permite lista de ligas
    # -------------------------
    def get_fixtures_by_date(self, date: str, leagues: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if leagues:
            if len(leagues) > 20:
                logger.warning("Recebida lista de ligas > 20, truncando para os primeiros 20.")
                leagues = leagues[:20]
            for lid in leagues:
                logger.info(f"Buscando fixtures para {date} | league={lid}")
                resp = self._make_request("fixtures", params={'date': date, 'league': lid})
                if resp is None:
                    logger.warning(f"Falha ao buscar fixtures para liga {lid} (retornou None).")
                    continue
                if isinstance(resp, list):
                    results.extend(resp)
        else:
            logger.info(f"Buscando fixtures para {date} em todas as ligas.")
            resp = self._make_request("fixtures", params={'date': date})
            if resp is None:
                logger.warning("Falha ao buscar fixtures (todas as ligas).")
                return []
            if isinstance(resp, list):
                results = resp

        # remover duplicados por fixture id
        unique = {}
        for f in results:
            try:
                fid = int(f['fixture']['id'])
            except Exception:
                fid = id(f)
            unique[fid] = f
        fixtures_unique = list(unique.values())
        logger.info(f"Fixtures coletadas: {len(fixtures_unique)}")
        return fixtures_unique

    # -------------------------
    # Team statistics (teams/statistics)
    # -------------------------
    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Optional[Dict[str, Any]]:
        params = {'team': team_id, 'league': league_id, 'season': season}
        resp = self._make_request("teams/statistics", params=params)
        if resp is None:
            logger.warning(f"Falha ao obter stats para team {team_id} (league {league_id}).")
            return None

        try:
            data = resp if isinstance(resp, dict) else (resp[0] if isinstance(resp, list) and resp else resp)
            def dget(path_list):
                node = data
                for p in path_list:
                    if node is None:
                        return None
                    if isinstance(node, list):
                        node = node[0] if node else None
                    if isinstance(node, dict):
                        node = node.get(p)
                    else:
                        return None
                return node

            gf = dget(['goals', 'for', 'total', 'average']) or dget(['team', 'statistics', 'goals_for_avg'])
            ga = dget(['goals', 'against', 'total', 'average']) or dget(['team', 'statistics', 'goals_against_avg'])
            over_15 = dget(['fixtures', 'goals', 'for', 'over_1_5']) or dget(['over_1_5_rate'])
            over_25 = dget(['fixtures', 'goals', 'for', 'over_2_5']) or dget(['over_2_5_rate'])

            def to_float(x):
                try:
                    return float(x)
                except Exception:
                    return None

            result = {
                'goals_for_avg': to_float(gf),
                'goals_against_avg': to_float(ga),
                'over_1_5_rate': to_float(over_15),
                'over_2_5_rate': to_float(over_25),
                'raw': data
            }
            logger.info(f"Estatísticas processadas para team {team_id}.")
            return result
        except Exception as e:
            logger.error(f"Erro ao processar team stats: {e}")
            return None

    # -------------------------
    # H2H
    # -------------------------
    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Optional[Dict[str, Any]]:
        resp = self._make_request("fixtures/headtohead", params={'h2h': f"{team1_id}-{team2_id}"})
        if resp is None:
            logger.warning("Falha ao obter H2H.")
            return None

        try:
            matches = resp if isinstance(resp, list) else [resp]
            total = 0
            over15 = 0
            over25 = 0
            for m in matches:
                sc_home = None
                sc_away = None
                try:
                    sc_home = m.get('score', {}).get('fulltime', {}).get('home')
                    sc_away = m.get('score', {}).get('fulltime', {}).get('away')
                except Exception:
                    continue
                if sc_home is None or sc_away is None:
                    continue
                try:
                    s = int(sc_home) + int(sc_away)
                except Exception:
                    continue
                total += 1
                if s > 1:
                    over15 += 1
                if s > 2:
                    over25 += 1
            if total == 0:
                return {'h2h_over_1_5_rate': None, 'h2h_over_2_5_rate': None, 'h2h_matches': 0}
            return {'h2h_over_1_5_rate': over15 / total, 'h2h_over_2_5_rate': over25 / total, 'h2h_matches': total}
        except Exception as e:
            logger.error(f"Erro ao processar H2H: {e}")
            return None

    # -------------------------
    # Odds: API -> fallback exchange-simulado
    # -------------------------
    def get_odds(self, fixture_id: int) -> Dict[str, float]:
        logger.info(f"Buscando odds para fixture {fixture_id} via API-Sports...")
        resp = self._make_request("odds", params={'fixture': fixture_id})
        parsed: Dict[str, float] = {}

        if resp:
            try:
                for item in resp if isinstance(resp, list) else [resp]:
                    bookmakers = item.get('bookmakers') or item.get('bookmaker') or []
                    for bk in bookmakers:
                        markets = bk.get('bets') or bk.get('markets') or []
                        for m in markets:
                            values = m.get('values') or m.get('options') or []
                            for v in values:
                                label = str(v.get('value', '')).lower()
                                odd = v.get('odd') or v.get('price') or v.get('odds')
                                if odd is None:
                                    continue
                                odd = float(odd)
                                if '0.5' in label and 'over' in label:
                                    parsed.setdefault('over_0_5_odds', odd)
                                if '1.5' in label and 'over' in label:
                                    parsed.setdefault('over_1_5_odds', odd)
                                if '2.5' in label and 'over' in label:
                                    parsed.setdefault('over_2_5_odds', odd)
                if parsed:
                    logger.info("Odds extraídas da API-Sports.")
                    return parsed
            except Exception as e:
                logger.warning(f"Erro a extrair odds da API-Sports: {e}")

        logger.info("Odds não encontradas na API-Sports — a usar fallback exchange simulado.")
        return self._external_exchange_odds(fixture_id)

    def _external_exchange_odds(self, fixture_id: int) -> Dict[str, float]:
        base_05 = 1.08 + (fixture_id % 5) * 0.01
        base_15 = 1.25 + (fixture_id % 7) * 0.02
        return {'over_0_5_odds': round(base_05, 2), 'over_1_5_odds': round(base_15, 2)}
