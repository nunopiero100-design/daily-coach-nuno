# Daily Coach Backend — Docker

Este documento explica como construir e correr a API do Daily Coach em Docker.

---

## 1. Build

Na raiz do repositório:

```bash
docker build -t daily-coach-api .
```

---

## 2. Run local

```bash
docker run --rm \
  -p 8000:8000 \
  -e APP_TOKEN=test-token \
  daily-coach-api
```

Abrir:

```text
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/health
```

Endpoint protegido sem token:

```bash
curl -i http://localhost:8000/api/v1/reports
```

Esperado:

```text
401 Unauthorized
```

Endpoint protegido com token:

```bash
curl -i \
  -H "Authorization: Bearer test-token" \
  http://localhost:8000/api/v1/reports
```

---

## 3. Persistir dados localmente

Para manter relatórios e feedback fora do container, cria a pasta local:

```bash
mkdir -p data
```

Depois corre o container com volume:

```bash
docker run --rm \
  -p 8000:8000 \
  -e APP_TOKEN=test-token \
  -e DATA_DIR=/app/data \
  -v "$(pwd)/data:/app/data" \
  daily-coach-api
```

Isto guarda dados em:

```text
data/reports/
data/feedback/
```

---

## 4. Variáveis de ambiente

Mínimo para a API:

```text
APP_TOKEN
DATA_DIR
```

Exemplo:

```text
APP_TOKEN=test-token
DATA_DIR=/app/data
```

Necessárias futuramente para executar o Daily Coach dentro do backend:

```text
INTERVALS_API_KEY
ATHLETE_ID
OPENAI_API_KEY
OPENAI_MODEL
AUTO_APPLY
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
TO_EMAIL
FROM_EMAIL
```

---

## 5. Segurança

- Não copiar `.env` para a imagem.
- Não commitar secrets.
- Não usar `test-token` em produção.
- Montar `data/` como volume se quiser persistência.
- Em produção, configurar `APP_TOKEN` no painel do serviço de deploy.
- A app Android nunca deve receber `INTERVALS_API_KEY`, `OPENAI_API_KEY` ou credenciais SMTP.
