# Coach System Updates v7.32

Correção de versionamento: esta versão substitui a v7.31 como pacote novo.

## Alteração principal

Daily Coach: quando o treino planeado é VO2, as alternativas práticas de 60/45 min deixam de sugerir tempo/Sweet Spot e passam a manter estímulo VO2 reduzido.

Antes, em dias VO2, podia aparecer:
- 60 min: 2x12 tempo/SS baixo @85–88%
- 45 min: 2x8 tempo/SS baixo @85–88%

Agora, em dias VO2, aparece:
- 60 min: versão curta de VO2, por exemplo 3x3 ou 3x4
- 45 min: versão mínima de VO2, por exemplo 2x3 ou 2x4
- indoor/rolo: cadência alta, ventilação, cortar repetição se o ERG prender

## Exemplos

Para `VO2max introdução — 4 x 3 min @110%`:
- 60 min: 10–15 min aquecer, 3x3 min VO2 @108–110%, resto Z2 e cooldown.
- 45 min: 10 min aquecer, 2x3 min VO2 @108–110%, resto Z2 e cooldown.

Para `VO2 4 x 4`:
- 60 min: 3x4 min VO2.
- 45 min: 2x4 min VO2.

## Ficheiros alterados

- `daily_coach_agent.py`

Weekly não foi alterado nesta versão.
