# Coach System Updates v7.25

Versão limpa após discussão sobre `plan_events.csv`.

## Decisão

Não usar `plan_events.csv` / snapshot original como fonte do Weekly.

Motivo:
Se o Daily ajustar treinos no Intervals, o plano original deixa de representar a verdade atual do calendário.
Usar snapshot antigo poderia induzir erro, por exemplo comparando um treino ajustado de 35 TSS contra um treino original de 105 TSS.

## Fonte de verdade

A fonte de verdade passa a ser:

`Calendário atual do Intervals`

Regra operacional:

`Não remover treinos planeados depois do facto.`

Se um treino não for feito, deixar o treino no calendário.
Se for movido, mover o treino planeado.
Se o Daily ajustar, o treino ajustado fica no calendário e passa a ser a verdade para o Weekly.

## O que fica da v7.24

Mantida a melhoria do Daily:

- em dias sem treino planeado, se os últimos 3 dias ainda incluem carga concentrada, o Daily evita sugerir 45–60/60 min Z2 como se nada tivesse acontecido;
- prefere descanso total ou 30–45 min recovery muito fácil;
- evita frases tipo “sem carga a compensar” quando ainda há carga recente no sistema.

Mantidas as melhorias do Weekly da v7.23:

- `CUMPRIDA`
- `CUMPRIDA, MAS ACIMA DO PLANEADO`
- `ACIMA DO PLANEADO`
- `MUITO ACIMA DO PLANEADO`
- linha `Desvio: +/- X TSS | +/-Y% vs planeado`

## Ficheiros alterados

- `daily_coach_agent.py`
- `weekly_planner_agent.py`

## Notas

Não é preciso adicionar `plan_events.csv` ao repo.
Não definir `WEEKLY_PLANNED_EVENTS_FILE`.
