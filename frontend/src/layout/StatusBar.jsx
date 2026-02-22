import { memo } from 'react';

function StatusBar({ activeSession, isSessionLoading }) {
  return (
    <footer className="status-bar" aria-live="polite">
      <span className="status-item">Session: {activeSession?.session_id || 'Not initialized'}</span>
      <span className="status-item">Repository: {activeSession?.repo_path || 'None'}</span>
      <span className="status-item">State: {isSessionLoading ? 'Syncing…' : 'Ready'}</span>
    </footer>
  );
}

export default memo(StatusBar);
