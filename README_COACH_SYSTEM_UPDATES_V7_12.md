# Coach System Updates v7.12

Correção importante ao uso de Form/TSB no Daily Coach.

## Problema corrigido

No Intervals.icu, a Fitness/Fatigue/Form reportada para o dia pode incluir o treino planeado desse mesmo dia.
Nesse caso, se ainda não há atividade feita hoje, a Form pode ser uma projeção pós-treino planeado e não a readiness real pré-treino.

## Novo comportamento

O Daily passa a mostrar e usar:

- `Form reportada`
- `Form pré-treino usada`

Regra:
- se há treino planeado hoje e ainda não há atividade concluída hoje, usa a Form de ontem como proxy de Form pré-treino;
- se já há atividade feita hoje, usa a Form de hoje;
- se não houver Form de ontem, usa a reportada.

## Exemplo de relatório

`Fitness/CTL: 67 | Fatigue/ATL: 82 | Form reportada: -15 | Form pré-treino usada: -9`

## Ficheiro principal alterado

- `daily_coach_agent.py`
