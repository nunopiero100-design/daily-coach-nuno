# Coach System Updates v7.13

Correção ao uso de CTL/ATL/Form no Daily Coach.

## Problema corrigido

A v7.12 corrigia a Form/TSB, mas ainda deixava Fitness/CTL e Fatigue/ATL reportados como se fossem sempre pré-treino.

No Intervals.icu, quando existe treino planeado hoje e ainda não há atividade feita, estes valores podem estar projetados com o treino planeado de hoje.

## Novo comportamento

O Daily passa a mostrar:

- Fitness/CTL reportada e Fitness/CTL pré-treino usada
- Fatigue/ATL reportada e Fatigue/ATL pré-treino usada
- Form reportada e Form pré-treino usada

Regra:
- se há treino planeado hoje e ainda não há atividade concluída hoje, usa os valores de ontem como proxy pré-treino;
- se já há atividade feita hoje, usa os valores de hoje;
- se não houver valores de ontem, usa os reportados.

## Exemplo de relatório

`Fitness/CTL reportada: 67 | pré-treino usada: 66 | Fatigue/ATL reportada: 82 | pré-treino usada: 75 | Form reportada: -15 | pré-treino usada: -9`

## Ficheiro principal alterado

- `daily_coach_agent.py`
