# Coach System Updates v7.15

Correção para treinos mistos: Sweet Spot + Z2.

## Problema corrigido

Um treino chamado:

- `Sweet Spot 2 x 15 min + Z2 cap 200W`

era classificado como Z2/endurance porque continha `Z2` no nome.

Isto estava errado, porque ainda tem blocos Sweet Spot.

## Novo comportamento

- Se o nome tiver Sweet Spot / Threshold / VO2 / Over-Under / Intervals, o treino é qualidade.
- Se também tiver Z2/Endurance no nome, passa a ser `qualidade controlada/mista`.
- Z2 puro continua a ser Z2.
- Fueling para treino misto >75 min:
  - 50–70 g hidratos/h
- Fueling para Z2 puro:
  - 30–45 g/h até 2h
  - 40–60 g/h acima de 2h

## Ficheiro principal alterado

- `daily_coach_agent.py`
