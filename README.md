# Football Value Detector (Over 1.5)

## Variáveis de ambiente necessárias
- `API_FOOTBALL_KEY` — chave para v3.football.api-sports.io (obrigatório para dados reais)
- `DAYS_TO_ADD` — (opcional) dias a adicionar à data de hoje para buscar (default 5)
- `LEAGUES` — (opcional) lista CSV de league IDs. Se vazio, usa TOP_20_LEAGUES
- `ANALYSIS_INTERVAL_HOURS` — (opcional) intervalo entre análises (default 4)
- `SEASON` — (opcional) temporada (ex.: 2024)

## Como executar localmente
1. `pip install -r requirements.txt`
2. Defina `API_FOOTBALL_KEY` no ambiente.
3. `python -m src.main`

## No Render
- Use `Procfile` acima.
- Defina `API_FOOTBALL_KEY` nas environment variables do deploy.
- Porta padrão configurada pelo Render (usamos `$PORT` no Procfile).

