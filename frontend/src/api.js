const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const graphCache = new Map();

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function indexRepo(repoUrl, branch, { signal } = {}) {
  return requestJson('/index_repo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, branch: branch || null }),
    signal,
  });
}

export async function explainFunction(functionName, { signal } = {}) {
  return requestJson('/explain_function', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ function_name: functionName }),
    signal,
  });
}

export async function explainSnippet(code, language, { signal } = {}) {
  return requestJson('/explain_snippet', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, language }),
    signal,
  });
}

export async function fetchGraph(functionName, { forceRefresh = false, signal } = {}) {
  const cacheKey = functionName.trim().toLowerCase();

  if (!forceRefresh && graphCache.has(cacheKey)) {
    return graphCache.get(cacheKey);
  }

  const graphData = await requestJson(`/graph/${encodeURIComponent(functionName)}`, { signal });
  graphCache.set(cacheKey, graphData);
  return graphData;
}
