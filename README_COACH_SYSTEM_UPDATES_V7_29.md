# Coach System Updates v7.29

Weekly Coach agora sugere ajustes sobre o plano real que já está no Intervals.

## Problema

A v7.28 passou a respeitar o calendário atual do Intervals, mas quando a semana anterior vinha alta,
o Weekly apenas dizia que havia `reduced/recovery` e deixava tudo para o Daily.

Isso era pouco "coach semanal": o Weekly deve ajustar a dose da semana, mas sem voltar ao template antigo.

## Novo comportamento

Se a semana atual já tem treinos no Intervals:

1. O Weekly lê esses treinos.
2. Calcula o ajuste semanal (`normal`, `reduced`, `recovery`, etc.).
3. Se o ajuste for `reduced` ou `recovery`, gera um plano ajustado sugerido a partir dos treinos reais do calendário.
4. Preserva dias e intenção dos treinos.
5. Não aplica automaticamente nesta versão.

Exemplo de lógica:

- SS/Threshold/Tempo: cortar 1 bloco ou baixar dose 10–15%.
- VO2: cortar 1 repetição ou baixar dose 10–15%.
- Z2 curto: manter.
- Endurance longo/social: manter intenção, mas reduzir carga/cap.
- Recovery: converter qualidade para recovery/Z2 muito fácil.

## Novo relatório

Quando o Weekly sugerir ajuste, aparece:

`Fonte plano da semana: calendário atual do Intervals + ajuste semanal sugerido pelo Weekly.`

E cada treino ajustado mostra:

`AJUSTADO — nome | novo TSS | nova duração (original X TSS | Y duração) — nota`

## Aplicação automática

Nesta versão é propositalmente só sugestão:

`WEEKLY_AUTO_APPLY=true` NÃO aplica `calendar_adjusted_suggestion`.

Isto é para testarmos primeiro se as sugestões são boas.

## Nova variável opcional

Default:

```text
WEEKLY_SUGGEST_ADJUST_CURRENT_PLAN=true
```

Se quiseres voltar ao comportamento v7.28, define:

```text
WEEKLY_SUGGEST_ADJUST_CURRENT_PLAN=false
```

## Ficheiro alterado

- `weekly_planner_agent.py`

Daily não foi alterado.
