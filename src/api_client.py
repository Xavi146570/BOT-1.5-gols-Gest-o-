# api_client.py
from typing import Dict, Any, List, Optional, Union
import requests
import time
import logging
import math

logger = logging.getLogger("src.api_client")
logger.setLevel(logging.INFO)

# Configure um handler se ainda não existir (útil para execução "standalone")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class APIClient:
    """
    Cliente para interagir com API-Sports (v3.football.api-sports.io) e
    com um fallback opcional para a TheOddsAPI (https://the-odds-api.com)
    para recuperar odds quando a API-Sports não fornecer.
    
    - Não usa MOCK.
    - get_fixtures_by_date aceita:
        * league_id: int (apenas uma liga)
        * league_ids: List[int] (até 20)
        * league_id = None -> retorna todos os jogos do dia (quando suportado pela API)
    """

    API_BASE = "https://v3.football.api-sports.io/"
    ODDS_API_BASE = "https://api.the-odds-api.com/v4/sports/"

    def __init__(self, api_key: str, odds_api_key: Optional[str] = None, max_retries: int = 3, timeout: int = 15):
        self.api_key = api_key or ""
        self.odds_api_key = odds_api_key or ""
        self.headers = {'x-apisports-key': self.api_key} if self.api_key else {}
        self.max_retries = max_retries
        self.timeout = timeout

        if not self.api_key:
            logger.warning("API_FOOTBALL_KEY não fornecido. Muitas chamadas poderão falhar.")
        else:
            logger.info("Conectado ao cliente da API de Futebol e cabeçalho de autenticação configurado.")

        if not self.odds_api_key:
            logger.info("ODDS_API_KEY (fallback) não fornecido — odds fallback desativado.")
        else:
            logger.info("ODDS fallback configurado (TheOddsAPI).")

    # -----------------------
    # Helper de requisições
    # -----------------------
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Faz requests GET com retry e tratamento para 403/429/timeout.
        Retorna a chave 'response' do JSON (ou None em falha).
        """
        url = f"{self.API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
                if resp.status_code == 403:
                    logger.error("❌ Erro 403: autenticação falhou (verifique API_FOOTBALL_KEY).")
                    return None
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"⚠️ Rate limit (429). Tentativa {attempt}/{self.max_retries}. Esperando {wait}s.")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                # API-Sports usa 'results' e 'response'
                if isinstance(data, dict) and data.get('errors'):
                    logger.error(f"❌ Erros na resposta da API: {data.get('errors')}")
                    return None
                # OK
                logger.info(f"✅ Requisição {endpoint} OK (params={params}).")
                return data.get('response', data)
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Erro de conexão na requisição {endpoint}: {e}")
                # backoff exponencial
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"❌ Erro inesperado na requisição {endpoint}: {e}")
                break
        logger.error(f"❌ Todas as tentativas para {endpoint} falharam.")
        return None

    # -----------------------
    # Fixtures
    # -----------------------
    def get_fixtures_by_date(self, date: str, league_id: Optional[int] = None,
                             league_ids: Optional[List[int]] = None,
                             max_leagues: int = 20) -> List[Dict[str, Any]]:
        """
        date: 'YYYY-MM-DD'
        league_id: se definido, busca apenas essa liga
        league_ids: lista de ligas (até max_leagues)
        Se ambos forem None -> busca por date apenas (todas as ligas)
        Retorna lista de fixtures (padrão API-Sports), ou [] se nenhum resultado / falha.
        """
        results: List[Dict[str, Any]] = []

        # Prioridade: league_ids (lista) -> league_id (single) -> none (all)
        if league_ids:
            if len(league_ids) > max_leagues:
                logger.warning(f"Limite de ligas atingido: cortando para os primeiros {max_leagues} ligas.")
                league_ids = league_ids[:max_leagues]
            for lid in league_ids:
                logger.info(f"Buscando fixtures para {date} | league={lid}")
                resp = self._make_request("fixtures", params={'date': date, 'league': lid})
                if resp is None:
                    logger.warning(f"Falha ao obter fixtures para league {lid} — pulando.")
                    continue
                # API retorna lista em resp
                if isinstance(resp, list):
                    results.extend(resp)
        else:
            params = {'date': date}
            if league_id:
                params['league'] = league_id
                logger.info(f"Buscando fixtures para {date} | league={league_id}")
            else:
                logger.info(f"Buscando fixtures para {date} | todas as ligas (quando suportado)")
            resp = self._make_request("fixtures", params=params)
            if resp is None:
                logger.warning("Falha ao obter fixtures (todos/league). Retornando lista vazia.")
                return []
            if isinstance(resp, list):
                results = resp

        # Remove duplicados (caso liga repetida)
        unique = {}
        for f in results:
            try:
                fid = int(f['fixture']['id'])
            except Exception:
                fid = id(f)
            unique[fid] = f
        fixtures_unique = list(unique.values())
        logger.info(f"🔎 Fixtures coletadas: {len(fixtures_unique)}")
        return fixtures_unique

    # -----------------------
    # Team statistics
    # -----------------------
    def collect_team_data(self, team_id: int, league_id: int, season: int) -> Optional[Dict[str, Any]]:
        """
        Coleta estatísticas da equipa via endpoint 'teams/statistics'.
        Retorna dicionário com métricas extraídas:
           - goals_for_avg
           - goals_against_avg
           - over_1_5_rate
           - over_2_5_rate
           - shots_avg (se disponível)
           - clean_sheets_rate (se disponível)
        Retorna None em caso de falha.
        """
        logger.info(f"Coletando stats do time {team_id} | league {league_id} | season {season}")
        resp = self._make_request("teams/statistics", params={'team': team_id, 'league': league_id, 'season': season})
        if resp is None:
            logger.warning(f"    ⚠️ Falha ao obter estatísticas da equipa {team_id}.")
            return None

        try:
            # O formato de resp costuma ser um objeto com estatísticas agregadas.
            # Vamos tentar extrair valores comuns com verificações defensivas.
            # As keys exatas dependem da versão da API - este método tenta ser robusto.
            # Se a resposta for uma lista (caso raro), pegue o primeiro elemento.
            data = resp
            if isinstance(resp, list) and len(resp) > 0:
                data = resp[0]

            # Exemplos possíveis de onde encontrar: data['response']['goals'] etc
            # Aqui fazemos múltiplas tentativas de leitura das métricas.
            gf = None
            ga = None
            over_15 = None
            over_25 = None
            shots = None
            clean_sheet_rate = None

            # Estrutura comum da API: data['team']['form'] e 'goals' dentro de 'fixtures' ou 'goals'
            # Tentativas práticas:
            # 1) procurar por 'goals' em resp
            if isinstance(data, dict):
                # goals for/against: procurar em keys aninhadas
                # várias APIs fornecem 'goals' -> {'for': {'total': {...}}, 'against': {...}}
                goals = self._deep_get(data, ['goals', 'for', 'total', 'average'])
                if goals is not None:
                    # average devolvido como string "1.5"
                    try:
                        gf = float(goals)
                    except Exception:
                        gf = None

                goals_against = self._deep_get(data, ['goals', 'against', 'total', 'average'])
                if goals_against is not None:
                    try:
                        ga = float(goals_against)
                    except Exception:
                        ga = None

                # percentuais de over - tentar em 'over' keys
                over_15 = self._deep_get(data, ['fixtures', 'goals', 'for', 'over_1_5'])
                over_25 = self._deep_get(data, ['fixtures', 'goals', 'for', 'over_2_5'])
                # alternativa: procurar por 'over' em respostas H2H ou similares
                # shots
                shots = self._deep_get(data, ['shots', 'total', 'average'])
                # clean sheets
                clean_sheet_rate = self._deep_get(data, ['clean_sheet', 'percentage'])

            # Como fallback, se não encontramos gf/ga, tentar checar 'team' ou formas
            if gf is None:
                gf_try = self._deep_get(data, ['team', 'statistics', 'goals_for_avg'])
                if gf_try is not None:
                    try:
                        gf = float(gf_try)
                    except:
                        gf = None

            # Final assembly (algumas métricas podem ficar None)
            result = {
                'goals_for_avg': gf,
                'goals_against_avg': ga,
                'over_1_5_rate': over_15,
                'over_2_5_rate': over_25,
                'shots_avg': shots,
                'clean_sheet_rate': clean_sheet_rate,
                'raw': data  # caso precise inspeccionar a resposta completa
            }
            logger.info(f"    ✅ Estatísticas processadas para team {team_id}.")
            return result
        except Exception as e:
            logger.error(f"    ❌ Erro ao processar estatísticas da equipa {team_id}: {e}")
            return None

    # -----------------------
    # H2H
    # -----------------------
    def collect_h2h_data(self, team1_id: int, team2_id: int) -> Optional[Dict[str, Any]]:
        """
        Coleta H2H via fixtures/headtohead?h2h=team1-team2
        Retorna dicionário com métricas (ex.: h2h_over_1_5_rate) ou None.
        """
        logger.info(f"Coletando H2H: {team1_id} vs {team2_id}")
        resp = self._make_request("fixtures/headtohead", params={'h2h': f"{team1_id}-{team2_id}"})
        if resp is None:
            logger.warning("    ⚠️ Falha ao obter H2H.")
            return None

        try:
            # Resp costuma ser lista de fixtures; podemos calcular uma taxa de over 1.5 a partir dos resultados
            matches = resp if isinstance(resp, list) else [resp]
            total = 0
            over15_count = 0
            over25_count = 0
            for m in matches:
                # path comum: m['score']['fulltime']['home'] / ['away']
                sc_home = self._deep_get(m, ['score', 'fulltime', 'home'])
                sc_away = self._deep_get(m, ['score', 'fulltime', 'away'])
                if sc_home is None or sc_away is None:
                    continue
                try:
                    s = int(sc_home) + int(sc_away)
                except:
                    continue
                total += 1
                if s > 1:
                    over15_count += 1
                if s > 2:
                    over25_count += 1

            if total == 0:
                logger.info("    ℹ️ H2H sem jogos com resultado disponível.")
                return {'h2h_over_1_5_rate': None, 'h2h_over_2_5_rate': None, 'h2h_matches': 0}

            return {
                'h2h_over_1_5_rate': over15_count / total,
                'h2h_over_2_5_rate': over25_count / total,
                'h2h_matches': total
            }
        except Exception as e:
            logger.error(f"    ❌ Erro ao processar H2H: {e}")
            return None

    # -----------------------
    # Odds (API-Sports -> fallback TheOddsAPI)
    # -----------------------
    def get_odds(self, fixture_id: int, sport_key: str = "soccer_epl") -> Dict[str, Any]:
        """
        Tenta obter odds via API-Sports (endpoint odds).
        Se não existir ou falhar, tenta fallback para TheOddsAPI (requires ODDS_API_KEY).
        Retorna dicionário mapeando 'over_0_5_odds', 'over_1_5_odds', 'over_2_5_odds' quando possível.
        Se nada encontrado, retorna {}.
        """
        # 1) API-Sports odds endpoint (se disponível na sua subscrição)
        if self.api_key:
            logger.info(f"Buscando odds via API-Sports para fixture {fixture_id}...")
            resp = self._make_request("odds", params={'fixture': fixture_id})
            if resp:
                # tentar extrair mercados
                try:
                    # resp geralmente é lista de bookmakers -> markets
                    # vamos procurar por mercados 'over/under' e valor '1.5' '0.5'
                    parsed = {}
                    for book in resp:
                        markets = book.get('bookmakers') or book.get('bookmaker') or book.get('markets') or []
                        # API shapes variam; tentar de forma defensiva
                        for b in markets:
                            # cada b possivelmente tem 'bets' com nomes e valores
                            bets = b.get('bets') or b.get('bets') or []
                            for bet in bets:
                                name = bet.get('name', '').lower()
                                if 'over' in name or 'over/under' in name or 'total goals' in name:
                                    # checar valores
                                    for opt in bet.get('values', []) or bet.get('options', []):
                                        label = str(opt.get('value', '')).lower()
                                        odd = opt.get('odd') or opt.get('price') or opt.get('odds')
                                        if isinstance(label, str) and odd:
                                            if '0.5' in label:
                                                parsed.setdefault('over_0_5_odds', float(odd))
                                            if '1.5' in label:
                                                parsed.setdefault('over_1_5_odds', float(odd))
                                            if '2.5' in label:
                                                parsed.setdefault('over_2_5_odds', float(odd))
                    if parsed:
                        logger.info("    ✅ Odds extraídas da API-Sports.")
                        return parsed
                except Exception as e:
                    logger.warning(f"    ⚠️ Não foi possível processar odds da API-Sports: {e}")

        # 2) Fallback: TheOddsAPI (ou outra)
        if self.odds_api_key:
            try:
                logger.info(f"Buscando odds via TheOddsAPI (fallback) para fixture {fixture_id}...")
                # TheOddsAPI consulta por esporte (ex: 'soccer_epl') e retorna eventos com odds.
                # Aqui fazemos um GET básico e tentamos casar por fixture_id usando tempos/teams (impreciso).
                url = f"{self.ODDS_API_BASE}{sport_key}/odds"
                params = {'apiKey': self.odds_api_key, 'regions': 'eu', 'markets': 'totals', 'oddsFormat': 'decimal'}
                r = requests.get(url, params=params, timeout=self.timeout)
                r.raise_for_status()
                data = r.json()
                # data é lista de eventos; devemos tentar casar por teams/commence_time
                # Para simplificar: vamos procurar por correspondência aproximada por fixture_id no 'id' (se existir)
                # Caso não encontre, retornamos {}.
                for event in data:
                    # event keys: 'id', 'home_team', 'away_team', 'bookmakers'...
                    # sem match direto, ignorar
                    # É complexo casar; aqui deixamos como tentativa básica.
                    if str(fixture_id) in str(event.get('id', '')):
                        parsed = {}
                        for b in event.get('bookmakers', []):
                            for m in b.get('markets', []):
                                if m.get('key') == 'totals':
                                    for outcome in m.get('outcomes', []):
                                        name = outcome.get('name', '').lower()
                                        price = outcome.get('price')
                                        if 'over 0.5' in name and price:
                                            parsed.setdefault('over_0_5_odds', float(price))
                                        if 'over 1.5' in name and price:
                                            parsed.setdefault('over_1_5_odds', float(price))
                                        if 'over 2.5' in name and price:
                                            parsed.setdefault('over_2_5_odds', float(price))
                        if parsed:
                            logger.info("    ✅ Odds extraídas do fallback TheOddsAPI.")
                            return parsed
            except Exception as e:
                logger.warning(f"    ⚠️ Falha no fallback de odds: {e}")

        logger.info("    ℹ️ Odds não encontradas para este fixture.")
        return {}

    # -----------------------
    # Utilitários
    # -----------------------
    @staticmethod
    def _deep_get(dct: Dict[str, Any], path: List[str]):
        """
        Acessa dct conforme a lista de chaves (segura). Retorna None se não encontrar.
        Ex: _deep_get(data, ['goals','for','total','average'])
        """
        node = dct
        try:
            for p in path:
                if node is None:
                    return None
                if isinstance(node, list):
                    # pega primeiro elemento se lista
                    node = node[0]
                node = node.get(p)
            return node
        except Exception:
            return None
