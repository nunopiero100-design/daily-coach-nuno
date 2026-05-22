# Coach System Updates v7.20

Correção para dias sem treino planeado com sinais ligeiros de fadiga.

## Problema corrigido

Exemplo real:
- Sem treino planeado
- HRV 48 vs baseline 53.3 (~10% abaixo)
- RHR 48 vs baseline 45 (+3 bpm)
- Sono score 77

A versão anterior podia dizer:
- Estado: VERDE
- Descanso total ou 45–75 min Z2

Isto soava demasiado permissivo.

## Novo comportamento

Se não há treino planeado e aparecem sinais ligeiros de fadiga:

- Estado: AMARELO
- Decisão: descanso total preferencial
- Se quiser rolar: 30–45 min recovery/Z1-Z2 muito fácil
- Não sugerir 60–75 min Z2 como opção principal
- Fueling: défice no máximo leve; proteína alta, hidratação/eletrólitos e hidratos moderados

## Ficheiro principal alterado

- `daily_coach_agent.py`
