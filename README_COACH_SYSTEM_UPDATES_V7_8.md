# Coach System Updates v7.8

Correção ao Daily Coach para treinos Z2/endurance.

## Problema corrigido

Quando o treino planeado era `Zone 2: 1.5 hours`, o agente ainda gerava alternativas de 45/60 min com tempo/sweet spot e dizia que o dia era de qualidade/intensidade.

Isso estava errado.

## Novo comportamento

Se o treino planeado contém:
- Zone 2
- Z2
- Endurance
- Recovery
- fácil/easy

Então:
- plano normal mantém Z2;
- 60 min = Z2/recovery, sem blocos;
- 45 min = recovery/Z2 muito fácil ou descanso;
- indoor = Z2 fácil, sem transformar em tempo/SS;
- fueling = 30–45 g CH/h para Z2 75–120 min, não 60–80 g/h obrigatório.

## Ficheiro principal alterado

- `daily_coach_agent.py`
