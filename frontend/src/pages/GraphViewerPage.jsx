import { useMemo, useState } from 'react';
import ReactFlow, { Background, Controls } from 'react-flow-renderer';
import { fetchGraph } from '../api';

function GraphViewerPage() {
  const [functionName, setFunctionName] = useState('');
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [error, setError] = useState('');

  async function onLoad(event) {
    event.preventDefault();
    setError('');
    try {
      const graph = await fetchGraph(functionName);
      setNodes(
        graph.nodes.map((node, index) => ({
          id: node.id,
          data: { label: `${node.type}: ${node.id}` },
          position: { x: 120 + (index % 5) * 220, y: 80 + Math.floor(index / 5) * 140 },
        }))
      );
      setEdges(
        graph.edges.map((edge, index) => ({
          id: `${edge.source}-${edge.target}-${index}`,
          source: edge.source,
          target: edge.target,
          label: edge.type,
        }))
      );
    } catch (err) {
      setError(err.message);
    }
  }

  const elements = useMemo(() => [...nodes, ...edges], [nodes, edges]);

  return (
    <section>
      <h2>Graph Viewer</h2>
      <form onSubmit={onLoad} className="panel">
        <label>
          Function name
          <input value={functionName} onChange={(event) => setFunctionName(event.target.value)} required />
        </label>
        <button type="submit">Load Graph</button>
      </form>
      {error && <p>{error}</p>}
      <div className="panel" style={{ height: '65vh' }}>
        <ReactFlow elements={elements} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </section>
  );
}

export default GraphViewerPage;
