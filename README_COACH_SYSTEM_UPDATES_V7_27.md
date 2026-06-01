# Coach System Updates v7.27

Correção de coerência nas ações do Daily Coach.

## Problema

Quando o estado vinha `AMARELO` após um dia muito acima do planeado, mas o treino de hoje era Z2/endurance longo, o relatório podia dizer:

`Estado: AMARELO — Reduzir o treino de hoje`

mas nas ações começava por:

`Plano normal: fazer Zone 2: 3 hours ...`

Isto era contraditório.

## Novo comportamento

Se:

- estado = `AMARELO`
- treino de hoje = Z2/endurance fácil
- duração planeada >= 1h15
- ontem foi carga alta ou feito mais duro
- ou recent_3d está alto

então o Daily força:

`Plano normal ajustado: não fazer o Z2 longo como planeado; fazer 45–75 min recovery/Z2 muito fácil, sem blocos, ou descanso se as pernas estiverem pesadas.`

E remove opções tipo:

- fazer 3h como planeado
- 2h Z2 bem feitas
- cumprir volume original indoor

## O que não muda

- Weekly não muda.
- A decisão base não muda.
- Só corrige ações contraditórias.

## Ficheiro alterado

- `daily_coach_agent.py`
