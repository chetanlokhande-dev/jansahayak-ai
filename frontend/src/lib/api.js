// All calls go to the FastAPI backend. No secrets live in the browser.
const BASE = import.meta.env.VITE_API_BASE || '';

function getClientId() {
  try {
    let id = localStorage.getItem('jansahayak_client_id');
    if (!id) {
      id = (crypto.randomUUID && crypto.randomUUID()) || `c-${Date.now()}-${Math.random().toString(16).slice(2)}0000000000`;
      localStorage.setItem('jansahayak_client_id', id);
    }
    return id;
  } catch {
    return 'anonymous-session-0000000000';
  }
}

async function request(path, { method = 'GET', body, form } = {}) {
  const headers = { 'X-Client-Id': getClientId() };
  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  } catch {
    throw new Error('Cannot reach the server. Please check that the backend is running and try again.');
  }
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON response */ }
  if (!res.ok) {
    const detail = data && data.detail;
    const message = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map((d) => d.msg).join('; ')
      : `Request failed (${res.status}).`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  meta: () => request('/api/meta'),
  schemes: (q = '', category = '') =>
    request(`/api/schemes?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}`),
  rights: () => request('/api/rights'),
  chat: (message, language, conversationId, documentId) =>
    request('/api/chat', { method: 'POST', body: { message, language, conversation_id: conversationId || null, document_id: documentId || null } }),
  uploadDocument: (file, language) => {
    const form = new FormData();
    form.append('file', file);
    form.append('language', language);
    return request('/api/documents', { method: 'POST', form });
  },
  sampleDocuments: () => request('/api/sample-documents'),
  analyzeSample: (name, language) =>
    request(`/api/sample-documents/${encodeURIComponent(name)}?language=${language}`, { method: 'POST' }),
  getDocument: (id) => request(`/api/documents/${id}`),
  eligibilityFields: (lang) => request(`/api/eligibility/fields?lang=${lang}`),
  checkEligibility: (profile, language) =>
    request('/api/eligibility/check', { method: 'POST', body: { profile, language, explain: true } }),
  history: () => request('/api/history'),
  conversation: (id) => request(`/api/history/conversations/${id}`),
  deleteConversation: (id) => request(`/api/history/conversations/${id}`, { method: 'DELETE' }),
  deleteDocument: (id) => request(`/api/documents/${id}`, { method: 'DELETE' }),
  clearHistory: () => request('/api/history', { method: 'DELETE' }),
};
