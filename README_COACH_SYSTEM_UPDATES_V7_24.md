# Coach System Updates v7.24

Melhorias no Daily e Weekly.

## 1) Weekly — treinos removidos do calendário

Problema:
Se um treino planeado for removido manualmente do Intervals, a API deixa de o devolver.
O Weekly passava a comparar contra um planeado mais baixo e podia dizer "acima do planeado" de forma enganadora.

Novo comportamento:
O Weekly pode usar um snapshot original do plano:

- `WEEKLY_PLANNED_EVENTS_FILE=plan_events.csv`
- ou `WEEKLY_PLANNED_EVENTS_FILE=plan_events.json`

Se não definires a variável, ele tenta usar automaticamente:

- `plan_events.csv`
- `plan_events.json`

quando existirem na raiz do repo.

No relatório aparece:

- `Fonte planeado: calendário atual do Intervals.`
ou
- `Fonte planeado: calendário atual + snapshot original do plano (inclui treinos removidos do calendário).`

Nota:
Para a fase FasCat/pré-plano, se não houver snapshot do plano FasCat, o Weekly só consegue usar o calendário atual.
Para o plano Coach Nuno a partir de 2026-06-01, manter `plan_events.csv` no repo resolve isto.

## 2) Daily — dia sem treino após carga concentrada recente

Problema:
Depois de uma volta grande no sábado e descanso no domingo, a segunda-feira podia dizer:
"sem carga a compensar" ou sugerir 45–60 min Z2.

Novo comportamento:
Se não há treino planeado e os últimos 3 dias ainda incluem carga concentrada (ex: ~180+ TSS / 3h+):

- descanso total preferencial;
- opcional 30–45 min recovery muito fácil;
- não sugerir 60 min como alvo;
- não dizer "sem carga a compensar".

## Ficheiros alterados

- `daily_coach_agent.py`
- `weekly_planner_agent.py`
