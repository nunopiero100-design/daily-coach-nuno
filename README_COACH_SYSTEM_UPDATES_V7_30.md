# Coach System Updates v7.30

Afinação do Weekly Coach sobre a v7.29.

## Objetivo

Manter a nova lógica da v7.29:

- ler o plano real no Intervals;
- sugerir ajuste semanal sobre esse plano real;
- não voltar ao template antigo;
- não aplicar automaticamente ainda.

Mas melhorar wording e leitura do relatório.

## Melhorias

### 1. Motivos do ajuste mais claros

Antes podia dizer:

`Carga sem contar domingo também ficou alta...`
`Redução moderada: a carga extra não veio só do domingo.`

Agora explica melhor:

`Semana total ficou +X% vs planeado, mas a carga ficou concentrada antes de domingo: sem domingo, A vs B TSS.`

E:

`Redução leve/moderada para entrar na semana com margem, sem transformar a semana em recovery.`

### 2. Ajuste semanal mais específico

Quando a sugestão ajustada é leve/moderada, o cabeçalho pode mostrar:

- `reduced_light`
- `reduced_moderate`
- `reduced`

em vez de apenas `reduced`.

### 3. Mostra a redução sugerida

Na secção PLANO DA SEMANA aparece, por exemplo:

`Redução sugerida: -56 TSS | -12% vs calendário atual (462 → 406 TSS).`

## Aplicação automática

Continua igual à v7.29:

- sugestões sobre calendário atual são apenas relatório;
- o Weekly não substitui treinos automaticamente nesta versão.

## Ficheiro alterado

- `weekly_planner_agent.py`

Daily não foi alterado.
