# Daily Coach — Design & Vision Review

*Based on a read-through of `mobile/src/App.jsx`, `styles.css`, `TodayScreen.jsx`, `GymScreen.jsx`, `HistoryScreen.jsx`, `SettingsScreen.jsx`, `api/client.js` and `api/push.js` in `daily-coach-nuno`, 2026-08-21.*

## What's already working

The dark theme reads clean and purpose-built rather than generic — the single-column, 480px-max layout is the right call for a personal tool that lives in one hand on a bike-adjacent morning routine. The status color language (green/yellow/red, plus the orange Z4 token that's defined but not yet used anywhere) is a solid semantic backbone, and the underlying flows — feedback that now actually changes tomorrow's decision, apply-preview-before-apply for the Intervals.icu alternate workout, the collapsed `<details>` for "se só tiveres X min" alternates — are genuinely good UX decisions, not just backend plumbing. The problem isn't the structure. It's that everything on screen currently has the same visual weight, so nothing feels like the one thing you're supposed to look at first.

## Where it feels flat, and what "bold" would actually fix

**One accent color is doing every job.** `--lime` is the brand dot, the active tab, the primary button, the action-line arrows, the chart line, and the focus state, all at once. When one color means everything, nothing reads as more important than anything else. The fix isn't a new palette — it's a second accent reserved for one specific job (see the mockup: a violet `--accent2` used only for the "days to goal" chip), so lime stays legible as "the thing to tap" everywhere else.

**There's no hero moment for the single most important fact in the app.** Opening Hoje answers "how do I feel today" by making you read a small uppercase pill next to the title, then scan four stacked `kv` rows to piece together why. That's backwards for a coaching app — the status deserves to be the first and biggest thing on screen, not a label. A circular ring/gauge sized around 90–100px, colored by status, with the state word inside it, turns "GREEN/YELLOW/RED" from a fact you read into a fact you *see* before you read anything else.

**Every card has identical visual weight.** Readiness, weight, decision, apply, motivos, feedback — six `.card` boxes in a row, same radius, same border, same padding. It reads like a spec sheet. The decision card is the one that should look heavier: a tinted background using the day's status color at low opacity, more padding, a bigger headline. The five stacked `Sono / HRV / Resting HR / Fitness-Fatigue / Form` rows can collapse into a two-column stat grid — same data, half the vertical space, which then gives the decision card room to actually feel like the centerpiece instead of the fifth card down.

**There are no icons anywhere.** Not on the tab bar (plain text labels), not next to Sono/HRV/Resting HR, not on the feedback chips. This is the cheapest possible upgrade for the amount of "bold" it buys — a dozen small inline SVGs (no icon font or CDN dependency needed) make the tab bar scannable at a glance and give the stat grid and feedback chips something to anchor on besides text.

**Buttons don't differentiate intent.** `.icon-btn` and `.feedback-btn` are visually almost the same — muted background, thin border, same font size — so the refresh button, "Testar ligação," and the five feedback options all carry equal visual weight even though they mean very different things. Keep exactly one true primary style (lime, reserved for the single most important action per screen — `.primary-btn` already does this correctly), give feedback chips their own icon + a clearly different resting state, and make the topbar refresh a small icon-only circular button instead of the current "⟳ Atualizar" text label that awkwardly becomes "…" while it runs.

**Motion is entirely absent.** Loading states are literal text ("A carregar…"), and the running refresh state is a text swap. A spinning icon while `runState === 'running'`, a skeleton/pulse while the report loads, and a small transition into the "✓ criado" apply-success state would make the app feel considerably more finished for very little engineering effort.

### Quick wins (front-end only, no backend changes)

- A second accent color token, used only for one specific new thing (not sprinkled everywhere lime already is).
- A status ring/gauge on Hoje, replacing the inline badge as the primary way you see today's state.
- A small inline-SVG icon set for the tab bar, the stat rows, and the feedback chips.
- A two-column stat grid replacing the five stacked `kv` rows, freeing space for the decision card.
- A spinning icon-only refresh button instead of the current text-based one.
- Skeleton/pulse loading states instead of "A carregar…".

A live-ish mockup of Hoje with all of the above applied is attached (`daily_coach_bold_mockup.html`) — open it to see the direction rather than just read about it. It reuses your existing data shape and Portuguese copy; it's a design direction, not a code drop-in.

## The "full cycling app" rethink

Right now Daily Coach is a single-purpose daily readiness coach. Turning it into something closer to "a full cycling app with all the involvements of cycling" doesn't mean starting over — the data plumbing already in place (Intervals.icu ingestion, Postgres persistence via `daily_reports`/`feedback_entries`/`device_tokens`, the feedback loop, the non-destructive alternate-workout apply flow) is exactly the foundation a bigger app needs. The question is what to build on top of it, and in what order.

### Near-term additions (reuse what's already wired)

- **Season / gran fondo plan.** A periodization calendar counting down to the March 2027 goal, phase-aware (base/build/peak/taper), that feeds the current phase into `daily_coach_agent.py`'s existing OpenAI-reasoning + heuristic-fallback pipeline so recommendations shift automatically as the goal gets closer — this was already floated as an idea and is a natural extension of logic that exists today, not a new system.
- **A real History tab.** The 14-day Form sparkline already proves the concept; `fitness_ctl`/`fatigue_atl`/`form` are already stored per report, so a proper CTL/ATL/TSB trend chart and a weekly TSS bar chart are front-end work against data you already have, not a new data source.
- **Nutrition tab**, taken one step further than the original RidePlan-porting idea: since every report already carries `planned_tss` and `duration_minutes`, the nutrition tab can compute an on-the-bike fueling target (grams of carbs/hour) per ride directly from the report, instead of being a static reference page disconnected from the daily data.
- **"Upgrade" option on GREEN days** (already discussed, no consensus yet) — this slots naturally into the existing DECISÃO card as a second action, and can reuse the apply-preview → confirm pattern already built for YELLOW/RED substitutions almost as-is.
- **An injury/pain log.** The `INJURED` feedback type is already captured; a small new table logging it over time, resurfaced in the Gym tab's "Evitar" section, would close the loop between what you report and what the gym plan warns you away from.

### Bigger lifts (need a genuinely new integration)

- **Gear & maintenance tracking** — chain, tires, brake pads, cassette mileage sourced from Intervals.icu activity distances, with a "due for service" nudge. New table, plus a periodic mileage rollup job.
- **Route/ride library with elevation + weather-aware packing checklists** — needs a weather API and route/GPX data, so this is new plumbing, not just new screens.
- **Race-day mode** for the gran fondo itself — pacing plan, fueling timing, gear checklist, auto-generated as the date approaches. This is really a specialized view over the season plan + nutrition + gear systems above, so it's worth sequencing last, once those exist.
- **Lightweight sharing** — a "share today's status" export rendered as an image, for a coach or training partner. No new backend needed, but it's a genuinely new client-side capability rather than an extension of existing data.

### If I were sequencing this

1. The visual redesign above — no backend work, and it sets the visual language everything else inherits.
2. A real History tab (CTL/ATL/TSB, weekly TSS) — pure front-end against data already in Postgres.
3. Nutrition tab — already scoped as an idea, just not started.
4. Season/gran fondo plan — the piece that makes the daily coach itself feel smarter as the goal approaches.
5. Gear tracking, weather/route library, race-day mode — worth doing, but each needs a new integration, and each will look better once it inherits a settled design system from step 1 rather than the other way around.

## Open question worth resolving before any of this

The push notification you didn't get after tapping "Atualizar," and the Android permission prompt that appeared around the same time, are almost certainly unrelated to each other rather than cause-and-effect — `initPushNotifications()` runs once per app launch in `App.jsx`, independent of the refresh button, and only asks for permission if it isn't already granted. So this was most likely a one-time timing coincidence (permission got granted for the first time right around when you happened to trigger a refresh), not a bug in the refresh flow itself. Worth a five-minute check tomorrow morning: if the 08:00 cron report *does* push correctly now that permission is granted, it confirms this was just first-run timing and nothing needs fixing.
