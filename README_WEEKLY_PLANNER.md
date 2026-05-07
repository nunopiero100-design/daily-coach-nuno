# Weekly Planner Agent

Segundo workflow do Daily Coach.

## O que faz

À segunda-feira:
1. Lê semana anterior no Intervals
2. Compara planeado vs realizado
3. Lê último wellness disponível
4. Decide se a semana deve ser normal, reduced ou recovery
5. Cria a semana no Intervals com ZWO, se autorizado
6. Envia e-mail com o plano

## Ficheiros a adicionar

- `weekly_planner_agent.py`
- `.github/workflows/weekly_planner.yml`
- `README_WEEKLY_PLANNER.md`

## Secrets opcionais novos

- `WEEKLY_AUTO_APPLY` = `false`
- `PLAN_START_DATE` = `2026-05-11`
- `PLAN_ID` = `coach-pro-nuno-12w-domingo-generico-150tss-v1`

Se não existirem, o script usa estes defaults.

## Teste manual

Actions → Weekly Planner Agent → Run workflow

- apply = false
- target_week_start vazio

Para aplicar manualmente:
- apply = true

## Automático

Corre à segunda-feira às 08:15 Portugal no horário de verão.

No inverno, muda no cron:
- verão: `15 7 * * 1`
- inverno: `15 8 * * 1`
