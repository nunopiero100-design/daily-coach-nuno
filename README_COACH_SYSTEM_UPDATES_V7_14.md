# Coach System Updates v7.14

Limpeza dos motivos quando CTL/ATL/Form estão projetados.

## Problema corrigido

A v7.13 já mostrava valores reportados e pré-treino usados, mas a OpenAI ainda podia escrever motivos misturados como:

- `fatigue_atl alto (81.79)`
- `form real/reportado -14.5`
- `readiness_form -9.42`

Isto era confuso porque os valores reportados podem incluir o treino planeado de hoje.

## Novo comportamento

Se `metrics_are_projected_after_planned = true`:

- remove motivos que usem CTL/ATL/Form reportados/projetados como se fossem pré-treino;
- acrescenta um motivo limpo:
  - `Valores CTL/ATL/Form reportados podem incluir o treino planeado de hoje; para readiness pré-treino usei CTL X, ATL Y e Form Z.`
- mantém HRV, RHR, sono, carga real recente e compliance de ontem como sinais principais.

## Ficheiro principal alterado

- `daily_coach_agent.py`
