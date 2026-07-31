import React from "react";
import { ChatWindow } from "./components/ChatWindow";

export default function App() {
  return (
    <div style={styles.appContainer}>
      {/* Top Navbar */}
      <header style={styles.navbar}>
        <div style={styles.navBrand}>
          <div style={styles.logoBadge}>P</div>
          <span style={styles.brandTitle}>Plateau Form Assistant</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={styles.mainContent}>
        <ChatWindow formName="user_registration" />
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
  mainContent: {
    flex: "1",
    padding: "20px",
  },
};