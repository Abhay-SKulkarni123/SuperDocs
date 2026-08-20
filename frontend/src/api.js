const API_URL = "http://127.0.0.1:8000";

export async function checkHealth() {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }

  return response.json();
}

export async function createRun() {
  const response = await fetch(`${API_URL}/runs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    let message = `Backend returned ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep the default message when the response isn't JSON.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function uploadDocument(runId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/runs/${runId}/documents`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = `Backend returned ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep the default message.
    }

    throw new Error(message);
  }

  return response.json();
}