# Coach System Updates v7.17

Correção de wording/lógica para dias Z2 após carga alta.

## Base

Esta versão foi criada a partir da v7.16 atual.

## Problema corrigido

Quando havia treino Z2 planeado após carga alta, o relatório dizia:

`Dia de descanso após carga alta`

Isto era incorreto porque havia treino planeado.

## Novo comportamento

Se houver treino fácil/Z2 planeado:

`Dia fácil/Z2 após carga alta: foco em recuperação ativa e aeróbico leve, não em cortar hidratos agressivamente.`

Se não houver treino planeado:

`Dia de descanso após carga alta: foco em recuperação, não em cortar hidratos agressivamente.`

## Ficheiro principal alterado

- `daily_coach_agent.py`
