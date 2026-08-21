import React, { useState, useEffect, useRef } from "react";
import { MessageList } from "./MessageList";
import { SectionProgress } from "./SectionProgress";
import { sendChatMessage } from "../services/api";

export function ChatWindow({ formName, sessionId, isResume }) {

  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [formState, setFormState] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [sections, setSections] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const applyResponse = (data, appendBot = true) => {
    if (data.response && appendBot) {
      setMessages((prev) => [...prev, { sender: "bot", text: data.response }]);
    }
    if (data.current_state) {
      setFormState(data.current_state);
    }
    if (data.validation_errors) {
      setValidationErrors(data.validation_errors);
    }
    if (data.action_plan?.action === "COMPLETE_FORM") {
      setIsComplete(true);
    }
    // sections is present (even if null) whenever the backend knows
    // about this form -- explicitly set it so a non-sectioned form
    // correctly clears out any stale progress bar.
    setSections(data.sections ?? null);
  };

  // For a sectioned form, show fields from any section that's either
  // complete or currently active -- so the panel only ever grows as
  // you make progress, and going BACK to edit an earlier part
  // doesn't make later, already-filled sections disappear from view.
  // Forms without sections show the full state, unchanged.
  const visibleFormState = (() => {
    if (!sections) return formState;

    const visibleFieldNames = new Set(
      sections
        .filter((s) => s.complete || s.active)
        .flatMap((s) => s.fields || [])
    );

    return Object.fromEntries(
      Object.entries(formState).filter(([key]) => visibleFieldNames.has(key))
    );
  })();

  useEffect(() => {
    let isMounted = true;

    async function startSession() {
      setLoading(true);
      setMessages(
        isResume
          ? [{ sender: "bot", text: "Welcome back! Picking up where you left off..." }]
          : []
      );
      setFormState({});
      setValidationErrors({});
      setIsComplete(false);
      setSections(null);

      try {
        const data = await sendChatMessage(sessionId, formName, "");
        if (!isMounted) return;
        applyResponse(data);
      } catch (err) {
        if (isMounted) {
          setMessages([{ sender: "bot", text: "Unable to connect to the server." }]);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    startSession();

    return () => {
      isMounted = false;
    };
  }, [sessionId, formName]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading || isComplete) return;

    const userText = inputMessage.trim();
    setInputMessage("");

    setMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setLoading(true);

    try {
      const data = await sendChatMessage(sessionId, formName, userText);
      applyResponse(data);
    } catch (err) {
      setMessages((prev) => [...prev, { sender: "bot", text: "Error communicating with the server." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigateSection = async (targetIndex) => {
    if (loading || isComplete) return;
    setLoading(true);

    try {
      // Navigation via the progress bar doesn't go through the text
      // input -- send an empty message with target_section set, and
      // don't echo a "You" bubble for it (nothing was actually typed).
      const data = await sendChatMessage(sessionId, formName, "", targetIndex);
      applyResponse(data);
    } catch (err) {
      setMessages((prev) => [...prev, { sender: "bot", text: "Error communicating with the server." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.wrapper}>
      <div style={styles.chatSection}>
        <div style={styles.headerBar}>
          <div style={styles.logoBadge}>P</div>
          <h2 style={styles.heading}>Conversational Assistant</h2>
        </div>

        {sections && (
          <SectionProgress sections={sections} onNavigate={handleNavigateSection} />
        )}

        <MessageList messages={messages} loading={loading} />
        <div ref={messagesEndRef} />

        <form onSubmit={handleSend} style={styles.form}>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={isComplete ? "Form submitted" : "Type your response..."}
            disabled={loading || isComplete}
            style={styles.input}
          />
          <button
            type="submit"
            disabled={loading || isComplete || !inputMessage.trim()}
            style={{
              ...styles.button,
              opacity: loading || isComplete || !inputMessage.trim() ? 0.6 : 1,
              cursor: loading || isComplete || !inputMessage.trim() ? "not-allowed" : "pointer"
            }}
          >
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>

      <div style={styles.sidePanel}>
        <h3 style={styles.sideHeading}>Form Progress</h3>

        <div style={styles.card}>
          <h4 style={styles.cardTitle}>Collected Data</h4>
          <pre style={styles.jsonBox}>
            {JSON.stringify(visibleFormState, null, 2)}
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
    fontFamily: "Inter, sans-serif",
    width: "100%"
  },
  chatSection: {
    flex: "2",
    display: "flex",
    flexDirection: "column",
    minWidth: "0"
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
    gap: "14px",
    minWidth: "220px"
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
