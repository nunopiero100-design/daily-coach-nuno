# Coach System Updates v7.34

Afinação sobre a v7.33.

## Correção

A v7.33 mantinha a correção das alternativas VO2 e da linha `Se for indoor/rolo`, mas o relatório diário tinha ficado demasiado comprido e perdeu a linha do `Coach Recovery Score`.

Motivo:
- O relatório TXT estava a imprimir blocos muito longos e repetitivos, especialmente `PESO / FUELING`, `Motivos` e `Ações`.
- O `Coach Recovery Score` deixou de aparecer na secção de dados/readiness, apesar de continuar a existir informação suficiente para calcular o estado do dia.

## Novo comportamento

O relatório diário fica mais curto e passa a mostrar novamente:

- Coach Recovery Score
- Sono
- HRV
- Resting HR
- Peso
- CTL/ATL/Form pré-treino
- Últimos 3 dias
- Decisão curta
- Ação principal
- Fueling curto
- Estado do Intervals

## Mantido da v7.33

Em dias VO2, as ações devem continuar a mostrar:

- Plano normal
- Se só tiveres 60 min
- Se só tiveres 45 min
- Se for indoor/rolo
- Recuperação/fueling

Quando o treino planeado é VO2:
- 60 min continua a ser uma versão curta de VO2, por exemplo 3x3 ou 3x4.
- 45 min continua a ser uma versão mínima de VO2, por exemplo 2x3 ou 2x4.
- Não sugere tempo/Sweet Spot em dias VO2.

## Ficheiros alterados

- `daily_coach_agent.py`

Weekly não foi alterado.
