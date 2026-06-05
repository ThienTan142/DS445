const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the HTTP status message.
    }
    throw new Error(detail);
  }

  return response.json();
}

export function predictSentiment(text) {
  return request('/predict', {
    method: 'POST',
    body: JSON.stringify({ text })
  });
}

export function getMetrics() {
  return request('/metrics');
}

export function getHealth() {
  return request('/health');
}

export function getConfig() {
  return request('/config');
}

export { API_BASE_URL };
