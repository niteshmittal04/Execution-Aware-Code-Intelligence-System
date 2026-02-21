import { useState } from 'react';
import { fetchGraph } from '../api';
import ListPanel from '../components/ListPanel';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';
import { getGraphSummary } from '../utils/graphTransforms';

function FunctionExplorerPage() {
  const [functionName, setFunctionName] = useState('');
  const [fileTree, setFileTree] = useState([]);
  const [functions, setFunctions] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const runAbortable = useAbortableAction();

  async function onLoad(event) {
    event.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const graph = await runAbortable((signal) => fetchGraph(functionName, { signal }));
      const { files, functions: graphFunctions } = getGraphSummary(graph);
      setFileTree(files);
      setFunctions(graphFunctions);
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="page">
      <h2>Function Explorer</h2>
      <p className="page-intro">Load graph data for a target function to inspect discovered files and related function nodes.</p>
      <div className="page-chips" aria-label="Function explorer capabilities">
        <span className="chip">Symbol Map</span>
        <span className="chip">Call Context</span>
        <span className="chip">File Discovery</span>
      </div>
      <form onSubmit={onLoad} className="panel form-panel">
        <label>
          Function name
          <input
            placeholder="module.function_name"
            value={functionName}
            onChange={(event) => setFunctionName(event.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={isLoading}>{isLoading ? 'Loading...' : 'Load'}</button>
      </form>
      <StatusMessage type="error">{error}</StatusMessage>
      <div className="grid-two">
        <ListPanel title="File Tree" count={fileTree.length} items={fileTree} emptyText="No files loaded yet." />
        <ListPanel title="Functions List" count={functions.length} items={functions} emptyText="No functions loaded yet." />
      </div>
    </section>
  );
}

export default FunctionExplorerPage;
