import { useState } from 'react';
import { indexRepo } from '../api';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';

function RepositoryInputPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('');
  const [status, setStatus] = useState({ type: '', text: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const runAbortable = useAbortableAction();

  async function onSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: 'info', text: 'Indexing repository...' });
    try {
      const result = await runAbortable((signal) => indexRepo(repoUrl, branch, { signal }));
      setStatus({ type: 'success', text: `Indexed successfully: ${JSON.stringify(result)}` });
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
    <section className="page">
      <h2>Repository Input</h2>
      <p className="page-intro">Provide a public repository URL to build the backend index for retrieval and explanation.</p>
      <div className="page-chips" aria-label="Repository capabilities">
        <span className="chip">Git</span>
        <span className="chip">Indexing</span>
        <span className="chip">Fast Sync</span>
      </div>
      <form onSubmit={onSubmit} className="panel form-panel">
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
        <button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Indexing...' : 'Index Repository'}</button>
      </form>
      <StatusMessage type={status.type}>{status.text}</StatusMessage>
    </section>
  );
}

export default RepositoryInputPage;
