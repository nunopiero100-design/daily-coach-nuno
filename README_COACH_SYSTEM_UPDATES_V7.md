# Coach System Updates v7

Alterações principais:

## Daily Coach
- Horário: 08:20 Portugal no horário de verão (`cron: "20 7 * * *"`).
- Se faltarem dados essenciais de hoje (`sleep_hours`, `hrv`, `resting_hr`):
  - não chama a OpenAI para decisão de treino;
  - não altera Intervals;
  - envia relatório com: "Dados incompletos: atualiza/sincroniza os dados no Intervals e corre manualmente".
- Inclui secção `PESO / FUELING`:
  - peso de hoje;
  - média 7 dias;
  - objetivo 74 kg;
  - orientação de hidratos/proteína/défice conforme tipo de treino.
- Mantém regras:
  - alternativa indoor automática sábado/domingo;
  - treino falhado não vira dívida;
  - substituição indoor/versão curta válida ao fim de semana;
  - domingo social com carga real é interpretado com contexto.

## Weekly Planner
- Horário: segunda-feira 08:40 Portugal no horário de verão (`cron: "40 7 * * 1"`).
- Mantém:
  - NO BIKE WEEK via Holiday;
  - re-entry week;
  - domingo social alto não força recovery week sozinho.

## Ficheiros a substituir
- `daily_coach_agent.py`
- `weekly_planner_agent.py`
- `.github/workflows/daily_coach.yml`
- `.github/workflows/weekly_planner.yml`

Recomendado por agora:
- `AUTO_APPLY=false`
- `WEEKLY_AUTO_APPLY=false`
