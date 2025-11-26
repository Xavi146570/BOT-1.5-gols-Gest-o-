# Football Value Detector (Over 1.5)

Projeto que detecta oportunidades de value betting para mercados Over 0.5 / Over 1.5.

## Variáveis de ambiente necessárias
- `API_FOOTBALL_KEY` — chave para v3.football.api-sports.io (obrigatório)
- `DAYS_TO_ADD` — dias a adicionar à data de hoje para buscar (default 5)
- `LEAGUES` — lista CSV de league IDs (ex.: "39,140,78") — se vazio usa TOP_20_LEAGUES
- `ANALYSIS_INTERVAL_HOURS` — intervalo entre análises (default 4)
- `SEASON` — temporada usada para estatísticas (default 2024)
- `PORT` — porta (p/ Docker / Render)

## Deploy local
1. `pip install -r requirements.txt`
2. Exporta `API_FOOTBALL_KEY`
3. `python -m src.main`

## Deploy no Render
1. Subir repo ao GitHub.
2. Adicionar `render.yaml` ao repo e apontar `repo` no ficheiro ou configurar manualmente no dashboard.
3. Definir variable `API_FOOTBALL_KEY` no dashboard do serviço.
4. Deploy — o serviço executa o scheduler e expõe `/` e `/run`.

## Notas
- O sistema tenta usar dados reais; se a API falhar, usa fallbacks controlados.
- Para produção real, recomendo:
  - usar um job scheduler externo (p.ex. cron / Cloud scheduler) em vez de `threading.Timer`
  - armazenar DB num serviço gerido se vários workers forem usados
  - rever limites de rate da API e ajustar `ANALYSIS_INTERVAL_HOURS` e `LEAGUES`
