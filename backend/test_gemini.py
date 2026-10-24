# Run from the repo root:  python -m backend.test_gemini
# Needs GEMINI_API_KEY in your .env. This makes REAL Gemini calls (4 requests).
try:
    from .ai_classifier import classify_with_ai
except ImportError:
    from ai_classifier import classify_with_ai

# Expected deadline for each mail is written in the comment above it.
# (2026-10-19 is a Monday, so "this Friday" = 2026-10-23.)
test_emails = [
    # Expected: COURSES AND ANNOUNCEMENTS, deadline 2026-10-23
    {
        "actual_sender": "prof.sharma@iitr.ac.in",
        "actual_subject": "Assignment 3",
        "actual_date": "Mon, 19 Oct 2026 10:15:00 +0530",
        "snippet": "Please submit Assignment 3.",
        "body_preview": "Submit Assignment 3 on the course portal by this Friday 5 PM.",
    },
    # Expected: CLUBS AND SOCIETIES, deadline null (an invitation, nothing to submit)
    {
        "actual_sender": "helios@iitroorkee.ac.in",
        "actual_subject": "HELIOS Intro Talk",
        "actual_date": "Mon, 19 Oct 2026 12:00:00 +0530",
        "snippet": "Join us for our introductory session.",
        "body_preview": "Learn about the club and meet its members. Everyone is welcome.",
    },
    # Expected: deadline 2026-10-28 (explicit date)
    {
        "actual_sender": "academic.office@iitroorkee.ac.in",
        "actual_subject": "UGTA Feedback Form",
        "actual_date": "Tue, 20 Oct 2026 09:00:00 +0530",
        "snippet": "Please submit your feedback.",
        "body_preview": "The Academic Affairs Office requests feedback on UGTA performance. "
                        "Fill the form before 28 October 2026.",
    },
    # Expected: deadline null (no date given, so it must NOT be guessed)
    {
        "actual_sender": "unknown@example.com",
        "actual_subject": "Tutorial Class 4",
        "actual_date": "Wed, 21 Oct 2026 08:00:00 +0530",
        "snippet": "Tutorial details attached.",
        "body_preview": "Complete the assigned tutorial questions before the next class.",
    },
]

for email in test_emails:
    print("\nSubject:", email["actual_subject"])
    result = classify_with_ai(email)

    if result is None:
        print("Result: None (Gemini failed, check the [GEMINI ERROR] line above)")
        continue

    print("Category:", result["category"], "| method:", result["method"])
    print("Deadline:", result["deadline"])
