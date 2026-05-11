# Daily Coach Backend — Docker

Este documento explica como construir e correr a API do Daily Coach em Docker.

---

## Build

Na raiz do repositório:

```bash
docker run --rm \
  -p 8000:8000 \
  -e APP_TOKEN=test-token \
  -e DATA_DIR=/app/data \
  -v "$(pwd)/data:/app/data" \
  daily-coach-api