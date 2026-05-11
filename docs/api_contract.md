# Daily Coach API Contract

API mínima para a futura app Android do Daily Coach.

Esta API serve relatórios estruturados gerados pelo Daily Coach, histórico local e feedback manual do atleta.

---

## Base URL

Em desenvolvimento local:

```text
http://localhost:8000
```

Em GitHub Codespaces:

```text
https://<codespace>-8000.app.github.dev
```

Em produção:

```text
https://<backend-url>
```

---

## Autenticação

Todos os endpoints `/api/v1/...` requerem Bearer token.

Header obrigatório:

```http
Authorization: Bearer <APP_TOKEN>
```

Exceção:

```http
GET /health
```

O endpoint `/health` é público.

---

## Status do relatório

Campo:

```json
{
  "status": "GREEN"
}
```

Valores possíveis:

```text
GREEN
YELLOW
RED
INCOMPLETE
```

Significado:

```text
GREEN       manter plano / dia ok
YELLOW      reduzir ou encurtar
RED         recovery, Z2 ou descanso
INCOMPLETE  dados essenciais incompletos
```

---

## Recommendation action

Campo:

```json
{
  "recommendation": {
    "action": "NO_TRAINING_TODAY"
  }
}
```

Valores possíveis:

```text
KEEP
REDUCE
RECOVERY
REST
INDOOR_ALTERNATIVE
NO_TRAINING_TODAY
SYNC_REQUIRED
```

Significado:

```text
KEEP                  manter treino planeado
REDUCE                reduzir ou encurtar treino
RECOVERY              recovery/Z2 ou descanso
REST                  descanso
INDOOR_ALTERNATIVE    alternativa indoor/rolo
NO_TRAINING_TODAY     não há treino ou já houve atividade hoje
SYNC_REQUIRED         dados incompletos; sincronizar Intervals/Garmin
```

---

## Feedback types

A futura app pode enviar estes tipos:

```text
NO_TIME
RAIN_INDOOR
SICK
INJURED
NO_BIKE_WEEK
MANUAL_NOTE
```

Significado:

```text
NO_TIME        pouco tempo disponível
RAIN_INDOOR    chuva / alternativa rolo
SICK           doente
INJURED        lesionado
NO_BIKE_WEEK   semana sem bicicleta
MANUAL_NOTE    nota livre
```

---

# Endpoints

---

## Health check

```http
GET /health
```

Não requer autenticação.

### Response 200

```json
{
  "status": "ok",
  "service": "daily-coach-api"
}
```

---

## Obter relatório de hoje

```http
GET /api/v1/reports/today
Authorization: Bearer <APP_TOKEN>
```

### Response 200

```json
{
  "date": "2026-05-11",
  "generated_at": "2026-05-11T11:38:34.590083",
  "status": "GREEN",
  "title": "Descanso ou Z2 fácil conforme planeado",
  "summary": "Não há treino planeado para hoje, regra diz repouso total ou Z2 fácil...",
  "full_text": "========================================================================\nDAILY COACH AGENT...",
  "planned_workout": {
    "name": null,
    "description": null,
    "duration_minutes": null,
    "planned_tss": null,
    "source": null
  },
  "completed_activity": {
    "exists": false,
    "name": null,
    "duration_minutes": null,
    "tss": null,
    "avg_power": null,
    "normalized_power": null,
    "intensity_factor": null
  },
  "readiness": {
    "sleep_available": true,
    "hrv_available": true,
    "resting_hr_available": true,
    "sleep_hours": 8.87,
    "hrv": 51.0,
    "resting_hr": 46.0,
    "fitness_ctl": 61.84,
    "fatigue_atl": 52.34,
    "form": 9.5,
    "notes": null
  },
  "weight": {
    "current_kg": 76.19,
    "avg_7d_kg": 76.96,
    "target_kg": 74.0,
    "weekly_trend_kg": null,
    "guidance": null
  },
  "fueling": {
    "protein_target_g": "150–170 g/dia",
    "carb_guidance": null,
    "deficit_guidance": null,
    "notes": "Peso hoje: 76.2 kg.\nMédia 7d: 77.0 kg..."
  },
  "recommendation": {
    "action": "NO_TRAINING_TODAY",
    "headline": "Descanso ou Z2 fácil conforme planeado",
    "details": "Não há treino planeado para hoje...",
    "workout_modification": null,
    "indoor_alternative": "Se for indoor/rolo: rolar muito fácil..."
  },
  "flags": {
    "incomplete_essential_data": false,
    "already_trained_today": false,
    "missed_yesterday_workout": false,
    "weekend_indoor_option_available": false,
    "no_bike_week": false,
    "sick": false,
    "injured": false,
    "race_week": false,
    "rain_or_indoor_constraint": false,
    "no_time_constraint": false
  },
  "source_plan": "FasCat",
  "auto_apply": false
}
```

### Response 404

```json
{
  "detail": "No report found for today: 2026-05-11"
}
```

---

## Listar relatórios

```http
GET /api/v1/reports?limit=30
Authorization: Bearer <APP_TOKEN>
```

### Query params

```text
limit: int, default 30, min 1, max 365
```

### Response 200

```json
{
  "count": 1,
  "reports": [
    {
      "date": "2026-05-11",
      "status": "GREEN",
      "title": "Descanso ou Z2 fácil conforme planeado",
      "summary": "..."
    }
  ]
}
```

Nota: cada item em `reports` contém o relatório completo, não apenas resumo.

---

## Obter relatório por data

```http
GET /api/v1/reports/2026-05-11
Authorization: Bearer <APP_TOKEN>
```

### Response 200

Mesmo formato de `GET /api/v1/reports/today`.

### Response 400

```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD."
}
```

### Response 404

```json
{
  "detail": "No report found for date: 2026-05-11"
}
```

---

## Run now

```http
POST /api/v1/reports/run-now
Authorization: Bearer <APP_TOKEN>
```

Reservado para o futuro botão “Atualizar agora” da app.

Por agora, não executa o Daily Coach real.

### Response 200

```json
{
  "status": "not_implemented",
  "message": "Run-now endpoint reserved for future Daily Coach execution.",
  "next_step": "This will eventually trigger daily_coach_agent.py with rate limiting and safe execution."
}
```

---

## Criar feedback

```http
POST /api/v1/feedback
Authorization: Bearer <APP_TOKEN>
Content-Type: application/json
```

### Request body

```json
{
  "date": "2026-05-11",
  "type": "NO_TIME",
  "note": "Só tenho 45 minutos hoje."
}
```

### Response 200

```json
{
  "status": "saved",
  "path": "data/feedback/2026-05-11.json",
  "feedback": {
    "date": "2026-05-11",
    "type": "NO_TIME",
    "note": "Só tenho 45 minutos hoje.",
    "created_at": "2026-05-11T13:45:18.927816"
  }
}
```

### Tipos válidos

```text
NO_TIME
RAIN_INDOOR
SICK
INJURED
NO_BIKE_WEEK
MANUAL_NOTE
```

---

## Listar feedback

```http
GET /api/v1/feedback
Authorization: Bearer <APP_TOKEN>
```

### Response 200

```json
{
  "count": 2,
  "feedback": [
    {
      "date": "2026-05-11",
      "type": "NO_TIME",
      "note": "Só tenho 45 minutos hoje.",
      "created_at": "2026-05-11T13:45:18.927816"
    },
    {
      "date": "2026-05-11",
      "type": "RAIN_INDOOR",
      "note": "Chuva, provavelmente rolo.",
      "created_at": "2026-05-11T13:46:00.000000"
    }
  ]
}
```

---

## Listar feedback por data

```http
GET /api/v1/feedback?date=2026-05-11
Authorization: Bearer <APP_TOKEN>
```

### Response 200

```json
{
  "count": 1,
  "feedback": [
    {
      "date": "2026-05-11",
      "type": "NO_TIME",
      "note": "Só tenho 45 minutos hoje.",
      "created_at": "2026-05-11T13:45:18.927816"
    }
  ]
}
```

### Response 400

```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD."
}
```

---

# Android UI mapping

## Today screen

Usar:

```http
GET /api/v1/reports/today
```

Campos principais:

```text
status
title
summary
planned_workout
completed_activity
readiness
weight
fueling
recommendation
flags
```

Sugestão de card:

```text
[GREEN] Descanso ou Z2 fácil conforme planeado
Sono 8h52 · HRV 51 · RHR 46 · Form +10
Peso 76.2 kg · média 7d 77.0 kg
```

---

## History screen

Usar:

```http
GET /api/v1/reports?limit=30
```

Mostrar:

```text
date
status
title
summary
recommendation.action
```

---

## Feedback buttons

Botões da app:

```text
Sem tempo       → NO_TIME
Chuva / indoor  → RAIN_INDOOR
Doente          → SICK
Lesão           → INJURED
No bike week    → NO_BIKE_WEEK
Nota manual     → MANUAL_NOTE
```

Cada botão faz:

```http
POST /api/v1/feedback
```

---

# Segurança

- Nunca guardar `INTERVALS_API_KEY`, `OPENAI_API_KEY`, SMTP ou outros secrets na app Android.
- A app só deve guardar o `APP_TOKEN` enquanto for MVP.
- Em produção, trocar Bearer token fixo por autenticação melhor, por exemplo Firebase Auth, Supabase Auth ou Google Sign-In.
