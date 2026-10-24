# InSorta

InSorta organizes IIT Roorkee Gmail messages into campus categories and highlights deadlines, opportunities, academic updates, and recent mail.

## Features

- Gmail sign-in using read-only access.
- Mail classification with Gemini when `GEMINI_API_KEY` is configured, plus a rule-based fallback.
- Deadline extraction and a month calendar. Dates with deadlines have a red dot; selecting a date lists its deadlines.
- Opportunities grouped into scholarships and fellowships, placements and internships, and international opportunities.
- Daily digest grouped by received date, with the newest day selected by default.
- Search across loaded messages by sender, email address, subject, preview, message text, category, and classification reason.
- Classroom-style stream and classwork view sourced from course and deadline emails. Completion state is local to the current browser session; this is not connected to Google Classroom.
- Quick links to AIS and Channeli.

## Requirements

- Python 3.10 or newer
- Node.js and npm for frontend development or rebuilding the production UI
- Google OAuth client credentials
- Optional: Gemini API key for AI classification

## Configuration

1. Copy `.env.example` to `.env` in the project root.
2. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from a Google Cloud OAuth client.
3. Add the redirect URI `http://127.0.0.1:5000/auth/callback` to the OAuth client's authorized redirect URIs for local development. For deployment, set `GOOGLE_REDIRECT_URI` to the deployed callback URL and register that URL with Google.
4. Optionally set `GEMINI_API_KEY`. Without it, the app uses its keyword rule classifier.
5. Set a stable, random `SESSION_SECRET`. Keep `.env` private and do not commit it.

`OAUTHLIB_INSECURE_TRANSPORT=1` is included in the example for local HTTP development. Do not use that setting in production; serve the app over HTTPS.

## Run locally

In PowerShell, from the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
$env:FLASK_APP = "run.py"
flask run --host 127.0.0.1 --port 5000
```

Fill in `.env` before signing in. In another terminal, start the frontend development server:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite address shown in the terminal (normally `http://localhost:5173`). Its development proxy forwards `/auth` and `/gmail` requests to Flask on port 5000.

## Build for deployment

From `frontend/` run:

```bash
npm install
npm run build
```

Vite writes the production assets to `backend/static`, which Flask serves directly. Rebuild after frontend changes and include the updated `backend/static` directory when deploying. The Flask app itself does not need Node.js at runtime.

## Data and limits

- Each inbox refresh asks Gmail for the newest 100 messages. Previously classified messages are also loaded from the SQLite cache at `backend/instance/insorta.sqlite3` by default. Set `INSORTA_DB_PATH` to use a different persistent database location.
- Search filters the messages currently returned by the inbox endpoint; it does not search Gmail's entire mailbox remotely.
- The app stores message classifications and deadline details in SQLite. Gmail access is read-only.
- Message text shown to classification and search is limited to the body preview fetched by the backend.
- Classroom is an email-based view with browser-local completion tracking. It does not create classes, accept submissions, or synchronize with Google Classroom.
- Extracted deadlines are suggestions from email content. Open the original message to confirm dates and requirements.

## Project layout

- `backend/app.py` — Flask app, Google OAuth, Gmail fetching, classification cache, and API routes.
- `backend/ai_classifier.py` — Gemini prompt, category validation, and deadline validation.
- `backend/static/` — production frontend served by Flask.
- `frontend/src/App.tsx` — dashboard and page components.
- `frontend/src/inbox.ts` — inbox API client and message/deadline data mapping.
- `frontend/src/global.css` — global styles and theme rules.
- `run.py` — Flask application entry point.
