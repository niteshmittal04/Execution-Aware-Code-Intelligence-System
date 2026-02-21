import { useMemo, useState } from 'react';
import ReactFlow, { Background, Controls } from 'react-flow-renderer';
import { fetchGraph } from '../api';
import StatusMessage from '../components/StatusMessage';
import useAbortableAction from '../hooks/useAbortableAction';
import { buildFlowElements } from '../utils/graphTransforms';

function GraphViewerPage() {
  const [functionName, setFunctionName] = useState('');
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const runAbortable = useAbortableAction();

  async function onLoad(event) {
    event.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const graph = await runAbortable((signal) => fetchGraph(functionName, { signal }));
      const flowElements = buildFlowElements(graph);
      setNodes(flowElements.nodes);
      setEdges(flowElements.edges);
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  const elements = useMemo(() => [...nodes, ...edges], [nodes, edges]);

  return (
    <section className="page">
      <h2>Graph Viewer</h2>
      <p className="page-intro">Render function-level graph connectivity to visualize execution relationships and dependencies.</p>
      <div className="page-chips" aria-label="Graph capabilities">
        <span className="chip">Node Graph</span>
        <span className="chip">Relations</span>
        <span className="chip">Interactive View</span>
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
        <button type="submit" disabled={isLoading}>{isLoading ? 'Loading...' : 'Load Graph'}</button>
      </form>
      <StatusMessage type="error">{error}</StatusMessage>
      <div className="panel graph-panel">
        {elements.length === 0 && <p className="graph-empty">Load a function graph to start exploring relationships.</p>}
        <ReactFlow elements={elements} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </section>
  );
}

export default GraphViewerPage;
