const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const graphCache = new Map();

function normalizeErrorPayload(payload) {
  if (!payload) {
    return '';
  }

  if (typeof payload === 'string') {
    return payload;
  }

  if (Array.isArray(payload)) {
    return payload.map((item) => normalizeErrorPayload(item)).filter(Boolean).join('; ');
  }

  if (typeof payload === 'object') {
    if (payload.detail) {
      return normalizeErrorPayload(payload.detail);
    }
    if (payload.message) {
      return normalizeErrorPayload(payload.message);
    }
    return Object.entries(payload)
      .map(([key, value]) => `${key}: ${normalizeErrorPayload(value) || String(value)}`)
      .join('; ');
  }

  return String(payload);
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const rawText = await response.text();
    let message = rawText;

    try {
      const parsed = JSON.parse(rawText);
      message = normalizeErrorPayload(parsed) || rawText;
    } catch {
      message = rawText;
    }

    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.json();
}

export async function indexRepo(repoUrl, branch, { signal } = {}) {
  throw new Error('Deprecated signature. Use indexRepoBySession(sessionId, options).');
}

export function clearGraphCache() {
  graphCache.clear();
}

export async function createSession({ repoUrl, repoPath, branch, signal } = {}) {
  return requestJson('/session/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_url: repoUrl || null,
      repo_path: repoPath || null,
      branch: branch || null,
    }),
    signal,
  });
}

export async function switchSession({ repoUrl, repoPath, branch, signal } = {}) {
  return requestJson('/session/switch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_url: repoUrl || null,
      repo_path: repoPath || null,
      branch: branch || null,
    }),
    signal,
  });
}

export async function closeSession(sessionId, { signal } = {}) {
  return requestJson('/session/close', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
    signal,
  });
}

export async function resetSession(sessionId, { signal } = {}) {
  return requestJson('/session/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
    signal,
  });
}

export async function getActiveSession({ signal } = {}) {
  return requestJson('/session/active', { signal });
}

export async function getSessionStructure(sessionId, { signal } = {}) {
  return requestJson(`/session/structure?session_id=${encodeURIComponent(sessionId)}`, { signal });
}

export async function indexRepoBySession(sessionId, { repoUrl = null, branch = null, reindex = false, signal } = {}) {
  return requestJson('/index_repo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      repo_url: repoUrl,
      branch,
      reindex,
    }),
    signal,
  });
}

export async function explainFunction(sessionId, functionName, { signal } = {}) {
  return requestJson('/explain_function', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, function_name: functionName }),
    signal,
  });
}

export async function explainSnippet(sessionId, code, language, { signal } = {}) {
  return requestJson('/explain_snippet', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, code, language }),
    signal,
  });
}

export async function fetchGraph(sessionId, functionName, { forceRefresh = false, signal } = {}) {
  const cacheKey = `${sessionId}::${functionName.trim().toLowerCase()}`;

  if (!forceRefresh && graphCache.has(cacheKey)) {
    return graphCache.get(cacheKey);
  }

  const graphData = await requestJson(
    `/graph/${encodeURIComponent(functionName)}?session_id=${encodeURIComponent(sessionId)}`,
    { signal }
  );
  graphCache.set(cacheKey, graphData);
  return graphData;
}
