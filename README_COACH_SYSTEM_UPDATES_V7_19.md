# Coach System Updates v7.19

Correção de motivos contraditórios com o compliance de ontem.

## Problema corrigido

Quando ontem estava:

- Estado: CUMPRIDO
- Planeado: 103 TSS / 2h00
- Realizado: 104 TSS / 2h00
- Leitura: dentro de margem normal

a OpenAI ainda podia escrever nos motivos:

- "ontem foi ligeiramente acima da carga planeada"

Isto era incorreto.

## Novo comportamento

Se o compliance determinístico de ontem for `CUMPRIDO` dentro da margem:

- remove motivos que digam que ontem foi acima/mais duro/excesso;
- acrescenta, se necessário:
  - `Ontem o treino ajustado foi cumprido dentro da margem; a cautela vem da carga acumulada recente, não de excesso ontem.`

## Ficheiro principal alterado

- `daily_coach_agent.py`
