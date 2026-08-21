const STORAGE_KEY = "plateau_form_sessions";
const MAX_REMEMBERED = 30;

// Every session this browser has ever started gets recorded here so
// "My Forms" and "resume" work without any login system -- purely
// client-side, tied to this browser/device only.

export function getRememberedSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.error("Could not read remembered sessions:", err);
    return [];
  }
}

export function rememberSession(sessionId, formId, formName) {
  try {
    const sessions = getRememberedSessions();

    // Don't add a duplicate if it's already tracked
    if (sessions.some((s) => s.sessionId === sessionId)) return;

    sessions.unshift({
      sessionId,
      formId,
      formName,
      startedAt: new Date().toISOString(),
    });

    // Cap how many we remember so this doesn't grow forever
    const trimmed = sessions.slice(0, MAX_REMEMBERED);

    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch (err) {
    console.error("Could not save session to local storage:", err);
  }
}

export function forgetSession(sessionId) {
  try {
    const sessions = getRememberedSessions().filter(
      (s) => s.sessionId !== sessionId
    );
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch (err) {
    console.error("Could not remove session from local storage:", err);
  }
}
