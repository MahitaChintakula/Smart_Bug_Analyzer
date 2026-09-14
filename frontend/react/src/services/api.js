const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function analyzeBug(bugReport) {
  let response;

  try {
    response = await fetch(`${API_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bug_report: bugReport }),
    });
  } catch {
    throw new Error('Cannot connect to the analysis service. Make sure FastAPI is running.');
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(payload?.detail || `The analysis service returned HTTP ${response.status}.`);
  }

  return payload;
}

export async function extractTextFromImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  return requestApi(
    '/extract-text',
    {
      method: 'POST',
      body: formData,
    },
    'OCR service',
  );
}

export async function askBugChat(analysis, messages, message) {
  let response;

  try {
    response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analysis, messages, message }),
    });
  } catch {
    throw new Error('Cannot connect to the chatbot. Make sure FastAPI is running.');
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail || `The chatbot returned HTTP ${response.status}.`);
  }

  return payload?.message || 'The chatbot returned an empty response.';
}

async function requestApi(path, options = {}, serviceName = 'knowledge-base service') {
  let response;

  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error(`Cannot connect to the ${serviceName}. Make sure FastAPI is running.`);
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail || `The ${serviceName} returned HTTP ${response.status}.`);
  }

  return payload;
}

export function getKnowledgeBase(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return requestApi(`/knowledge-base${query ? `?${query}` : ''}`);
}

export function getKnowledgeBaseStats() {
  return requestApi('/knowledge-base/stats');
}

export function rebuildKnowledgeBase() {
  return requestApi('/knowledge-base/rebuild', { method: 'POST' });
}

export function addKnowledgeBaseEntry(entry) {
  return requestApi('/knowledge-base', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  });
}
