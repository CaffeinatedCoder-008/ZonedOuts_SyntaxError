import { useCallback, useEffect, useState } from "react";

// ---- Types the UI uses -------------------------------------------------------

export type DeadlineInfo = {
  date: string; // YYYY-MM-DD
  text: string | null;
  action: string | null;
};

export type Email = {
  id: string;
  sender: string;
  address: string;
  subject: string;
  preview: string;
  body: string;
  category: string;
  time: string;
  receivedAt: string;
  unread: boolean;
  starred: boolean;
  urgent?: boolean;
  deadline: DeadlineInfo | null;
  method: string;
  reason: string;
};

export type DeadlineItem = {
  id: string;
  date: string;
  day: string;
  month: string;
  title: string;
  sub: string;
  when: string;
  daysLeft: number;
};

// ---- Backend category -> the label this UI shows -----------------------------

const CATEGORY_MAP: Record<string, string> = {
  "PROFESSOR/TA": "Professors and TAs",
  "ACADEMIC AND SECTIONS": "Academic Section",
  "DEPARTMENT AND ADMIN": "Departments and Administration",
  "COURSES AND ANNOUNCEMENTS": "Courses and Announcements",
  "CLUBS AND SOCIETIES": "Clubs and Societies",
  "PLACEMENT AND INTERNSHIPS": "Placements and Internships",
  "INTERNATIONAL OPPORTUNITIES": "International Opportunities",
  SCHOLARSHIPS: "Scholarships and Fellowships",
  "HOSTEL MESS": "Hostel and Mess",
  "CR/BR UPDATES": "CR and BR Updates",
  "PROMOTION/NEWSLETTERS": "Promotions and Newsletters",
  "PERSONAL/OTHERS": "Personal and Other",
};

// ---- Small helpers -----------------------------------------------------------

function senderName(raw?: string | null): string {
  if (!raw) return "Unknown sender";
  const cleaned = raw.replace(/<[^>]*>/g, "").replace(/"/g, "").trim();
  return cleaned || raw;
}

function senderAddress(raw?: string | null): string {
  if (!raw) return "";
  const match = raw.match(/<([^>]+)>/);
  if (match) return match[1];
  return raw.includes("@") ? raw.trim() : "";
}

// "2026-10-23" -> local Date (avoids the timezone shift of new Date("2026-10-23")).
function parseDay(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function daysUntil(iso: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((parseDay(iso).getTime() - today.getTime()) / 86400000);
}

function whenLabel(days: number): string {
  if (days < 0) return days === -1 ? "Overdue by 1 day" : `Overdue by ${-days} days`;
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  return `In ${days} days`;
}

function formatTime(raw?: string | null): string {
  if (!raw) return "";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  return date.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

// ---- Backend JSON -> UI shapes -----------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function toEmail(m: any): Email {
  const classification = m.classification || {};
  const backendCategory: string = classification.category || "PERSONAL/OTHERS";

  const deadline: DeadlineInfo | null =
    m.deadline && typeof m.deadline.date === "string"
      ? {
          date: m.deadline.date,
          text: m.deadline.text ?? null,
          action: m.deadline.action ?? null,
        }
      : null;

  const body: string = m.body_preview || m.snippet || "";
  const preview: string = (m.snippet || body).slice(0, 160);
  const urgent = deadline ? daysUntil(deadline.date) <= 2 : false;

  return {
    id: String(m.id),
    sender: senderName(m.original_sender || m.actual_sender),
    address: senderAddress(m.original_sender || m.actual_sender),
    subject: m.original_subject || m.actual_subject || "(no subject)",
    preview,
    body,
    category: CATEGORY_MAP[backendCategory] || "Personal and Other",
    time: formatTime(m.original_date || m.actual_date),
    receivedAt: m.original_date || m.actual_date || "",
    unread: Boolean(m.unread),
    starred: Boolean(m.starred),
    urgent,
    deadline,
    method: classification.method || "",
    reason: classification.reason || "",
  };
}

export function toDeadlineItems(emails: Email[]): DeadlineItem[] {
  return emails
    .filter((email) => email.deadline)
    .map((email) => {
      const deadline = email.deadline as DeadlineInfo;
      const date = parseDay(deadline.date);
      const days = daysUntil(deadline.date);
      return {
        id: email.id,
        date: deadline.date,
        day: String(date.getDate()),
        month: date.toLocaleDateString(undefined, { month: "short" }).toUpperCase(),
        title: deadline.action || deadline.text || email.subject,
        sub: `${email.subject} · ${email.category}`,
        when: whenLabel(days),
        daysLeft: days,
        sortKey: deadline.date,
      };
    })
    .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
    .map(({ sortKey: _sortKey, ...item }) => item);
}

// ---- The hook the page uses --------------------------------------------------

export type InboxStatus = "loading" | "signedOut" | "ready" | "error";

type InboxState = {
  status: InboxStatus;
  emails: Email[];
  deadlines: DeadlineItem[];
  summary: string;
  error: string;
};

const INITIAL: InboxState = {
  status: "loading",
  emails: [],
  deadlines: [],
  summary: "",
  error: "",
};

export function useInbox() {
  const [state, setState] = useState<InboxState>(INITIAL);

  const load = useCallback(async (refresh = false) => {
    setState((current) => ({ ...current, status: "loading", error: "" }));

    let response: Response;
    try {
      response = await fetch("/gmail/inbox" + (refresh ? "?refresh=1" : ""), {
        headers: { Accept: "application/json" },
      });
    } catch {
      setState({
        ...INITIAL,
        status: "error",
        error: "Can’t reach the server. Check your connection and try again.",
      });
      return;
    }

    if (response.status === 401) {
      setState({ ...INITIAL, status: "signedOut" });
      return;
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let data: any;
    try {
      data = await response.json();
    } catch {
      // e.g. the hosting platform's own error page while the app restarts
      setState({
        ...INITIAL,
        status: "error",
        error:
          "The server isn’t answering properly. It may be restarting, so wait a minute and try again.",
      });
      return;
    }

    if (!response.ok) {
      setState({
        ...INITIAL,
        status: "error",
        error: data?.error || `The server returned an error (${response.status}).`,
      });
      return;
    }

    const emails = Array.isArray(data.messages) ? data.messages.map(toEmail) : [];
    const bits = [`${emails.length} mail${emails.length === 1 ? "" : "s"}`];
    if (typeof data.from_cache === "number") bits.push(`${data.from_cache} saved`);
    if (typeof data.took_seconds === "number") bits.push(`${data.took_seconds}s`);

    setState({
      status: "ready",
      emails,
      deadlines: toDeadlineItems(emails),
      summary: bits.join(" · "),
      error: "",
    });
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  return { ...state, reload: load };
}
