import React, { useState, useEffect } from "react";
import { ChatWindow } from "./components/ChatWindow";
import { MyForms } from "./components/MyForms";
import { getAvailableForms } from "./services/api";
import { rememberSession } from "./services/sessionStore";

// view: "landing" | "chat" | "myforms"

export default function App() {
  const [forms, setForms] = useState([]);
  const [selectedFormId, setSelectedFormId] = useState("");
  const [view, setView] = useState("landing");
  const [loading, setLoading] = useState(true);

  // Active chat session details -- set either when starting a new
  // form (fresh session id) or resuming one (from My Forms)
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activeFormName, setActiveFormName] = useState("");
  const [isResume, setIsResume] = useState(false);

  useEffect(() => {
    async function loadForms() {
      try {
        const data = await getAvailableForms();
        if (data.forms && data.forms.length > 0) {
          setForms(data.forms);
          setSelectedFormId(data.forms[0].id);
        }
      } catch (err) {
        console.error("Failed to load forms", err);
      } finally {
        setLoading(false);
      }
    }
    loadForms();
  }, []);

  const handleStartSession = (e) => {
    e.preventDefault();
    if (!selectedFormId) return;

    const formMeta = forms.find((f) => f.id === selectedFormId);
    const formName = formMeta ? formMeta.name : selectedFormId;

    const newSessionId =
      "session_" + Date.now() + "_" + Math.random().toString(36).substring(2, 9);

    rememberSession(newSessionId, selectedFormId, formName);

    setActiveSessionId(newSessionId);
    setActiveFormName(formName);
    setIsResume(false);
    setView("chat");
  };

  const handleResume = (sessionId, formId, formName) => {
    setSelectedFormId(formId);
    setActiveSessionId(sessionId);
    setActiveFormName(formName);
    setIsResume(true);
    setView("chat");
  };

  const handleSwitchForm = () => {
    setActiveSessionId(null);
    setIsResume(false);
    setView("landing");
  };

  if (loading) {
    return (
      <div style={styles.loadingScreen}>
        Loading available forms...
      </div>
    );
  }

  return (
    <div style={styles.appContainer}>
      <header style={styles.navbar}>
        <div style={styles.navBrand}>
          <div style={styles.logoBadge}>P</div>
          <span style={styles.brandTitle}>Plateau Form Assistant</span>
        </div>

        <div style={styles.navRight}>
          {view === "chat" && (
            <div style={styles.selectorContainer}>
              <span style={styles.activeFormIndicator}>
                Active Form: <strong>{activeFormName}</strong>
              </span>
              <button onClick={handleSwitchForm} style={styles.switchButton}>
                Switch Form
              </button>
            </div>
          )}

          {view !== "myforms" && (
            <button onClick={() => setView("myforms")} style={styles.myFormsButton}>
              My Forms
            </button>
          )}
        </div>
      </header>

      <main style={styles.mainContent}>
        {view === "landing" && (
          <div style={styles.landingCard}>
            <h2 style={styles.landingTitle}>Select a Form to Begin</h2>
            <p style={styles.landingText}>
              Choose a dynamic registration or application schema from your backend to initialize your assistant session.
            </p>

            <form onSubmit={handleStartSession}>
              <div style={styles.formControlGroup}>
                <label style={styles.selectorLabel}>Available Forms:</label>
                <select
                  value={selectedFormId}
                  onChange={(e) => setSelectedFormId(e.target.value)}
                  style={styles.selectDropdownLanding}
                >
                  {forms.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
              </div>

              <button type="submit" style={styles.startButton}>
                Start Session
              </button>
            </form>
          </div>
        )}

        {view === "myforms" && (
          <MyForms onResume={handleResume} onBack={() => setView("landing")} />
        )}

        {view === "chat" && activeSessionId && (
          <ChatWindow
            key={activeSessionId}
            sessionId={activeSessionId}
            formName={selectedFormId}
            isResume={isResume}
          />
        )}
      </main>
    </div>
  );
}

const styles = {
  appContainer: {
    minHeight: "100vh",
    backgroundColor: "#FAF9F8",
    display: "flex",
    flexDirection: "column",
  },
  loadingScreen: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    fontSize: "18px",
    color: "#0B3B60",
    fontWeight: "600",
  },
  navbar: {
    backgroundColor: "#FFFFFF",
    borderBottom: "1px solid #E2E8F0",
    padding: "16px 32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
  },
  navBrand: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  logoBadge: {
    backgroundColor: "rgb(241, 176, 54)",
    color: "#FFFFFF",
    fontWeight: "bold",
    borderRadius: "8px",
    width: "32px",
    height: "32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "16px",
  },
  brandTitle: {
    color: "#0B3B60",
    fontSize: "18px",
    fontWeight: "700",
    letterSpacing: "-0.01em",
  },
  navRight: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },
  selectorContainer: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },
  activeFormIndicator: {
    fontSize: "14px",
    color: "#334155",
  },
  switchButton: {
    backgroundColor: "#F1F5F9",
    color: "#0B3B60",
    border: "1px solid #CBD5E1",
    padding: "6px 12px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  myFormsButton: {
    backgroundColor: "#0B3B60",
    color: "#FFFFFF",
    border: "none",
    padding: "8px 16px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  mainContent: {
    flex: "1",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
  },
  landingCard: {
    maxWidth: "460px",
    width: "100%",
    margin: "80px auto",
    padding: "32px",
    backgroundColor: "#FFFFFF",
    borderRadius: "12px",
    boxShadow: "0 4px 16px rgba(0,0,0,0.06)",
    border: "1px solid #E2E8F0",
    textAlign: "center",
  },
  landingTitle: {
    color: "#0B3B60",
    fontSize: "22px",
    fontWeight: "700",
    marginBottom: "8px",
  },
  landingText: {
    color: "#64748B",
    fontSize: "14px",
    lineHeight: "1.5",
    marginBottom: "24px",
  },
  formControlGroup: {
    textAlign: "left",
    marginBottom: "20px",
  },
  selectorLabel: {
    display: "block",
    fontSize: "13px",
    fontWeight: "600",
    color: "#0B3B60",
    marginBottom: "8px",
  },
  selectDropdownLanding: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "6px",
    border: "1px solid #CBD5E1",
    fontSize: "14px",
    outline: "none",
    backgroundColor: "#FFFFFF",
    boxSizing: "border-box",
  },
  startButton: {
    width: "100%",
    backgroundColor: "rgb(241, 176, 54)",
    color: "#FFFFFF",
    border: "none",
    padding: "12px",
    borderRadius: "6px",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "pointer",
    boxShadow: "0 2px 4px rgba(241, 176, 54, 0.3)",
  },
};
