# Coach System Updates v7.10

Correção ao Daily Coach para AMARELO forte em treino longo/de qualidade.

## Problema corrigido

Num cenário como:

- Ontem: FEITO MAS MAIS DURO / acima do planeado
- Hoje: Sweet Spot Group Ride 3h / carga muito alta
- HRV abaixo do baseline
- Form muito negativa

O agente dizia AMARELO, mas recomendava uma redução demasiado pequena:
- reduzir 3%
- cortar um bloco

Isto era brando demais.

## Novo comportamento

Se for AMARELO forte com treino longo/de qualidade:

- não fazer o treino longo/de qualidade como planeado;
- substituir por 90–120 min Z2 fácil/endurance;
- sem blocos, sem sweet spot, sem perseguir TSS;
- descanso total se as pernas estiverem pesadas;
- group ride só se for possível ficar em Z2 e cortar cedo.

## Ficheiro principal alterado

- `daily_coach_agent.py`
