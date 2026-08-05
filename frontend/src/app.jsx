import React, { useState, useEffect } from "react";
import { ChatWindow } from "./components/ChatWindow";
import { getAvailableForms } from "./services/api";

export default function App() {
  const [forms, setForms] = useState([]);
  const [selectedForm, setSelectedForm] = useState("");
  const [isSessionStarted, setIsSessionStarted] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch form list from backend on load
  useEffect(() => {
    async function loadForms() {
      try {
        const data = await getAvailableForms();
        if (data.forms && data.forms.length > 0) {
          setForms(data.forms);
          setSelectedForm(data.forms[0]);
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
    if (selectedForm) {
      setIsSessionStarted(true);
    }
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
      {/* Top Navbar */}
      <header style={styles.navbar}>
        <div style={styles.navBrand}>
          <div style={styles.logoBadge}>P</div>
          <span style={styles.brandTitle}>Plateau Form Assistant</span>
        </div>

        {/* Show selector in navbar only if session has started, with a switch option */}
        {isSessionStarted && (
          <div style={styles.selectorContainer}>
            <span style={styles.activeFormIndicator}>
              Active Form: <strong>{selectedForm.replace('_', ' ').toUpperCase()}</strong>
            </span>
            <button 
              onClick={() => setIsSessionStarted(false)}
              style={styles.switchButton}
            >
              Switch Form
            </button>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main style={styles.mainContent}>
        {!isSessionStarted ? (
          /* --- LANDING VIEW FOR FORM SELECTION --- */
          <div style={styles.landingCard}>
            <h2 style={styles.landingTitle}>Select a Form to Begin</h2>
            <p style={styles.landingText}>
              Choose a dynamic registration or application schema from your backend to initialize your assistant session.
            </p>

            <form onSubmit={handleStartSession}>
              <div style={styles.formControlGroup}>
                <label style={styles.selectorLabel}>Available Forms:</label>
                <select 
                  value={selectedForm} 
                  onChange={(e) => setSelectedForm(e.target.value)}
                  style={styles.selectDropdownLanding}
                >
                  {forms.map((f) => (
                    <option key={f} value={f}>
                      {f.replace('_', ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <button type="submit" style={styles.startButton}>
                Start Session
              </button>
            </form>
          </div>
        ) : (
          /* --- ACTIVE CHAT SESSION VIEW --- */
          <ChatWindow key={selectedForm} formName={selectedForm} />
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
    boxSizing: "box-sizing",
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