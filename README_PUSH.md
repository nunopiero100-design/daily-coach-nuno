# Push notifications - backend

IMPORTANT: this api.py and daily_coach_agent.py already include everything
from the earlier runnow_patch.zip and feedback_patch.zip too (I kept building
on the same checkout) - you only need to apply the files in THIS zip for
those, don't also apply the older ones for api.py/daily_coach_agent.py.

Files: api.py, db.py, postgres_storage.py (all modified), devices.py, push.py
(new), daily_coach_agent.py (has the refined feedback rule from earlier),
requirements.txt (added firebase-admin).

Tested: no-op with no credential configured (0,0 - no crash), device
registration against real Postgres, full ingest-triggers-push chain with
mocked FCM send (verified correct title/body/token), and a push SEND
FAILURE still lets the report save successfully (200) - push is best-effort,
never blocks the real work.

## What I genuinely cannot test from here
Actual delivery to your phone - that needs a real Firebase project, a real
service account, and your real device. Everything up to "does FCM accept
the message" is verified; "does it actually arrive and show up" is the one
thing only you can confirm once it's all wired up.

## What you need to do

### 1. Get the SERVICE ACCOUNT key (different from google-services.json!)
Firebase Console -> gear icon (top left) -> Project Settings -> "Service
accounts" tab -> "Generate new private key" -> downloads a JSON file.

### 2. Add it to Render
Open that downloaded file in a text editor, copy its ENTIRE content, and
add to Render -> Environment:
    FIREBASE_SERVICE_ACCOUNT_JSON = <paste the whole JSON content>

### 3. Apply the code
Same as always - replace/add these files, commit, push.

### 4. Test
Once deployed, tap "⟳ Atualizar" in the app to trigger a fresh run - if
everything's wired correctly, you should get a real push notification a
minute or so later when the report lands.
