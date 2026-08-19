import React from "react";

export function SectionProgress({ sections, onNavigate }) {
  if (!sections || sections.length === 0) return null;

  return (
    <div style={styles.wrapper}>
      {sections.map((section) => {
        const isClickable = section.navigable && !section.active;

        return (
          <button
            key={section.index}
            onClick={() => isClickable && onNavigate(section.index)}
            disabled={!isClickable}
            style={{
              ...styles.pill,
              ...(section.active ? styles.pillActive : {}),
              ...(section.complete && !section.active ? styles.pillComplete : {}),
              ...(!section.navigable && !section.active ? styles.pillUpcoming : {}),
              cursor: isClickable ? "pointer" : "default",
            }}
            title={
              section.navigable
                ? `Go to ${section.name}`
                : `${section.name} (not reached yet)`
            }
          >
            <span style={styles.pillIndex}>
              {section.complete ? "✓" : section.index + 1}
            </span>
            <span style={styles.pillLabel}>{section.name}</span>
          </button>
        );
      })}
    </div>
  );
}

const styles = {
  wrapper: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
    marginBottom: "16px",
  },
  pill: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 12px",
    borderRadius: "999px",
    border: "1px solid #E2E8F0",
    backgroundColor: "#FFFFFF",
    color: "#64748B",
    fontSize: "12px",
    fontWeight: "600",
  },
  pillActive: {
    backgroundColor: "#0B3B60",
    borderColor: "#0B3B60",
    color: "#FFFFFF",
  },
  pillComplete: {
    backgroundColor: "#F0FDF4",
    borderColor: "#BBF7D0",
    color: "#166534",
  },
  pillUpcoming: {
    backgroundColor: "#F8FAFC",
    borderColor: "#E2E8F0",
    color: "#CBD5E1",
  },
  pillIndex: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "16px",
    height: "16px",
    fontSize: "10px",
  },
  pillLabel: {
    whiteSpace: "nowrap",
  },
};
