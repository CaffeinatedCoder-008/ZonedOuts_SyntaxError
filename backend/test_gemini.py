
from ai_classifier import classify_with_ai

test_emails = [
    {
        "actual_sender": "helios@iitroorkee.ac.in",
        "actual_subject": "HELIOS Intro Talk",
        "snippet": "Join us for our introductory session.",
        "body_preview": "Learn about the club and meet its members.",
    },
    {
        "actual_sender": "academic.office@iitroorkee.ac.in",
        "actual_subject": "UGTA Feedback Form",
        "snippet": "Please submit your feedback.",
        "body_preview": "The Academic Affairs Office requests feedback on UGTA performance.",
    },
    {
        "actual_sender": "unknown@example.com",
        "actual_subject": "Tutorial Class 4",
        "snippet": "Tutorial details attached.",
        "body_preview": "Complete the assigned tutorial questions before the next class.",
    },
]

for email in test_emails:
    print("\nSubject:", email["actual_subject"])
    result = classify_with_ai(email)
    print("Result:", result)
