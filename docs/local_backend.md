# Daily Coach Backend — Local Development

Este documento explica como correr a API local do Daily Coach.

---

## 1. Instalar dependências

```bash
python -m pip install -r requirements.txt
```

---

## 2. Storage local

Por defeito, a API guarda dados em:

```text
data/reports/
data/feedback/
```

É possível alterar a pasta base com:

```bash
export DATA_DIR=data
```

ou:

```bash
DATA_DIR=data APP_TOKEN=test-token PYTHONPATH=. uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. Configurar token local

A API protege os endpoints `/api/v1/...` com Bearer token.

Para teste local:

```bash
export APP_TOKEN=test-token
```

Ou, numa única linha:

```bash
APP_TOKEN=test-token PYTHONPATH=. uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

---

## 4. Arrancar API local

```bash
APP_TOKEN=test-token PYTHONPATH=. uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

Depois abrir:

```text
http://localhost:8000/docs
```

Em GitHub Codespaces, usar o forwarded address da porta 8000.

---

## 5. Endpoints públicos

```http
GET /health
```

Exemplo:

```bash
curl http://localhost:8000/health
```

---

## 6. Endpoints protegidos

Todos os endpoints `/api/v1/...` requerem:

```http
Authorization: Bearer test-token
```

Exemplo:

```bash
curl \
  -H "Authorization: Bearer test-token" \
  http://localhost:8000/api/v1/reports
```

---

## 7. Testar API

```bash
PYTHONPATH=. python scripts/test_api.py
```

O teste define `APP_TOKEN=test-token` automaticamente.

---

## 8. Testar feedback

```bash
PYTHONPATH=. python scripts/test_feedback.py
```

---

## 9. Limpar ficheiros gerados localmente

Os testes podem criar:

```text
tmp/
data/reports/
data/feedback/
```

Limpar:

```bash
rm -rf tmp data
```

Estas pastas estão ignoradas pelo Git.

---

## 10. Notas de segurança

- Não commitar `.env`.
- Não colocar `INTERVALS_API_KEY`, `OPENAI_API_KEY`, SMTP ou tokens reais no código.
- A app Android nunca deve guardar chaves da Intervals, OpenAI ou SMTP.
- Para MVP, a app pode usar `APP_TOKEN`.
- Para produção, substituir por autenticação mais robusta.
