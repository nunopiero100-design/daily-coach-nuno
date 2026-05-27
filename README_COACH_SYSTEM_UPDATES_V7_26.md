# Coach System Updates v7.26

Pequena afinação de wording no Daily Coach.

## Problema

Em dias Z2/endurance após apenas um treino de qualidade no dia anterior,
o relatório podia dizer:

`Défice leve é aceitável, mas sem sair vazio após dois dias de qualidade.`

Isto era demasiado genérico/impreciso quando só houve um dia de qualidade.

## Novo wording

Passa a dizer algo como:

`Défice leve é aceitável, mas sem sair vazio no dia seguinte a trabalho de qualidade.`

ou, quando não houve qualidade clara:

`Défice leve é aceitável, mas sem sair vazio se houver fadiga acumulada.`

## Lógica

Não muda a decisão de treino.
Não muda o Weekly.

Só melhora precisão do texto de fueling.

## Ficheiro alterado

- `daily_coach_agent.py`
