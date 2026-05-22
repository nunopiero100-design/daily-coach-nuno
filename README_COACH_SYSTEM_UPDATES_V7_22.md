# Coach System Updates v7.22

Correção da v7.21: OpenAI reasoning effort agora é passado corretamente.

## Problema

Na v7.21, o Daily lia:

- `OPENAI_REASONING_EFFORT`

mas a variável não era passada corretamente para `call_openai()`.
Resultado: a chamada OpenAI podia falhar e o relatório vinha com:

`Fonte decisão: heuristic`

## Correção

- `call_openai(openai_key, model, reasoning_effort, context)`
- Responses API usa `reasoning_effort`
- Chat Completions fallback também usa `reasoning_effort`
- Se OpenAI falhar, o relatório mantém uma nota técnica nos motivos

## Extra

Em dias sem treino planeado + sinais ligeiros de fadiga, a opção dos 60 min foi corrigida para:

`Se tiveres 60 min disponíveis: não é preciso usar os 60; faz 30–45 min recovery muito fácil ou descansa.`

## Secrets recomendados

```text
OPENAI_MODEL=gpt-5.5
OPENAI_REASONING_EFFORT=medium
```

Para teste manual:

```text
OPENAI_REASONING_EFFORT=high
```

## Ficheiro principal alterado

- `daily_coach_agent.py`

O Weekly continua igual.
