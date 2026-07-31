import React from "react";

export function MessageList({ messages, loading }) {
  return (
    <div style={styles.container}>
      {messages.map((msg, index) => (
        <div
          key={index}
          style={{
            ...styles.bubble,
            alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
            backgroundColor: msg.sender === "user" ? "#F15A36" : "#FFFFFF",
            color: msg.sender === "user" ? "#FFFFFF" : "#0B3B60",
            border: msg.sender === "user" ? "none" : "1px solid #E5E7EB",
          }}
        >
          <strong
            style={{
              ...styles.sender,
              color: msg.sender === "user" ? "#FFEAD8" : "#8892B0",
            }}
          >
            {msg.sender === "user" ? "You" : "Assistant"}
          </strong>
          <p style={styles.text}>{msg.text}</p>
        </div>
      ))}

      {loading && (
        <div
          style={{
            ...styles.bubble,
            alignSelf: "flex-start",
            backgroundColor: "#FFFFFF",
            border: "1px solid #E5E7EB",
            color: "#8892B0",
            fontStyle: "italic",
          }}
        >
          Assistant is thinking...
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    padding: "16px",
    overflowY: "auto",
    height: "420px",
    backgroundColor: "#FAF9F8",
    borderRadius: "12px",
    border: "1px solid #E2E8F0",
  },
  bubble: {
    maxWidth: "75%",
    padding: "10px 14px",
    borderRadius: "12px",
    fontSize: "14px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  },
  sender: {
    fontSize: "11px",
    display: "block",
    marginBottom: "2px",
  },
  text: {
    margin: 0,
    lineHeight: "1.4",
  },
};