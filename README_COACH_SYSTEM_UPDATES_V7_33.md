# Coach System Updates v7.33

Afinação sobre a v7.32.

## Correção

A v7.32 já corrigia as alternativas de 60/45 min para treinos VO2, mas a linha `Se for indoor/rolo` podia desaparecer do relatório.

Motivo:
- O filtro de recuperação/fueling removia qualquer linha que contivesse palavras como `recuperações`, `fuel` ou `hidratação`.
- A linha indoor de VO2 tinha texto como `Recuperações mesmo fáceis`, então era removida por engano.

## Novo comportamento

Em dias VO2, as ações devem mostrar:

- Plano normal
- Se só tiveres 60 min
- Se só tiveres 45 min
- Se for indoor/rolo
- Recuperação/fueling

## Mantido da v7.32

Quando o treino planeado é VO2:
- 60 min passa a versão curta de VO2, por exemplo 3x3 ou 3x4.
- 45 min passa a versão mínima de VO2, por exemplo 2x3 ou 2x4.
- Não sugere tempo/Sweet Spot em dias VO2.

## Ficheiros alterados

- `daily_coach_agent.py`

Weekly não foi alterado.
