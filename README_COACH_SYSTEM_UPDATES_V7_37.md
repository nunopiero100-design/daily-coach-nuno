# Coach System Updates v7.37

Afinação sobre a v7.36.

## Correção

A v7.36 ainda podia mostrar `Form pré-treino: -7` quando o Intervals estava a devolver a Form reportada/projetada do próprio dia.

Motivo:
- A versão curta do relatório já tentava mostrar a Form pré-treino, mas o contexto usado pelo relatório não guardava explicitamente os valores pré-treino.
- Sem esses campos, o relatório acabava por cair no valor `form` do dia, que pode estar projetado com o treino planeado.

## Novo comportamento

O script passa a calcular e guardar explicitamente:

- `readiness_fitness_ctl`
- `readiness_fatigue_atl`
- `readiness_form`
- `metrics_are_projected_after_planned`
- `yesterday_metrics`

Quando há treino planeado hoje e ainda não há atividade concluída, o script usa os dados de ontem como proxy pré-treino, quando disponíveis.

A linha do relatório passa a usar:

1. `readiness_form`
2. Se faltar, `readiness_fitness_ctl - readiness_fatigue_atl`
3. Se também faltar, `form`

## Mantido da v7.36

- Ação curta e limpa para Z2 puro:
  `90 min Z2 real. HR controlada, RPE baixo, sem perseguir TSS.`
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
