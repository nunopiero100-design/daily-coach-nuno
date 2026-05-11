# Coach System Updates v7.6

Correção ao Daily Coach após relatório de 2026-05-11.

## Problemas corrigidos

1. Ontem aparecia:
   - Planeado: 78 TSS / 1h45
   - Realizado: 77 TSS / 1h45
   - Estado: VERSÃO CURTA CUMPRIDA

   Isto estava errado. Agora, se carga e duração estiverem próximas do plano:
   - Estado: CUMPRIDO

2. Em dias sem treino planeado, as opções de 45/60 min agora aparecem como:
   - "Se quiseres rolar..."
   - e não como alternativas de treino.

3. Peso/fueling:
   - "faltam X kg" passa a dizer claramente que é pela média 7d.
   - se o peso do dia estiver muito abaixo da média, avisa que pode ser oscilação/hidratação.

## Ficheiro principal alterado

- `daily_coach_agent.py`
