# Coach System Updates v7.21

Configuração de modelo OpenAI e reasoning effort para o Daily Coach.

## O que mudou

Alterado:

- `daily_coach_agent.py`

Não alterado:

- `weekly_planner_agent.py`

## Porquê o Weekly não mudou?

O `weekly_planner_agent.py` atual não faz chamada à OpenAI.
Ele é determinístico/regras, usa Intervals e o plano, mas não lê `OPENAI_MODEL` nem `OPENAI_API_KEY`.

Portanto, mudar `OPENAI_MODEL` só afeta o Daily Coach neste momento.
Se no futuro quisermos um Weekly com análise OpenAI, isso precisa de uma alteração maior: adicionar uma chamada OpenAI ao weekly.

## Novas variáveis suportadas pelo Daily

No GitHub:

Settings → Secrets and variables → Actions → Repository secrets

Define/atualiza:

```text
OPENAI_MODEL=gpt-5.5
OPENAI_REASONING_EFFORT=medium
```

Para teste manual premium:

```text
OPENAI_REASONING_EFFORT=high
```

## Valores aceites para OPENAI_REASONING_EFFORT

- `minimal`
- `low`
- `medium`
- `high`

Se colocares um valor inválido, o script usa `medium`.

## Recomendação

Para cron diário normal:

```text
OPENAI_MODEL=gpt-5.5
OPENAI_REASONING_EFFORT=medium
```

Para comparação manual ocasional:

```text
OPENAI_REASONING_EFFORT=high
```
