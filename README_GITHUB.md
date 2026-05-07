# Daily Coach Nuno — GitHub Actions

Este repositório corre o Daily Coach Agent automaticamente via GitHub Actions.

## O que faz

Todos os dias:
1. Lê wellness do Intervals.icu: sono, HRV, resting HR, Fitness/Fatigue/Form
2. Lê atividades recentes
3. Lê treino planeado de hoje
4. Valida ontem: planeado vs realizado
5. Decide VERDE / AMARELO / VERMELHO
6. Opcionalmente substitui o treino no Intervals

## Secrets necessários

Em GitHub:

Settings → Secrets and variables → Actions → New repository secret

Criar:

- `INTERVALS_API_KEY`
- `ATHLETE_ID` = `i181951`
- `OPENAI_API_KEY`
- `OPENAI_MODEL` = `gpt-5-mini`
- `AUTO_APPLY` = `false`

Começa com `AUTO_APPLY=false`.

## Como testar manualmente

No GitHub repo:

Actions → Daily Coach Agent → Run workflow

Mantém:

- apply = false

Depois abre a execução e vê:

- Summary
- Artifact `daily-coach-report`

## Ligar alterações automáticas

Só depois de alguns testes.

Muda secret:

`AUTO_APPLY=true`

A execução agendada passa a poder alterar treinos quando correr com `--auto`.

Em execução manual, também podes usar:

- apply = true

## Horário

O workflow está em:

```yaml
cron: "5 6 * * *"
```

Isto é 06:05 UTC.

Em Portugal:
- verão: 07:05
- inverno: 06:05

No inverno, se quiseres 07:05 local, muda para:

```yaml
cron: "5 7 * * *"
```

## Segurança

- Nunca metas keys nos ficheiros.
- Usa apenas GitHub Secrets.
- O script não altera nada se já houver atividade concluída hoje.
- O script só substitui treinos com `external_id`, para reduzir risco de duplicados.
