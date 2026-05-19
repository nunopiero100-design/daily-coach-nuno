# Coach System Updates v7.16

Pequena correção de wording no Daily Coach.

## Base

Esta versão foi criada a partir da v7.15.

## Problema corrigido

A frase antiga dizia:

`Se HRV/sono piorarem ou a potência cair, não apertar dieta: primeiro recuperar.`

Num relatório diário isso era confuso, porque HRV e sono já foram medidos antes do relatório.

## Novo wording

`Nos próximos relatórios, se HRV/sono baixarem ou potência/RPE ficarem anormais, reduzir défice e priorizar recuperação.`

## Nota

A lógica experimental anterior de "não reduzir duas vezes pelo nome do treino" foi descartada.
No futuro, isso deve ser resolvido com marcador explícito `DAILY_COACH_ADJUSTED`, não por heurística no nome.

## Ficheiro principal alterado

- `daily_coach_agent.py`
