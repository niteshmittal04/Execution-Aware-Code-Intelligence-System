import { memo } from 'react';
import { NavLink } from 'react-router-dom';
import Button from '../controls/Button';

const navItems = [
  { to: '/', label: 'Repository Input', icon: '📦' },
  { to: '/functions', label: 'Function Explorer', icon: 'ƒ' },
  { to: '/explanation', label: 'Explanation Viewer', icon: '✦' },
  { to: '/graph', label: 'Graph Viewer', icon: '◉' },
];

function TopNavigation({
  activeSession,
  theme,
  onThemeToggle,
  onToggleSidebar,
  onResetSession,
  onCloseSession,
}) {
  return (
    <header className="top-navigation">
      <div className="top-navigation-header">
        <div className="top-navigation-copy">
          <h1>Execution Aware RAG Code Explainer</h1>
          <p>Index repositories, explore execution context, and inspect explanation outputs.</p>
          <span className="active-repository-pill">
            Active Repository: {activeSession?.repo_path || 'None'}
          </span>
        </div>
        <div className="top-navigation-actions">
          <Button variant="ghost" className="icon-only" onClick={onToggleSidebar} aria-label="Toggle sidebar">
            ☰
          </Button>
          <Button
            variant="ghost"
            className="icon-only"
            onClick={onThemeToggle}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          >
            {theme === 'dark' ? '☀' : '🌙'}
          </Button>
        </div>
      </div>

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

      {activeSession?.session_id ? (
        <div className="session-actions">
          <Button variant="secondary" onClick={onResetSession}>Reset Session</Button>
          <Button variant="secondary" onClick={onCloseSession}>Exit Repository</Button>
        </div>
      ) : null}
    </header>
  );
}

export default memo(TopNavigation);
