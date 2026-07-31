import React, { useState, useEffect, useRef } from "react";
import { MessageList } from "./MessageList";
import { sendChatMessage } from "../services/api";

export function ChatWindow({ formName = "user_registration" }) {
  const [sessionId] = useState(() =>
    "session_" + Math.random().toString(36).substring(2, 9)
  );

  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [formState, setFormState] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [loading, setLoading] = useState(false);
  
  // Ref for auto-scrolling
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    async function startSession() {
      setLoading(true);
      const data = await sendChatMessage(sessionId, formName, "");

      if (data.response) {
        setMessages([{ sender: "bot", text: data.response }]);
      }
      if (data.current_state) {
        setFormState(data.current_state);
      }
      setLoading(false);
    }

    startSession();
  }, [sessionId, formName]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userText = inputMessage.trim();
    setInputMessage("");

    setMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setLoading(true);

    const data = await sendChatMessage(sessionId, formName, userText);

    if (data.response) {
      setMessages((prev) => [...prev, { sender: "bot", text: data.response }]);
    }
    if (data.current_state) {
      setFormState(data.current_state);
    }
    if (data.validation_errors) {
      setValidationErrors(data.validation_errors);
    }

    setLoading(false);
  };

  return (
    <div style={styles.wrapper}>
      {/* Left Side: Chat Interface */}
      <div style={styles.chatSection}>
        <div style={styles.headerBar}>
          <div style={styles.logoBadge}>P</div>
          <h2 style={styles.heading}>Conversational Assistant</h2>
        </div>

        <MessageList messages={messages} loading={loading} />
        <div ref={messagesEndRef} />

        <form onSubmit={handleSend} style={styles.form}>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your response..."
            disabled={loading}
            style={styles.input}
          />
          <button
            type="submit"
            disabled={loading || !inputMessage.trim()}
            style={{
              ...styles.button,
              opacity: loading || !inputMessage.trim() ? 0.6 : 1,
              cursor: loading || !inputMessage.trim() ? "not-allowed" : "pointer"
            }}
          >
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>

      {/* Right Side: Dynamic Form State Visualizer */}
      <div style={styles.sidePanel}>
        <h3 style={styles.sideHeading}>Form Progress</h3>

        <div style={styles.card}>
          <h4 style={styles.cardTitle}>Collected Data</h4>
          <pre style={styles.jsonBox}>
            {JSON.stringify(formState, null, 2)}
          </pre>
        </div>

        {Object.keys(validationErrors).length > 0 && (
          <div
            style={{
              ...styles.card,
              borderColor: "#F15A36",
              backgroundColor: "#FFF5F2"
            }}
          >
            <h4 style={{ ...styles.cardTitle, color: "#F15A36" }}>
              Validation Errors
            </h4>
            <pre style={{ ...styles.jsonBox, color: "#C2410C" }}>
              {JSON.stringify(validationErrors, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    display: "flex",
    gap: "24px",
    maxWidth: "960px",
    margin: "30px auto",
    fontFamily: "Inter, sans-serif"
  },
  chatSection: {
    flex: "2",
    display: "flex",
    flexDirection: "column"
  },
  headerBar: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "12px"
  },
  logoBadge: {
    backgroundColor: "#F15A36",
    color: "white",
    width: "28px",
    height: "28px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    borderRadius: "8px",
    fontWeight: "bold"
  },
  heading: {
    fontSize: "20px",
    margin: 0,
    color: "#0B3B60"
  },
  sidePanel: {
    flex: "1",
    display: "flex",
    flexDirection: "column",
    gap: "14px"
  },
  sideHeading: {
    fontSize: "18px",
    margin: 0,
    color: "#0B3B60"
  },
  form: {
    display: "flex",
    gap: "10px",
    marginTop: "12px"
  },
  input: {
    flex: "1",
    padding: "12px",
    borderRadius: "8px",
    border: "1px solid #E2E8F0",
    fontSize: "14px",
    outline: "none"
  },
  button: {
    padding: "12px 22px",
    backgroundColor: "#F15A36",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontWeight: "600"
  },
  card: {
    padding: "14px",
    border: "1px solid #E2E8F0",
    borderRadius: "8px",
    backgroundColor: "#FFFFFF"
  },
  cardTitle: {
    fontSize: "12px",
    margin: "0 0 8px 0",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "#0B3B60"
  },
  jsonBox: {
    fontFamily: "monospace",
    fontSize: "12px",
    margin: 0,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word"
  }
};