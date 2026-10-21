# API Contract (draft v0.1)

> Planning document. It describes **what each endpoint accepts and returns** so the backend and frontend devs build against the same thing. Nothing here is implemented yet. Change it by agreement, and update this file whenever an endpoint changes.

Priority tags: **T1** = must work for the demo, **T2** = nice to have, **T3** = only if time remains.

---

## 1. Conventions

| Topic | Rule |
|---|---|
| Base URL | `http://localhost:8000` (frontend runs on `http://localhost:5173`) |
| Format | JSON in, JSON out. Header `Content-Type: application/json` |
| Prefix | Data endpoints start with `/api`. Login endpoints start with `/auth` |
| Login | Session cookie set by the backend after Google sign-in. Frontend sends requests with `credentials: "include"` |
| Dates | ISO 8601 strings. Date only: `"2026-10-28"`. Date and time: `"2026-10-28T17:00:00+05:30"`. Timezone: IST |
| IDs | Integers |
| Errors | `{ "detail": "human readable message" }` with a matching status code |

### Status codes

| Code | Meaning | Typical cause |
|---|---|---|
| 200 | OK | Success |
| 201 | Created | New category or announcement created |
| 204 | No content | Delete succeeded |
| 401 | Not logged in | Missing or expired session |
| 403 | Not allowed | Not a CR/BR trying to post an announcement |
| 404 | Not found | Wrong id |
| 422 | Bad input | Request body does not match the shape below |
| 429 | Slow down | AI rate limit reached; frontend should show "try again in a minute" |
| 500 | Server error | Backend bug; read the backend terminal |

---

## 2. Data shapes

### User
| Field | Type | Notes |
|---|---|---|
| id | integer | |
| email | string | The Gmail address they signed in with |
| name | string | From the Google profile |
| role | string | `"student"`, `"cr"` or `"br"` (CR/BR only matters for T3) |
| batch | string or null | e.g. `"2026-ChemE"` (T3) |

### Category
| Field | Type | Notes |
|---|---|---|
| id | integer | |
| name | string | e.g. `"Clubs & Societies"` |
| description | string | Plain-language meaning. For custom categories this is what the AI uses to decide matches |
| kind | string | `"default"` or `"custom"` |
| color | string | Hex colour such as `"#1f4e8c"`. Comes from the design system |
| mail_count | integer | Number of mails currently in it |
| unread_count | integer | |

### Mail
| Field | Type | Notes |
|---|---|---|
| id | integer | |
| gmail_id | string | Gmail's own message id (used to avoid classifying twice) |
| sender_name | string | |
| sender_email | string | |
| subject | string | |
| summary | string | One or two sentences written by the AI, max about 30 words |
| category | string | Exactly one **default** category name |
| custom_categories | list of integers | Ids of matching **custom** categories (a mail can match several) |
| deadline | string or null | Date by which the user must act. `null` if none |
| event_at | string or null | When an event happens, if different from the deadline |
| action_needed | boolean | `true` if the user must do something (register, submit, reply, attend) |
| confidence | number | 0 to 1. Low values can be shown as "unsure" |
| read | boolean | |
| done | boolean | User marked the task as handled |
| received_at | string | ISO date and time |

Example:

```json
{
  "id": 41,
  "gmail_id": "18c2f0a9d3b1",
  "sender_name": "ACM IITR",
  "sender_email": "acm@example.ac.in",
  "subject": "ACM recruitments open",
  "summary": "Applications for ACM IITR close on 28 Oct. Fill the form to apply.",
  "category": "Clubs & Societies",
  "custom_categories": [7],
  "deadline": "2026-10-28",
  "event_at": null,
  "action_needed": true,
  "confidence": 0.93,
  "read": false,
  "done": false,
  "received_at": "2026-10-21T09:14:00+05:30"
}
```

### Announcement (T3)
| Field | Type | Notes |
|---|---|---|
| id | integer | |
| author_name | string | |
| role | string | `"cr"` or `"br"` |
| batch | string | Who it is for |
| text | string | |
| created_at | string | |

---

## 3. Endpoints

### Health
| Endpoint | Priority | Purpose |
|---|---|---|
| `GET /health` | T1 | Returns `{ "status": "ok" }`. Used to check the backend is up |

### Login and account
| Endpoint | Priority | Purpose | Returns |
|---|---|---|---|
| `GET /auth/login` | T1 | Starts Google sign-in. Browser is redirected to Google | Redirect |
| `GET /auth/callback` | T1 | Google sends the user here. Backend stores the session, then redirects to the frontend home page | Redirect |
| `POST /auth/logout` | T1 | Ends the session | `204` |
| `GET /api/me` | T1 | Who is logged in. The frontend calls this on load to decide between the login screen and the app | User, or `401` |
| `DELETE /api/me` | T2 | Deletes all stored data for this user (privacy feature) | `204` |

### Mails
| Endpoint | Priority | Purpose |
|---|---|---|
| `POST /api/mails/sync` | T1 | Fetches new mail from Gmail and classifies it. Body: none. Returns counts: `{ "fetched": 24, "classified": 18, "skipped": 6 }`. May take several seconds, so the frontend shows a spinner |
| `GET /api/mails` | T1 | List mails. Query options below |
| `GET /api/mails/{id}` | T2 | One mail with full detail |
| `PATCH /api/mails/{id}` | T1 | Update `read`, `done`, or `category`. Body example: `{ "read": true }`. A user changing the category is a correction |

Query options for `GET /api/mails` (all optional, can be combined):

| Option | Example | Meaning |
|---|---|---|
| `category` | `category=3` | Category id. For a default category it matches the mail's main category. For a custom category it matches mails tagged with it |
| `unread` | `unread=true` | Only unread |
| `action_needed` | `action_needed=true` | Only mails that need action |
| `q` | `q=hackathon` | Text search in subject and summary |
| `limit`, `offset` | `limit=50&offset=0` | Paging |

Response: `{ "items": [Mail, Mail, ...], "total": 132 }`

### Deadlines
| Endpoint | Priority | Purpose |
|---|---|---|
| `GET /api/deadlines` | T1 | Mails that have a deadline, soonest first. Optional `days=14` limits to the next N days, and `include_done=false` hides handled ones. Each item is a Mail plus `days_left` (integer, negative if overdue) |

### Categories
| Endpoint | Priority | Purpose |
|---|---|---|
| `GET /api/categories` | T1 | All default categories plus the user's custom ones, with counts |
| `POST /api/categories` | T1 | Create a custom category. Body: `{ "name": "International applications", "description": "Fellowships, exchange programs, foreign universities", "color": "#6a3fa0" }`. Returns the Category (`201`) |
| `PATCH /api/categories/{id}` | T2 | Rename or edit description. Custom only |
| `DELETE /api/categories/{id}` | T1 | Delete a custom category. Default categories cannot be deleted (`403`) |
| `POST /api/categories/{id}/reclassify` | T2 | After creating or editing a custom category, re-check existing mails against it. Returns `{ "matched": 5 }` |

### Announcements (T3)
| Endpoint | Priority | Purpose |
|---|---|---|
| `GET /api/announcements` | T3 | Announcements for the user's batch |
| `POST /api/announcements` | T3 | CR/BR posts one. Body: `{ "text": "...", "batch": "2026-ChemE" }`. `403` if not a CR/BR |
| `DELETE /api/announcements/{id}` | T3 | Author deletes theirs |

---

## 4. Behaviour rules both sides rely on

1. **Sync is idempotent.** Calling it twice never creates duplicates, because mails are matched by `gmail_id`.
2. **A mail has exactly one default category** and zero or more custom ones.
3. **Deadlines in the past are kept** but returned with a negative `days_left`, so the UI can show "overdue".
4. **Deleting a custom category** removes the tag from mails but never deletes the mails.
5. **The frontend never calls Gmail or Gemini directly.** Everything goes through this API.
6. **If the AI is rate-limited**, sync still saves the mails it could not classify as category `"Other"` with `confidence: 0`, and returns status `429` only if nothing could be processed.

---

## 5. Open questions (decide as a team before building)

- [ ] Do custom categories work as **extra tags** on top of the default category (recommended), or do they **replace** it?
- [ ] Should sync run only when the user clicks, or also on a timer?
- [ ] Do we keep full email bodies, or only summaries and metadata? (Recommended: only summaries and metadata.)
- [ ] For the demo, is one pre-filled account enough, or do we support several users?
- [ ] Do we build the CR/BR announcements, or show it as seeded demo data?
