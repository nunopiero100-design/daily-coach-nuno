# Coach System Updates v7.35

Afinação sobre a v7.34.

## Correção

A v7.34 voltou a mostrar o `Coach Recovery Score` e encurtou o relatório diário, mas ainda havia dois pontos a afinar.

Motivo:
- A linha `Form` podia mostrar o valor reportado/projetado do Intervals, em vez do valor pré-treino usado para decisão.
- A linha `FUELING` podia ficar demasiado genérica, por exemplo `ajustar ao treino; proteína suficiente e hidratação`.

## Novo comportamento

O relatório diário passa a mostrar:

- `Form pré-treino`, usando `readiness_form` quando disponível.
- `FUELING` curto mas específico ao tipo de treino.

Exemplos:
- Z2 75–120 min: `30–45 g/h se precisares; água/eletrólitos. Proteína suficiente no dia.`
- Z2 longo: `40–60 g/h; água/eletrólitos. Proteína suficiente no dia.`
- Qualidade >75 min: `50–70 g/h; água/eletrólitos. 30–40 g proteína no pós.`

## Mantido da v7.34

- Relatório TXT curto.
- Coach Recovery Score calculado localmente pelo script.
- Mais detalhe mantido no JSON para auditoria.
- O bloco `EMAIL` continua a aparecer apenas depois do envio/log, não no corpo do e-mail enviado.

## Mantido da v7.33

Em dias VO2, as ações continuam a mostrar:

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
