# Coach System Updates v7.18

Correção para Z2 puro curto.

## Problema corrigido

Após a v7.17, um treino `Zone 2: 1 hour` passou de VERDE para AMARELO numa nova execução da OpenAI.
Pior: em AMARELO, o agente sugeriu blocos de tempo 80–85%, o que é errado para um dia Z2 puro.

## Novo comportamento

Para treino Z2/recovery/endurance puro e curto, até cerca de 75 min:

- se HRV/RHR/sono estão bons, manter VERDE;
- fazer Z2 fácil, sem blocos;
- não marcar AMARELO apenas por Form/carga acumulada;
- se por algum motivo ficar AMARELO, as ações continuam Z2/recovery;
- nunca sugerir tempo/SS/threshold em alternativa a um Z2 puro.

## Ficheiro principal alterado

- `daily_coach_agent.py`
