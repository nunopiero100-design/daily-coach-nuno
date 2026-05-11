# Daily Coach API — Render Deploy

Este documento explica como fazer deploy da API do Daily Coach no Render usando Docker.

---

## 1. Pré-requisitos

- Conta Render
- Repo GitHub ligado ao Render
- `Dockerfile` no repo
- `render.yaml` no repo

---

## 2. Criar serviço no Render

No Render:

1. New
2. Blueprint
3. Connect GitHub repository
4. Selecionar `daily-coach-nuno`
5. Confirmar o serviço definido em `render.yaml`

O serviço criado deve chamar-se:

`daily-coach-api`

---

## 3. Variáveis de ambiente

Configurar manualmente no Render:

`APP_TOKEN=<token-forte>`

Gerar token forte localmente:

```bash
python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
