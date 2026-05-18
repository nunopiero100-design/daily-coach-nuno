# Coach System Updates v7.11

Afinação ao Daily Coach para o dia seguinte a treino grande.

## Problemas corrigidos

1. Treino de 3h planeado / 3h29 feito e 212 TSS:
   - antes: `CUMPRIDO dentro de margem normal`
   - agora: `CUMPRIDO, mas com carga/duração acima do planeado`

2. Dia de descanso após treino grande:
   - antes podia sugerir `hidratos mais baixos`
   - agora prioriza recuperação:
     - não fazer défice agressivo;
     - hidratos moderados;
     - proteína alta;
     - hidratação/eletrólitos.

3. Sem treino planeado após carga alta:
   - descanso total preferencial;
   - no máximo recovery/Z1-Z2 muito fácil;
   - nada de transformar recuperação em treino.

## Ficheiro principal alterado

- `daily_coach_agent.py`
