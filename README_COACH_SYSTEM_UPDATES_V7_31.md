# Coach System Updates v7.31 VO2 + Score Patch

Patch mínimo sobre a v7.31.

## Correção

Esta versão volta à base v7.31 e mexe apenas em dois pontos.

Motivo:
- Em dias VO2, as alternativas de 60/45 min podiam sair como tempo/Sweet Spot.
- O `Coach Recovery Score` aparecia na secção `DADOS`, mas o objetivo é ficar junto da `DECISÃO`.

## Novo comportamento

Quando o treino planeado é VO2:
- 60 min passa a versão curta de VO2, por exemplo 3x3 ou 3x4.
- 45 min passa a versão mínima de VO2, por exemplo 2x3 ou 2x4.
- A linha `Se for indoor/rolo` mantém estrutura VO2 ou versão curta VO2.
- Não sugere tempo/Sweet Spot em dias VO2.

Na secção `DECISÃO`, passa a aparecer:

- `Coach Recovery Score: XX/100 | VERDE/AMARELO/VERMELHO`
- `Estado: VERDE/AMARELO/VERMELHO`

## Mantido da v7.31

- Relatório longo original.
- Bloco `DADOS`.
- Bloco `PESO / FUELING`.
- Motivos e ações completos.
- Lógica de Intervals/upload.
- Weekly não foi alterado.

## Ficheiros alterados

- `daily_coach_agent.py`
