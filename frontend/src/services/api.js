const API_BASE_URL = "/api";

// Fetch available form schemas. Each entry is {id, name}.
export async function getAvailableForms() {
  try {
    const response = await fetch(`${API_BASE_URL}/forms`);
    if (!response.ok) {
      throw new Error(`Server status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("API Error fetching forms:", error);
    return { forms: [{ id: "user_registration_form", name: "User Registration" }] };
  }
}

// Send user message to chatbot. targetSection (optional) lets the
// caller jump directly to a section of a multi-part form, e.g. from
// clicking a progress-bar pill, without needing to phrase it as a
// chat message.
export async function sendChatMessage(sessionId, formName, message, targetSection = null) {
  try {
    const body = {
      session_id: sessionId,
      form_name: formName,
      message: message,
    };
    if (targetSection !== null) {
      body.target_section = targetSection;
    }

    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Server status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API Error:", error);
    return {
      response: "Unable to reach server. Please ensure Flask is running on port 5000.",
      current_state: {},
      validation_errors: {},
    };
  }
}

// Fetch the live status/data for one session -- used to build the
// "My Forms" list and to resume a session.
export async function getSessionDetails(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
    if (!response.ok) {
      return null; // session no longer exists server-side -- caller should handle gracefully
    }
    return await response.json();
  } catch (error) {
    console.error("API Error fetching session:", error);
    return null;
  }
}
