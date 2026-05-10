# Coach System Updates v7.4

Ajuste de lógica para chuva/fim de semana.

## Regra nova

- Se for sábado/domingo e o treino planeado tiver até 2h:
  - não cria alternativa indoor de 90 min;
  - diz apenas para fazer o treino planeado indoor/rolo se chover ou as condições forem desfavoráveis.
- Só cria alternativa indoor de 90 min se o treino planeado for:
  - acima de 2h;
  - social ride;
  - group ride;
  - endurance longo / saída outdoor longa.

## Exemplo

Treino de 1h45 indoor/endurance/tempo:
- Faz o treino como planeado.
- Se chover: faz o treino indoor/rolo como planeado.

Domingo social 3h/150 TSS:
- Se chover: alternativa indoor 90 min estruturada.

## Ficheiro principal alterado

- `daily_coach_agent.py`
