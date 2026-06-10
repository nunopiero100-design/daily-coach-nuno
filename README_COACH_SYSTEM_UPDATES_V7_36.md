# Coach System Updates v7.36

Afinação sobre a v7.35.

## Correção

A v7.35 já corrigia o `FUELING` curto, mas a linha `Form pré-treino` ainda podia mostrar o mesmo valor reportado pelo Intervals quando `readiness_form` vinha igual ao valor projetado.

Motivo:
- Para o relatório curto, usar apenas `readiness_form` não era suficientemente robusto.
- Quando existem `readiness_fitness_ctl` e `readiness_fatigue_atl`, o valor mais claro para o atleta é calcular a Form pré-treino diretamente: `readiness_fitness_ctl - readiness_fatigue_atl`.

## Novo comportamento

O relatório diário passa a mostrar `Form pré-treino` calculada assim:

1. Se existirem `readiness_fitness_ctl` e `readiness_fatigue_atl`, usa `CTL pré-treino - ATL pré-treino`.
2. Se não existirem, usa `readiness_form`.
3. Se também não existir, usa `form`.

Também foi afinada a linha `AÇÃO` para treinos Z2 puros:
- Em vez de repetir texto variável da OpenAI, o relatório curto usa uma frase fixa e limpa:
  `90 min Z2 real. HR controlada, RPE baixo, sem perseguir TSS.`

## Mantido da v7.35

- `FUELING` curto e específico ao tipo de treino.
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
