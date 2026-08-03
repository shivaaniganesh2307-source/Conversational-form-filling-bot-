// Replace the domain below with your exact copied Port 5000 Forwarded Address from VS Code
const API_BASE_URL = "https://opulent-space-trout-69jwgr5rr67rcx45x-5000.app.github.dev/api";


export async function sendChatMessage(sessionId, formName, message) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        form_name: formName,
        message: message,
      }),
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