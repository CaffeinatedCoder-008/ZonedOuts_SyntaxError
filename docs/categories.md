# Categories and Classification Rules (draft v0.1)

> Planning document. It defines **what each category means**, how to break ties, what counts as a deadline, and how to label test mails consistently. The backend's AI prompt, the frontend's colours and the test set all come from this file, so agree on it before building. Nothing here is code.

---

## 1. Default categories

Every mail gets **exactly one** default category, chosen by **who sent it and what it is for**.

| # | Category | What belongs here | Typical senders | Example subjects |
|---|---|---|---|---|
| 1 | **Academics** | Anything about a course you are taking: assignments, quizzes, lab schedules, course announcements | Professors, TAs, course mailing lists | "Quiz 2 syllabus", "Lab 4 submission extended" |
| 2 | **Academic Office** | Official institute administration: registration, fees, exam schedules, results, department notices | Academic section, departments, deans' offices | "Course registration opens", "End-sem timetable" |
| 3 | **Clubs & Societies** | Recruitments, events, meetings and announcements from clubs and technical or cultural societies | Club and society mailing lists | "ACM recruitments open", "Photography club meet" |
| 4 | **Placements & Internships** | Companies, drives, internship postings, placement cell notices, resume deadlines | Placement and internship cell | "Company X pre-placement talk", "Internship form closes" |
| 5 | **Hostel & Mess** | Hostel allotments, mess menus and rebates, maintenance, warden notices | Hostel offices, mess committees | "Mess rebate form", "Water supply maintenance" |
| 6 | **Student Bodies** | Student council, councils and gymkhana-style bodies, institute-wide student activities and fests | Student council, student affairs | "Nominations for council", "Fest volunteer signups" |
| 7 | **Promotions** | Marketing and sponsored content: discounts, product launches, outside event advertising | Companies, sponsors, external senders | "50% off this weekend" |
| 8 | **Newsletters** | Regular digests and subscribed updates | Newsletter and digest senders | "Weekly digest", "This month at the institute" |
| 9 | **Personal / Other** | Everything else: friends, family, receipts, account notices, anything that does not fit | Individuals, services | "Your order has shipped" |

### Not a category: "Needs attention"

"Needs attention" is a **flag** (`action_needed`) and a **sorted view** (the Deadlines page), not a folder. A mail from any category can need attention.

---

## 2. Tie-break rules

Many mails fit more than one category. Apply these in order and stop at the first rule that matches:

1. **Sender type beats topic.** A recruitment mail from a club is **Clubs & Societies** even if it sounds like marketing.
2. **Official institute sender beats everything else.** Placement cell mail is always **Placements & Internships**, even if it mentions a course or a fest.
3. **Course-specific mail goes to Academics.** General institute administration goes to **Academic Office**.
4. **Outside companies advertising something go to Promotions**, unless the mail is routed through the placement cell (then **Placements & Internships**).
5. **Subscribed regular digests go to Newsletters**, even when they carry club or academic news.
6. **If still unsure, choose Personal / Other** and lower the confidence value, so the UI can mark it as uncertain.

---

## 3. Custom categories

A student can create their own section, for example **International applications**: *"fellowships, exchange programs, foreign universities"*.

**Recommended design: custom categories are extra tags, not replacements.**

- A mail keeps its default category **and** can also match one or more custom categories.
- Example: a mail about a summer exchange program from the institute is **Academic Office** (default) *and* **International applications** (custom).
- The custom category's **description** is what the AI reads to decide whether a mail matches, so the form should encourage clear, specific descriptions.
- Deleting a custom category removes the tag only, and never deletes mails.
- Colours: custom categories use a separate palette from the default ones.

---

## 4. What the AI returns for each mail

Fields the classifier is expected to produce (planning level):

| Field | Description |
|---|---|
| category | One of the nine default categories |
| custom_categories | Ids of matching custom categories (can be empty) |
| summary | One or two plain sentences, up to about 30 words, mentioning the key action and date |
| deadline | Date the user must act by, or null |
| event_at | Date and time of an event, or null |
| action_needed | true or false |
| confidence | Number from 0 to 1 |

---

## 5. Deadline rules

**Deadline** = the last moment to act (submit, register, apply, reply). **Event date** = when something happens (talk, meeting, match). They are different, and a mail can have both: "Register by 25 Oct for the talk on 28 Oct" has deadline 25 Oct and event 28 Oct.

1. If several dates appear, the **deadline is the nearest future cut-off that requires action**.
2. **Relative dates** ("by Friday", "within 3 days") are resolved from the mail's received date. Everything is in **IST**.
3. **A date without a year** is assumed to be the next occurrence.
4. **Past dates are not deadlines.** They may be history ("results announced on 12 Oct").
5. **A date with no action** (for example "classes resume on 3 Nov") is not a deadline. It may be an event date.
6. **If there is no clear date, use null.** Never guess.

### Action needed

`action_needed = true` when the reader has to **do** something: register, submit, fill a form, reply, attend, or bring something. Pure information ("mess will be closed Sunday") is `false`.

### Urgency buckets for the UI

| Bucket | Rule |
|---|---|
| Overdue | Deadline before today and not marked done |
| Today | Deadline is today |
| Soon | 1 to 3 days away |
| This week | 4 to 7 days away |
| Later | More than 7 days away |

---

## 6. Test set: labeling guide

For the 50 to 60 real mails collected in the dummy account. **Keep this file out of the repo** (it contains real mail content). Store it locally as a spreadsheet or CSV.

| Column | Value |
|---|---|
| id | A running number |
| sender | Sender name or type (anonymize individuals) |
| subject | Subject line |
| true_category | One of the nine default categories |
| true_custom | Names of custom categories it should match, if any |
| true_deadline | Date or empty |
| true_action_needed | yes or no |
| notes | Anything tricky about this mail |

**Rules for labelers:**
- Two people label independently, then compare. Disagreements usually mean the category definitions above need a tweak. Settle them and update this file.
- Include **hard cases** on purpose: promotional-sounding club mails, multi-date mails, replies, one-line mails.
- Aim for at least **4 mails per category**, so every category can be tested.
- Accuracy for the pitch = correct categories divided by total mails.

---

## 7. Open questions

- [ ] Do we agree on these nine categories, or rename or merge any?
- [ ] Should **Student Bodies** and **Clubs & Societies** be merged for simplicity?
- [ ] Do we want a **tenth category, "Events"**, for fests and talks, or keep them under Clubs and Student Bodies?
- [ ] Which two people do the labeling?
- [ ] Category colours: which palette do the designers pick? (Light and dark mode, and distinguishable without relying on colour alone.)
