# PROJECT_NAME

> A smart inbox for IIT Roorkee students. It connects to your institute email, sorts every mail into clear categories, pulls out deadlines, and shows what actually needs your attention.

Built for **Syntax Error**, the SDSLabs hackathon at IIT Roorkee.

---

## The problem

IIT Roorkee students get a constant stream of email from professors and TAs, departments, the academic section, clubs and societies, the placement and internship cell, hostel and mess offices, and student bodies. All of it lands in one inbox, mixed with personal mail, newsletters and promotions. Important deadlines get buried, and checking mail turns into digging through a pile.

## The solution

PROJECT_NAME is a web and mobile app that:

- **Sorts** every mail into categories automatically
- **Extracts deadlines** and lists what needs attention first
- Lets you **create your own categories** in plain language (for example, "international applications" for fellowships, exchange programs and foreign universities)
- Gives **clubs** their own section with application deadlines
- Keeps **promotions** out of your way in a separate section
- Gives **CRs and BRs** a place to relay information to their batch
- Can be adapted to **any institute** by changing a config file, not the code
  and much more!


## How it works

```
Gmail API → clean the mail → rule-based pre-filter → Gemini (structured JSON) → SQLite → FastAPI → React app
```

1. Mails are fetched with **read-only** Gmail access
2. Cheap rules (sender, mailing-list headers) handle the obvious cases first
3. Gemini classifies the rest and returns a category, summary, deadline and whether action is needed
4. Results are cached per mail, so nothing is classified twice
5. The React app shows categories, deadlines and custom sections

Institute-specific settings (sender domains, default categories, club names) live in `config/institute.iitr.json`.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, SQLite |
| AI | Google Gemini (free tier) |
| Mail | Gmail API (OAuth 2.0, `gmail.readonly`) |
| Frontend | React, Vite, Tailwind CSS |
| Design | Figma |

## Privacy

- Read-only access. The app cannot send, delete or modify mail
- Only summaries and metadata are stored, not full mail bodies
- A "delete my data" option removes everything stored for a user
- Secrets (`.env`, OAuth credentials) are never committed

## Getting started

### Prerequisites

Git, Python 3.12, Node.js (LTS) and VS Code.

### 1. Clone

```bash
git clone https://github.com/CaffeinatedCoder-008/ZonedOuts_SyntaxError.git
cd ZonedOuts_SyntaxError
```

### 2. Environment variables

```bash
copy .env.example .env
```

Fill in `.env`. Ask a teammate for the Gemini key. Never commit this file.

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Check it at <http://localhost:8000/health>. API docs are at <http://localhost:8000/docs>.

### 4. Frontend

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open <http://localhost:5173>.

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Gmail, classifier, deadlines
│   │   └── main.py
│   ├── tests/
│   │   └── sample_emails/
│   └── requirements.txt
├── web/                  # React app (Vite)
├── design/               # Figma links, assets, exports
├── config/               # Institute-specific settings
├── docs/                 # Architecture, API contract, demo script
├── prototype/            # Early prototype, kept for reference
└── .env.example
```

## Contributing (team workflow)

- Pull before you start: `git pull`
- Work on a branch: `feat/<thing>`, `fix/<thing>`, `design/<thing>`
- Small commits with clear messages
- Open a pull request into `main`; one teammate reviews it

## Team

| Name | Role | GitHub |
|---|---|---|
| Anshuman Mishra | _role_ | [@CaffeinatedCoder-008](https://github.com/CaffeinatedCoder-008) |
| _Teammate name_ | _role_ | _@username_ |
| _Teammate name_ | _role_ | _@username_ |
| _Teammate name_ | _role_ | _@username_ |

## Acknowledgements

Thanks to SDSLabs for organising Syntax Error, and to the seniors who reviewed our ideas.
