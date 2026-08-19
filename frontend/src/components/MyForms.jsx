import React, { useState, useEffect } from "react";
import { getRememberedSessions, forgetSession } from "../services/sessionStore";
import { getSessionDetails } from "../services/api";

export function MyForms({ onResume, onBack }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadSessions() {
      const remembered = getRememberedSessions();

      const withDetails = await Promise.all(
        remembered.map(async (s) => {
          const details = await getSessionDetails(s.sessionId);
          return { ...s, details };
        })
      );

      if (isMounted) {
        setSessions(withDetails);
        setLoading(false);
      }
    }

    loadSessions();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleRemove = (sessionId) => {
    forgetSession(sessionId);
    setSessions((prev) => prev.filter((s) => s.sessionId !== sessionId));
  };

  if (loading) {
    return <div style={styles.loadingText}>Loading your forms...</div>;
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.headerRow}>
        <h2 style={styles.title}>My Forms</h2>
        <button onClick={onBack} style={styles.backButton}>
          Back
        </button>
      </div>

      {sessions.length === 0 && (
        <p style={styles.emptyText}>
          You haven't started any forms on this device yet.
        </p>
      )}

      <div style={styles.list}>
        {sessions.map((s) => {
          const isAvailable = !!s.details;
          const status = s.details?.status;
          const formName = s.details?.form_name || s.formName;
          const isCompleted = status === "COMPLETED";

          return (
            <div key={s.sessionId} style={styles.card}>
              <div style={styles.cardMain}>
                <div style={styles.cardTitle}>{formName}</div>
                <div style={styles.cardMeta}>
                  {isAvailable ? (
                    <span
                      style={{
                        ...styles.badge,
                        backgroundColor: isCompleted ? "#DCFCE7" : "#FEF3C7",
                        color: isCompleted ? "#166534" : "#92400E",
                      }}
                    >
                      {isCompleted ? "Completed" : "In progress"}
                    </span>
                  ) : (
                    <span
                      style={{
                        ...styles.badge,
                        backgroundColor: "#FEE2E2",
                        color: "#991B1B",
                      }}
                    >
                      No longer available
                    </span>
                  )}
                  <span style={styles.dateText}>
                    Started {new Date(s.startedAt).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div style={styles.cardActions}>
                {isAvailable && (
                  <button
                    onClick={() => onResume(s.sessionId, s.formId, formName)}
                    style={styles.continueButton}
                  >
                    {isCompleted ? "View" : "Continue"}
                  </button>
                )}
                <button
                  onClick={() => handleRemove(s.sessionId)}
                  style={styles.removeButton}
                >
                  Remove
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    maxWidth: "640px",
    width: "100%",
    margin: "40px auto",
    padding: "0 20px",
  },
  loadingText: {
    textAlign: "center",
    margin: "80px auto",
    color: "#64748B",
    fontSize: "15px",
  },
  headerRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },
  title: {
    color: "#0B3B60",
    fontSize: "22px",
    fontWeight: "700",
    margin: 0,
  },
  backButton: {
    backgroundColor: "#F1F5F9",
    color: "#0B3B60",
    border: "1px solid #CBD5E1",
    padding: "6px 14px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  emptyText: {
    color: "#64748B",
    fontSize: "14px",
    textAlign: "center",
    marginTop: "40px",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  card: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "16px 18px",
    backgroundColor: "#FFFFFF",
    border: "1px solid #E2E8F0",
    borderRadius: "10px",
  },
  cardMain: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  cardTitle: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#0B3B60",
  },
  cardMeta: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  badge: {
    fontSize: "11px",
    fontWeight: "700",
    padding: "3px 8px",
    borderRadius: "999px",
    textTransform: "uppercase",
    letterSpacing: "0.03em",
  },
  dateText: {
    fontSize: "12px",
    color: "#94A3B8",
  },
  cardActions: {
    display: "flex",
    gap: "8px",
  },
  continueButton: {
    backgroundColor: "#F15A36",
    color: "white",
    border: "none",
    padding: "8px 16px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  removeButton: {
    backgroundColor: "transparent",
    color: "#94A3B8",
    border: "1px solid #E2E8F0",
    padding: "8px 12px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
};
