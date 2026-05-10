# Coach System Updates v7.5

Correção ao Daily Coach v7.4.

## Problema corrigido

A v7.4 já distinguia:
- treino até 2h → fazer o treino planeado indoor se chover;
- treino acima de 2h/social/long ride → alternativa indoor de 90 min.

Mas ainda existia um bloco antigo que acrescentava uma alternativa de 90 min ao fim de semana mesmo quando o treino tinha só 1h45.

## Alteração

- Removido o bloco antigo de fallback de 90 min.
- A lógica fica exclusivamente:
  - até 2h: “se chover, faz o treino planeado indoor/rolo”
  - acima de 2h/social/group ride/long endurance: alternativa indoor de 90 min

## Ficheiro principal alterado

- `daily_coach_agent.py`
