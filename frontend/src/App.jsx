import { Suspense, lazy, useEffect, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';

const THEME_STORAGE_KEY = 'execution-aware-ui-theme';

const RepositoryInputPage = lazy(() => import('./pages/RepositoryInputPage'));
const FunctionExplorerPage = lazy(() => import('./pages/FunctionExplorerPage'));
const ExplanationViewerPage = lazy(() => import('./pages/ExplanationViewerPage'));
const GraphViewerPage = lazy(() => import('./pages/GraphViewerPage'));

const navItems = [
  { to: '/', label: 'Repository Input', icon: '📦' },
  { to: '/functions', label: 'Function Explorer', icon: 'ƒ' },
  { to: '/explanation', label: 'Explanation Viewer', icon: '✦' },
  { to: '/graph', label: 'Graph Viewer', icon: '◉' },
];

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function detectInitialTheme() {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme;
  }
  return getSystemTheme();
}

function App() {
  const [theme, setTheme] = useState(detectInitialTheme);

  useEffect(() => {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <h1>Execution Aware RAG Code Explainer</h1>
          <p>Index repositories, explore function context, and inspect execution-aware explanations.</p>
        </div>
        <div className="header-controls">
          <nav className="top-nav" aria-label="Primary">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                <span className="nav-icon" aria-hidden="true">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <button
            type="button"
            className="theme-toggle-round"
            onClick={() => setTheme((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark'))}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          >
            {theme === 'dark' ? '☀' : '🌙'}
          </button>
        </div>
      </header>

      <main className="app-main">
        <Suspense fallback={<div className="panel app-loading">Loading page...</div>}>
          <Routes>
            <Route path="/" element={<RepositoryInputPage />} />
            <Route path="/functions" element={<FunctionExplorerPage />} />
            <Route path="/explanation" element={<ExplanationViewerPage />} />
            <Route path="/graph" element={<GraphViewerPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default App;
