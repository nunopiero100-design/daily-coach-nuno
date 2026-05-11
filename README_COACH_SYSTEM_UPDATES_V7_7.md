# Coach System Updates v7.7

Correção ao Weekly Planner.

## Problema corrigido

Depois de mudar `PLAN_START_DATE` para `2026-06-01`, o Weekly Planner corrido antes dessa data gerava:

- Semana -2 / Semana -1 / Semana 0
- uma proposta de plano Coach Nuno antes do início real
- nota antiga a dizer `target_week_start=2026-05-11`
- nota antiga a dizer Daily às 08:00

## Novo comportamento

Se `week_start < PLAN_START_DATE`:

- modo: `PRÉ-PLANO / FasCat em observação`
- não gera treinos do plano Coach Nuno
- não aplica nada ao Intervals
- mantém apenas:
  - análise da semana anterior
  - wellness mais recente
  - motivos/observações
- diz que a semana 1 começa em `PLAN_START_DATE`

## Ficheiro principal alterado

- `weekly_planner_agent.py`

O `daily_coach_agent.py` vem no zip para manter o pacote alinhado, mas a alteração principal é no Weekly.
