import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { getSessionFileContent } from '../api';
import { panelEnter } from '../animations/variants';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';
import Panel from '../panel/Panel';
import { useSessionContext } from '../session/SessionContext';

function CodeViewerPage() {
  const location = useLocation();
  const { activeSession } = useSessionContext();
  const runAbortable = useAbortableAction();
  const [status, setStatus] = useState({ type: '', text: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [loadedFilePath, setLoadedFilePath] = useState('');
  const [content, setContent] = useState('');

  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const sessionId = searchParams.get('session_id') || activeSession?.session_id || '';
  const filePath = searchParams.get('file_path') || '';

  useEffect(() => {
    async function loadFile() {
      if (!sessionId || !filePath) {
        setStatus({ type: 'info', text: 'Missing file context. Open a file from the sidebar.' });
        setLoadedFilePath('');
        setContent('');
        return;
      }

      setStatus({ type: 'info', text: 'Loading file content...' });
      setIsLoading(true);
      try {
        const payload = await runAbortable((signal) => getSessionFileContent(sessionId, filePath, { signal }));
        setLoadedFilePath(payload?.file_path || filePath);
        setContent(payload?.content || '');
        setStatus({ type: 'success', text: 'File loaded.' });
      } catch (err) {
        if (err.name === 'AbortError') {
          return;
        }
        setLoadedFilePath('');
        setContent('');
        setStatus({ type: 'error', text: err.message });
      } finally {
        setIsLoading(false);
      }
    }

    loadFile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filePath, sessionId]);

  return (
    <motion.section className="page" variants={panelEnter} initial="hidden" animate="visible">
      <h2>Code Viewer</h2>
      <p className="page-intro">Open source files directly from the repository sidebar in a separate browser tab.</p>
      <StatusMessage type={status.type}>{status.text}</StatusMessage>
      <Panel className="result-card code-viewer-panel">
        <h3>{loadedFilePath || 'No file selected'}</h3>
        <pre className="code-viewer-content" aria-busy={isLoading}>{content}</pre>
      </Panel>
    </motion.section>
  );
}

export default CodeViewerPage;
