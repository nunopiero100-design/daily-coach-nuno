# Coach System Updates v7.2

Polimento das alternativas práticas do Daily Coach.

## Correções

- A alternativa de 45 min agora cabe em 45 min.
- A alternativa de 60 min agora cabe em 60 min.
- A alternativa indoor de fim de semana agora cabe em 90 min.
- O plano B indoor usa tempo/SS baixo, normalmente 80–88%, não FTP.
- O script pós-processa as ações da OpenAI para evitar contas de duração erradas.

## Exemplos

VERDE / treino de qualidade:
- 60 min: 10 min aquecer, 2x12 min @85–88%, 6 min Z2, resto Z2, 5 min arrefecer.
- 45 min: 10 min aquecer, 2x8 min @85–88%, 5 min Z2, 9 min Z2, 5 min arrefecer.
- fim de semana indoor 90 min: 15 min aquecer, 3x12 min @85–88%, 6 min Z2, completar Z2, 10 min arrefecer.

AMARELO:
- alternativas mais leves, 80–85%, mais Z2.

VERMELHO:
- descanso ou recovery/Z2.

## Ficheiro principal alterado

- `daily_coach_agent.py`
