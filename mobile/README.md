# Daily Coach — Mobile (Capacitor + React)

Android client for the `daily-coach-nuno` backend. Same repo, lives in `mobile/`.

## What this is, honestly

A first working slice: a "Today" screen that renders the DailyCoachReport
(status badge, planned workout, readiness, weight, decision + reasons, quick
feedback buttons), plus a Settings screen to store the backend URL and
APP_TOKEN on-device (via Capacitor Preferences — plain local storage, fine
for a personal single-user app, not hardware-backed secure storage).

**Starts in MOCK mode** (toggle in Settings) — renders `src/mock/todayReport.json`
instead of calling the real API. Switch it off once:
1. The backend actually has an "ingest" endpoint so today's GitHub Actions
   run lands in the live API (see the architecture note from planning this).
2. The field names in `src/mock/todayReport.json` are reconciled against the
   real `backend/schemas.py` — this mock is a best-effort reconstruction from
   the progress report + printed report text, not the literal schema. Some
   field names likely need adjusting once compared side-by-side.

## Local setup

```bash
cd mobile
npm install
npm run dev          # runs the web app in a browser at localhost:5173, fastest way to iterate on UI
```

## Android

The native project already exists in `android/` (generated via `npx cap add android`,
confirmed to sync cleanly). To open/run it:

```bash
npm run build         # builds the web app into dist/
npm run cap:sync      # copies dist/ into android/app/src/main/assets
npm run cap:open:android   # opens the project in Android Studio
```

From Android Studio: connect a phone (USB debugging on) or use an emulator, hit Run.
`android/` is committed but build outputs (`android/app/build/`, `android/.gradle/`,
`android/local.properties`) are gitignored — Android Studio regenerates those.

## Structure

```
src/
  api/client.js         fetch wrapper, Bearer auth, reads settings from Preferences
  screens/TodayScreen.jsx
  screens/SettingsScreen.jsx
  components/StatusBadge.jsx
  mock/todayReport.json  mock data, see note above
  styles.css             dark/lime theme, same visual language as RidePlan
```

## Known gaps / next steps

- No `run-now` button — the backend endpoint is a placeholder (`not_implemented`),
  wiring a button to it now would be a dead end.
- No push notifications yet (Pelotão used Firebase Cloud Messaging for this —
  same approach would apply here once there's a reason to notify, e.g. "today's
  report is ready").
- Reconcile `mock/todayReport.json` field names against the real Pydantic schema.
- Once the ingest bridge exists, flip `useMock` default to `false` in `App.jsx`.
