# Coach System Updates v6

Inclui as afinações combinadas:

## Daily Coach
- Corre às 08:20 Portugal no horário de verão (`20 7 * * *`).
- Mantém fallback OpenAI para evitar quedas para heurística.
- Sábado/domingo: inclui automaticamente alternativa indoor/rolo de 90 min.
- Reconhece substituição válida de fim de semana:
  - sábado 2h -> 75-90 min indoor estruturado pode contar como versão curta cumprida;
  - domingo social -> 90 min indoor com carga razoável pode contar como substituição válida.
- Treino falhado não vira dívida: não recomenda compensar automaticamente no dia seguinte.
- Relatório passa a mostrar uma leitura de ontem, não apenas TSS/duração.

## Weekly Planner
- Corre à segunda às 08:40 Portugal no horário de verão (`40 7 * * 1`).
- Domingo social acima de TSS não força recovery week sozinho.
- Deteta `NO BIKE WEEK`, `SEM BIKE`, `SEM BICICLETA`, `FÉRIAS SEM BIKE`, etc. em eventos/holiday do Intervals.
- Se a semana atual for NO BIKE WEEK: não cria treinos de bicicleta.
- Se a semana anterior foi NO BIKE WEEK: cria uma semana de reentrada progressiva.
- Corrige a sessão `Z2 60min + 3x1min` para duração real de 60 min.

## Ficheiros a substituir no repo
- `daily_coach_agent.py`
- `weekly_planner_agent.py`
- `.github/workflows/daily_coach.yml`
- `.github/workflows/weekly_planner.yml`

Mantém `AUTO_APPLY=false` e `WEEKLY_AUTO_APPLY=false` enquanto validamos.
