import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import ReactFlow, { Background, Controls } from 'react-flow-renderer';
import { fetchGraph } from '../api';
import { panelEnter } from '../animations/variants';
import StatusMessage from '../components/StatusMessage';
import Button from '../controls/Button';
import Toolbar from '../controls/Toolbar';
import useAbortableAction from '../hooks/useAbortableAction';
import useElementSize from '../hooks/useElementSize';
import Panel from '../panel/Panel';
import { useSessionContext } from '../session/SessionContext';
import { buildFlowElements } from '../utils/graphTransforms';

function GraphViewerPage() {
  const location = useLocation();
  const { activeSession } = useSessionContext();
  const [functionName, setFunctionName] = useState('');
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [hoveredNodeId, setHoveredNodeId] = useState('');
  const [status, setStatus] = useState({ type: '', text: '' });
  const [isLoading, setIsLoading] = useState(false);
  const graphContainerRef = useRef(null);
  const graphContainerSize = useElementSize(graphContainerRef);
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

    setStatus({ type: 'info', text: 'Loading graph...' });
    setIsLoading(true);
    try {
      const graph = await runAbortable((signal) =>
        fetchGraph(activeSession.session_id, targetFunctionName, { forceRefresh: true, signal })
      );
      const flowElements = buildFlowElements(graph);
      setNodes(flowElements.nodes);
      setEdges(flowElements.edges);

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

  const highlightedElements = useMemo(() => {
    if (!hoveredNodeId) {
      return [...nodes, ...edges];
    }

    const nextNodes = nodes.map((node) => {
      const isHovered = node.id === hoveredNodeId;
      const isConnected = edges.some((edge) => (edge.source === hoveredNodeId && edge.target === node.id)
        || (edge.target === hoveredNodeId && edge.source === node.id));

      return {
        ...node,
        style: {
          ...(node.style || {}),
          opacity: isHovered || isConnected ? 1 : 0.5,
          border: isHovered ? '1px solid #3B82F6' : '1px solid #1F2937',
        },
      };
    });

    const nextEdges = edges.map((edge) => {
      const isConnected = edge.source === hoveredNodeId || edge.target === hoveredNodeId;
      return {
        ...edge,
        animated: isConnected,
        style: {
          ...(edge.style || {}),
          stroke: isConnected ? '#06B6D4' : '#1F2937',
          strokeWidth: isConnected ? 2 : 1,
          opacity: isConnected ? 1 : 0.4,
        },
      };
    });

    return [...nextNodes, ...nextEdges];
  }, [nodes, edges, hoveredNodeId]);

  useEffect(() => {
    if (!reactFlowInstance || highlightedElements.length === 0) {
      return;
    }
    const timeoutId = window.setTimeout(() => {
      reactFlowInstance.fitView({ padding: 0.2 });
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [reactFlowInstance, highlightedElements, graphContainerSize.width, graphContainerSize.height]);

  return (
    <motion.section className="page" variants={panelEnter} initial="hidden" animate="visible">
      <h2>Graph Viewer</h2>
      <p className="page-intro">Render function-level graph connectivity to visualize execution relationships and dependencies.</p>
      <div className="page-chips" aria-label="Graph capabilities">
        <span className="chip">Node Graph</span>
        <span className="chip">Relations</span>
        <span className="chip">Interactive View</span>
      </div>
      <Panel as="form" onSubmit={onLoad} className="form-panel">
        <Toolbar
          left={(
            <label className="toolbar-input-group">
              <span>Function name</span>
              <input
                placeholder="module.function_name"
                value={functionName}
                onChange={(event) => setFunctionName(event.target.value)}
                required
              />
            </label>
          )}
          center={<span className="toolbar-context">Interactive execution graph</span>}
          right={<Button type="submit" disabled={isLoading}>{isLoading ? 'Loading...' : 'Load Graph'}</Button>}
        />
      </Panel>
      <StatusMessage type={status.type}>{status.text}</StatusMessage>
      <Panel className="graph-panel graph-viewer-container" >
        <div className="graph-canvas" ref={graphContainerRef}>
          {highlightedElements.length === 0 && <p className="graph-empty">Load a function graph to start exploring relationships.</p>}
          <ReactFlow
            elements={highlightedElements}
            fitView
            minZoom={0.2}
            maxZoom={1.7}
            onLoad={setReactFlowInstance}
            onNodeMouseEnter={(_, node) => setHoveredNodeId(node?.id || '')}
            onNodeMouseLeave={() => setHoveredNodeId('')}
            panOnScroll
            zoomOnPinch
          >
          <Background gap={20} color="#1F2937" />
          <Controls />
          </ReactFlow>
        </div>
      </Panel>
    </motion.section>
  );
}

export default GraphViewerPage;
