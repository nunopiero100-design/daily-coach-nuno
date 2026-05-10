# Coach System Updates v7.3

Correção pequena ao Daily Coach v7.2.

## Problema corrigido

A OpenAI por vezes gerava uma alternativa com wording estranho, por exemplo:

- `If só tiveres 45 min...`

A v7.2 acrescentava as alternativas corretas, mas não removia esta linha antiga. Isso criava duplicados.

## Alterações

- Remove alternativas antigas mesmo que venham com wording misto português/inglês.
- Remove linhas duplicadas de 45/60/90 min, indoor/rolo e sábado/domingo.
- Mantém uma única linha de `Recuperação/fueling`, sempre no fim.
- Continua a forçar:
  - 45 min realistas
  - 60 min realistas
  - 90 min indoor realistas
  - intensidade 80–88%, sem transformar plano B em FTP

## Ficheiro principal alterado

- `daily_coach_agent.py`
