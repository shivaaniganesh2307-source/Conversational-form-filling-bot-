import React, { useState, useEffect } from "react";
import { ChatWindow } from "./components/ChatWindow";
import { getAvailableForms } from "./services/api";

export default function App() {
  const [forms, setForms] = useState([]);
  const [selectedForm, setSelectedForm] = useState("user_registration");

  // Fetch form list from backend on load
  useEffect(() => {
    getAvailableForms().then((data) => {
      if (data.forms && data.forms.length > 0) {
        setForms(data.forms);
        setSelectedForm(data.forms[0]);
      }
    });
  }, []);

  return (
    <div style={styles.appContainer}>
      {/* Top Navbar */}
      <header style={styles.navbar}>
        <div style={styles.navBrand}>
          <div style={styles.logoBadge}>P</div>
          <span style={styles.brandTitle}>Plateau Form Assistant</span>
        </div>

        {/* Dynamic Form Dropdown */}
        <div style={styles.selectorContainer}>
          <label style={styles.selectorLabel}>Form: </label>
          <select 
            value={selectedForm} 
            onChange={(e) => setSelectedForm(e.target.value)}
            style={styles.selectDropdown}
          >
            {forms.map((f) => (
              <option key={f} value={f}>
                {f.replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={styles.mainContent}>
        {/* Pass selectedForm dynamically instead of hardcoding */}
        <ChatWindow key={selectedForm} formName={selectedForm} />
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
    gap: "8px",
  },
  selectorLabel: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#0B3B60",
  },
  selectDropdown: {
    padding: "6px 12px",
    borderRadius: "6px",
    border: "1px solid #CBD5E1",
    fontSize: "14px",
    outline: "none",
  },
  mainContent: {
    flex: "1",
    padding: "20px",
  },
};