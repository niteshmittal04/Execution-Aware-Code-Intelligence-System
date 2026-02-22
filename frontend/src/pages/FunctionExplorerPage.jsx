import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { panelEnter } from '../animations/variants';
import Button from '../controls/Button';
import { fetchGraph } from '../api';
import ListPanel from '../components/ListPanel';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';
import Panel from '../panel/Panel';
import { useSessionContext } from '../session/SessionContext';
import { getGraphSummary } from '../utils/graphTransforms';

function FunctionExplorerPage() {
  const location = useLocation();
  const { activeSession } = useSessionContext();
  const [functionName, setFunctionName] = useState('');
  const [fileTree, setFileTree] = useState([]);
  const [functions, setFunctions] = useState([]);
  const [status, setStatus] = useState({ type: '', text: '' });
  const [isLoading, setIsLoading] = useState(false);
  const runAbortable = useAbortableAction();

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const functionFromQuery = searchParams.get('fn');
    if (functionFromQuery) {
      setFunctionName(functionFromQuery);
    }
  }, [location.search]);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const functionFromQuery = searchParams.get('fn');
    if (functionFromQuery && activeSession?.session_id) {
      onLoad(null, functionFromQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSession?.session_id, location.search]);

  async function onLoad(event, overrideFunctionName = '') {
    if (event) {
      event.preventDefault();
    }
    if (!activeSession?.session_id) {
      setStatus({ type: 'error', text: 'No active repository session. Load a repository first.' });
      return;
    }
    const targetFunctionName = (overrideFunctionName || functionName).trim();
    if (!targetFunctionName) {
      setStatus({ type: 'error', text: 'Function name is required.' });
      return;
    }

    setStatus({ type: 'info', text: 'Loading function graph...' });
    setIsLoading(true);
    try {
      const graph = await runAbortable((signal) =>
        fetchGraph(activeSession.session_id, targetFunctionName, { forceRefresh: true, signal })
      );
      const { files, functions: graphFunctions } = getGraphSummary(graph);
      setFileTree(files);
      setFunctions(graphFunctions);

      if ((graph.nodes?.length || 0) === 0) {
        setStatus({ type: 'info', text: 'No graph data found for this function. Try only the function name (for example: exception).' });
      } else {
        setStatus({ type: 'success', text: `Loaded ${graph.nodes.length} node(s) and ${graph.edges.length} edge(s).` });
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setStatus({ type: 'error', text: err.message });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <motion.section className="page" variants={panelEnter} initial="hidden" animate="visible">
      <h2>Function Explorer</h2>
      <p className="page-intro">Load graph data for a target function to inspect discovered files and related function nodes.</p>
      <div className="page-chips" aria-label="Function explorer capabilities">
        <span className="chip">Symbol Map</span>
        <span className="chip">Call Context</span>
        <span className="chip">File Discovery</span>
      </div>
      <Panel as="form" onSubmit={onLoad} className="form-panel">
        <label>
          Function name
          <input
            placeholder="module.function_name"
            value={functionName}
            onChange={(event) => setFunctionName(event.target.value)}
            required
          />
        </label>
        <Button type="submit" disabled={isLoading}>{isLoading ? 'Loading...' : 'Load'}</Button>
      </Panel>
      <StatusMessage type={status.type}>{status.text}</StatusMessage>
      <div className="grid-two">
        <ListPanel title="File Tree" count={fileTree.length} items={fileTree} emptyText="No files loaded yet." />
        <ListPanel title="Functions List" count={functions.length} items={functions} emptyText="No functions loaded yet." />
      </div>
    </motion.section>
  );
}

export default FunctionExplorerPage;
