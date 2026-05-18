# Coach System Updates v7.9

Pequena afinação ao Daily Coach para Z2 longo.

## Problema corrigido

A v7.8 tratava bem treinos Z2 de 75–120 min, mas em Z2 de 2h30 ainda dizia:

- 30–45 g hidratos/h

Para 2h30, especialmente indoor ou após dias de qualidade, isto podia ser curto.

## Novo comportamento

Para Z2/endurance:

- 75–120 min: 30–45 g hidratos/h
- >2h: 40–60 g hidratos/h + água/eletrólitos suficientes

Também acrescenta, para sábado/Z2 longo:

- se 2h30 não encaixar, 2h Z2 bem feitas são válidas;
- não perseguir TSS à força.

## Ficheiro principal alterado

- `daily_coach_agent.py`
