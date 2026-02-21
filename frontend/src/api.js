const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function indexRepo(repoUrl, branch) {
  const response = await fetch(`${API_BASE}/index_repo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, branch: branch || null }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function explainFunction(functionName) {
  const response = await fetch(`${API_BASE}/explain_function`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ function_name: functionName }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function explainSnippet(code, language) {
  const response = await fetch(`${API_BASE}/explain_snippet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, language }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function fetchGraph(functionName) {
  const response = await fetch(`${API_BASE}/graph/${encodeURIComponent(functionName)}`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}
