import { useState } from 'react';
import { motion } from 'framer-motion';
import { panelEnter } from '../animations/variants';
import Button from '../controls/Button';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';
import Panel from '../panel/Panel';
import { useSessionContext } from '../session/SessionContext';

function formatIndexingSuccess(result) {
  const safeResult = result || {};
  const warnings = Array.isArray(safeResult.warnings) ? safeResult.warnings : [];

  const metrics = [
    `${safeResult.indexed_nodes ?? 0} nodes`,
    `${safeResult.indexed_edges ?? 0} edges`,
    `${safeResult.indexed_variables ?? 0} variables`,
    `${safeResult.indexed_chunks ?? 0} chunks`,
  ];

  const warningSuffix = warnings.length > 0
    ? ` Completed with ${warnings.length} warning${warnings.length === 1 ? '' : 's'}.`
    : '';

  return `Repository indexed successfully. ${metrics.join(' • ')}.${warningSuffix}`;
}

function RepositoryInputPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('');
  const [status, setStatus] = useState({ type: '', text: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const runAbortable = useAbortableAction();
  const { createOrSwitchAndIndex } = useSessionContext();

  async function onSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: 'info', text: 'Indexing repository...' });
    try {
      const { indexResult } = await runAbortable((signal) => createOrSwitchAndIndex({ repoUrl, branch, signal }));
      const result = indexResult || {};
      if (result.status === 'reused') {
        setStatus({ type: 'success', text: 'Existing repository session restored. Reusing indexed artifacts without reindexing.' });
        return;
      }
      setStatus({ type: 'success', text: formatIndexingSuccess(result) });
    } catch (error) {
      if (error.name === 'AbortError') {
        return;
      }
      setStatus({ type: 'error', text: `Index failed: ${error.message}` });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <motion.section className="page" variants={panelEnter} initial="hidden" animate="visible">
      <h2>Repository Input</h2>
      <p className="page-intro">Provide a public repository URL to build the backend index for retrieval and explanation.</p>
      <div className="page-chips" aria-label="Repository capabilities">
        <span className="chip">Git</span>
        <span className="chip">Indexing</span>
        <span className="chip">Fast Sync</span>
      </div>
      <Panel as="form" className="form-panel" onSubmit={onSubmit}>
        <label>
          GitHub URL
          <input
            placeholder="https://github.com/owner/repo"
            value={repoUrl}
            onChange={(event) => setRepoUrl(event.target.value)}
            required
          />
        </label>
        <label>
          Branch (optional)
          <input placeholder="main" value={branch} onChange={(event) => setBranch(event.target.value)} />
        </label>
        <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Indexing...' : 'Index Repository'}</Button>
      </Panel>
      <StatusMessage type={status.type}>{status.text}</StatusMessage>
    </motion.section>
  );
}

export default RepositoryInputPage;
