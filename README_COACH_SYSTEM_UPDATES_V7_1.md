# Coach System Updates v7.1

Correção pequena ao Daily Coach v7.

## Alterações

Quando o agente é corrido depois de uma atividade já feita hoje:

- Estado continua: `JÁ FEITO`
- Não mostra alternativa indoor de fim de semana
- Não mostra fueling pré/durante treino
- A secção `PESO / FUELING` passa a ser pós-treino:
  - recuperação
  - proteína
  - hidratos suficientes
  - sem défice agressivo se foi treino de qualidade
- Ações passam a ser:
  - não repetir treino
  - recuperar/hidratar/comer
  - monitorizar sono/HRV amanhã

## Ficheiro principal alterado

- `daily_coach_agent.py`

Os workflows e o weekly planner mantêm a versão v7.
