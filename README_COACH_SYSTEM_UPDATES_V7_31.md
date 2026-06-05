# Coach System Updates v7.31

Pequena adição ao Daily Coach: Coach Recovery Score.

## Objetivo

Adicionar um score simples tipo readiness/recuperação, sem alterar a decisão do Daily.

## O que muda no relatório

Na secção DADOS aparece uma nova linha:

`Coach Recovery Score: XX/100 | VERDE/AMARELO/VERMELHO`

## Importante

Este score NÃO muda a decisão do treino.

A lógica continua igual:

- Daily decide VERDE/AMARELO/VERMELHO como antes;
- o score é apenas uma leitura rápida de recuperação;
- OpenAI não usa este score para decidir, porque ele é calculado depois da decisão.

## Fórmula geral

Score composto por:

- HRV vs baseline;
- resting HR vs baseline;
- sleep score / sono;
- carga recente, Form e ontem vs planeado.

## Labels

- 75–100: VERDE
- 60–74: AMARELO LEVE
- 45–59: AMARELO
- <45: VERMELHO

## Ficheiro alterado

- `daily_coach_agent.py`

Weekly não foi alterado.
