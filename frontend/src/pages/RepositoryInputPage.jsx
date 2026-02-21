import { useState } from 'react';
import { indexRepo } from '../api';

function RepositoryInputPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('');
  const [status, setStatus] = useState('');

  async function onSubmit(event) {
    event.preventDefault();
    setStatus('Indexing repository...');
    try {
      const result = await indexRepo(repoUrl, branch);
      setStatus(`Indexed: ${JSON.stringify(result)}`);
    } catch (error) {
      setStatus(`Index failed: ${error.message}`);
    }
  }

  return (
    <section>
      <h2>Repository Input</h2>
      <form onSubmit={onSubmit} className="panel">
        <label>
          GitHub URL
          <input value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} required />
        </label>
        <label>
          Branch (optional)
          <input value={branch} onChange={(event) => setBranch(event.target.value)} />
        </label>
        <button type="submit">Index Repository</button>
      </form>
      <p>{status}</p>
    </section>
  );
}

export default RepositoryInputPage;
