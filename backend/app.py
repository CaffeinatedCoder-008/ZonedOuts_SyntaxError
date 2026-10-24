
import os
import re
import base64
import secrets

from dotenv import load_dotenv

# Load local .env values before reading environment variables.
load_dotenv()

from flask import Flask, jsonify, redirect, request, session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .ai_classifier import classify_with_ai


app = Flask(__name__)

# Stable session signing key.
app.secret_key = os.environ.get("SESSION_SECRET")

if not app.secret_key:
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("SESSION_SECRET must be configured in production.")

    app.secret_key = secrets.token_hex(32)
    app.logger.warning(
        "SESSION_SECRET is not set. Sessions will be invalidated on restart."
    )

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

# Use the deployed URL by default. Local .env can override this.
REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "https://insorta-app-gasper.sdslabs.org/auth/callback",
)

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

# Browser session cookie settings.
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = REDIRECT_URI.startswith("https://")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Temporary in-memory credential storage.
# A server restart clears credentials; users must sign in again.
google_credentials = {}


CATEGORIES = [
    "PROFESSOR/TA",
    "ACADEMIC AND SECTIONS",
    "DEPARTMENT AND ADMIN",
    "COURSES AND ANNOUNCEMENTS",
    "CLUBS AND SOCIETIES",
    "PLACEMENT AND INTERNSHIPS",
    "SCHOLARSHIPS",
    "HOSTEL MESS",
    "CR/BR UPDATES",
    "PROMOTION/NEWSLETTERS",
    "PERSONAL/OTHERS",
]


def sid():
    """Return a stable, random identifier for the current browser session."""
    if "sid" not in session:
        session["sid"] = secrets.token_hex(16)
    return session["sid"]


def make_oauth_flow(state=None, code_verifier=None):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return None

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }

    return Flow.from_client_config(
        client_config,
        scopes=[GMAIL_SCOPE],
        state=state,
        redirect_uri=REDIRECT_URI,
        code_verifier=code_verifier,
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/auth/login")
def login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({
            "error": "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET first."
        }), 503

    code_verifier = secrets.token_urlsafe(64)
    flow = make_oauth_flow(code_verifier=code_verifier)

    if flow is None:
        return jsonify({"error": "Google OAuth is not configured."}), 503

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        code_challenge_method="S256",
    )

    session["oauth_state"] = state
    session["oauth_code_verifier"] = code_verifier

    app.logger.warning(
        "OAuth login: state_saved=%s, verifier_saved=%s, "
        "session_cookie_name=%s, redirect_uri=%s",
        bool(session.get("oauth_state")),
        bool(session.get("oauth_code_verifier")),
        app.config.get("SESSION_COOKIE_NAME"),
        REDIRECT_URI,
    )

    return redirect(authorization_url)


@app.get("/auth/callback")
def callback():
    # Diagnostic only: never log cookie values or OAuth secrets.
    app.logger.warning(
        "OAuth callback: cookie_received=%s, state_present=%s, "
        "verifier_present=%s",
        app.config["SESSION_COOKIE_NAME"] in request.cookies,
        bool(session.get("oauth_state")),
        bool(session.get("oauth_code_verifier")),
    )

    if request.args.get("error"):
        session.pop("oauth_state", None)
        session.pop("oauth_code_verifier", None)

        return jsonify({
            "error": "Google sign-in was cancelled or denied."
        }), 400

    state = session.get("oauth_state")
    code_verifier = session.get("oauth_code_verifier")

    if not state or not code_verifier:
        return jsonify({
            "error": "OAuth session is missing. Restart at /auth/login."
        }), 400

    flow = make_oauth_flow(
        state=state,
        code_verifier=code_verifier,
    )

    if flow is None:
        return jsonify({
            "error": "Google OAuth is not configured."
        }), 503

    try:
        authorization_response = (
            f"{REDIRECT_URI}?{request.query_string.decode('utf-8')}"
        )

        flow.fetch_token(
            authorization_response=authorization_response
        )

        credentials = flow.credentials

        google_credentials[sid()] = credentials
        session["google_connected"] = True

        session.pop("oauth_state", None)
        session.pop("oauth_code_verifier", None)

        return jsonify({
            "status": "signed_in",
            "message": "Google OAuth succeeded. Gmail access is read-only.",
            "has_credentials": credentials is not None,
        })

    except Exception:
        app.logger.exception("Google OAuth callback failed")

        session.pop("oauth_state", None)
        session.pop("oauth_code_verifier", None)

        return jsonify({
            "error": (
                "OAuth token exchange failed. Restart sign-in "
                "and check the server log."
            )
        }), 400


@app.get("/gmail/messages")
def gmail_messages():
    if not session.get("google_connected"):
        return jsonify({
            "error": "Not signed in. Visit /auth/login first."
        }), 401

    credentials = google_credentials.get(session.get("sid"))

    if credentials is None:
        session.pop("google_connected", None)

        return jsonify({
            "error": "Credentials unavailable. Sign in again at /auth/login."
        }), 401

    try:
        service = build("gmail", "v1", credentials=credentials)

        result = service.users().messages().list(
            userId="me",
            maxResults=10,
        ).execute()

        messages = result.get("messages", [])

        return jsonify({
            "count": len(messages),
            "messages": messages,
        })

    except Exception:
        app.logger.exception("Gmail fetch failed")

        return jsonify({
            "error": "Could not fetch Gmail messages. Check the server log."
        }), 500


def decode_body(data):
    """Decode a Gmail API base64url-encoded body."""
    if not data:
        return ""

    padding = "=" * (-len(data) % 4)
    decoded = base64.urlsafe_b64decode(data + padding)

    return decoded.decode("utf-8", errors="replace")


def extract_text(payload):
    """Extract readable plain text from a Gmail payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if mime_type == "text/plain" and body_data:
        return decode_body(body_data)

    texts = []

    for part in payload.get("parts", []):
        text = extract_text(part)

        if text:
            texts.append(text)

    return "\n".join(texts)


def parse_forwarded_email(text):
    """Extract common headers from an inline forwarded email."""
    patterns = {
        "original_sender": r"(?im)^From:\s*(.+)$",
        "original_subject": r"(?im)^Subject:\s*(.+)$",
        "original_date": r"(?im)^Date:\s*(.+)$",
    }

    marker = re.search(
        r"(?im)^[- ]*Forwarded message[- ]*[- ]*$",
        text,
    )

    search_text = text[marker.end():] if marker else text
    result = {}

    for key, pattern in patterns.items():
        match = re.search(pattern, search_text)
        result[key] = match.group(1).strip() if match else None

    result["is_forwarded"] = bool(
        marker
        or result["original_sender"]
        or result["original_subject"]
    )

    return result


def classify(mail):
    """Rule-based fallback classifier for IIT Roorkee campus emails."""

    sender = (
        mail.get("original_sender")
        or mail.get("actual_sender")
        or ""
    ).lower()

    subject = (
        mail.get("original_subject")
        or mail.get("actual_subject")
        or ""
    ).lower()

    body = (mail.get("body_preview") or "").lower()
    snippet = (mail.get("snippet") or "").lower()

    text = f"{sender} {subject} {snippet} {body}"

    rules = [
        ("SCHOLARSHIPS", [
            "scholarship", "fellowship", "student grant",
            "financial aid",
        ]),
        ("PLACEMENT AND INTERNSHIPS", [
            "placement cell", "placement office",
            "internship opportunity", "internship application",
            "pre-placement talk", "pre placement talk",
            "campus recruitment", "job opening",
            "recruitment drive", "pre placement offer",
        ]),
        ("HOSTEL MESS", [
            "mess menu", "mess fee", "mess bill",
            "hostel", "warden", "room allotment",
        ]),
        ("CR/BR UPDATES", [
            "class representative", "batch representative",
            "cr update", "br update",
        ]),
        ("PROFESSOR/TA", [
            "teaching assistant", "course instructor",
            "office hours", "professor", "faculty advisor",
        ]),
        ("DEPARTMENT AND ADMIN", [
            "academic affairs office", "undergraduate section",
            "dean academic affairs", "department office",
            "registrar office", "academic calendar",
            "grade card", "exam form", "semester registration",
            "feedback of ugtas", "feedback on the performance",
        ]),
        ("CLUBS AND SOCIETIES", [
            "helios", "economics circle", "enactus",
            "inter iit tech meet", "openai student collective",
            "club recruitment", "society recruitment",
            "club orientation", "student club",
            "club talk", "intro talk", "auditions",
            "workshop", "conclave",
        ]),
        ("ACADEMIC AND SECTIONS", [
            "section ", "section-wise", "section wise",
            "tutorial group", "class timetable",
            "section timetable", "academic section",
        ]),
        ("COURSES AND ANNOUNCEMENTS", [
            "assignment", "tutorial", "quiz", "midsem",
            "endsem", "lab submission", "course material",
            "lecture", "course announcement",
        ]),
        ("PROMOTION/NEWSLETTERS", [
            "newsletter", "weekly digest", "monthly digest",
            "unsubscribe", "discount", "limited time offer",
            "coupon", "cashback", "special offer",
        ]),
    ]

    for category, keywords in rules:
        matched = [
            keyword for keyword in keywords
            if keyword in text
        ]

        if matched:
            app.logger.debug(
                "Fallback rule classifier: subject=%r category=%r matched=%r",
                subject,
                category,
                matched,
            )

            return {
                "category": category,
                "confidence": 0.65,
                "method": "rules",
            }

    # No rule matched.
    return None


@app.get("/gmail/inbox")
def gmail_inbox():
    if not session.get("google_connected"):
        return jsonify({
            "error": "Sign in at /auth/login first."
        }), 401

    credentials = google_credentials.get(session.get("sid"))

    if credentials is None:
        session.pop("google_connected", None)

        return jsonify({
            "error": "Credentials unavailable. Sign in again."
        }), 401

    try:
        service = build("gmail", "v1", credentials=credentials)

        result = service.users().messages().list(
            userId="me",
            maxResults=10,
        ).execute()

        inbox = []

        for item in result.get("messages", []):
            message = service.users().messages().get(
                userId="me",
                id=item["id"],
                format="full",
            ).execute()

            headers = message.get("payload", {}).get("headers", [])

            header_map = {
                header["name"].lower(): header["value"]
                for header in headers
            }

            body_text = extract_text(message.get("payload", {}))
            forwarded = parse_forwarded_email(body_text)

            mail = {
                "id": message["id"],
                "actual_sender": header_map.get("from"),
                "actual_subject": header_map.get("subject"),
                "actual_date": header_map.get("date"),
                "snippet": message.get("snippet", ""),
                "body_preview": body_text[:3000],
                **forwarded,
            }

            # 1. Gemini is the primary classifier.
            try:
                ai_result = classify_with_ai(mail)
            except Exception:
                app.logger.exception("Gemini classifier failed")
                ai_result = None

            # Accept only results that use an exact frontend category.
            if (
                isinstance(ai_result, dict)
                and ai_result.get("category") in CATEGORIES
            ):
                mail["classification"] = ai_result

            else:
                # 2. If Gemini fails or returns an invalid result,
                #    use the rule-based classifier.
                app.logger.info(
                    "Gemini unavailable or returned an invalid category; "
                    "trying rule-based fallback."
                )

                try:
                    rule_result = classify(mail)
                except Exception:
                    app.logger.exception("Rule-based classifier failed")
                    rule_result = None

                if (
                    isinstance(rule_result, dict)
                    and rule_result.get("category") in CATEGORIES
                ):
                    mail["classification"] = rule_result

                else:
                    # 3. Final fallback if both classifiers fail.
                    mail["classification"] = {
                        "category": "PERSONAL/OTHERS",
                        "confidence": 0.0,
                        "method": "fallback",
                    }

            inbox.append(mail)

        return jsonify({
            "count": len(inbox),
            "messages": inbox,
        })

    except Exception:
        app.logger.exception("Gmail inbox fetch failed")

        return jsonify({
            "error": "Could not fetch inbox. Check the server log."
        }), 500


if __name__ == "__main__":
    # Local development only.
    app.run(host="127.0.0.1", port=5000, debug=True)
