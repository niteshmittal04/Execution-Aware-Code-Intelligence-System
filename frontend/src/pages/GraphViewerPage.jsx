import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import ReactFlow, { Background, Controls, MiniMap } from 'react-flow-renderer';
import { fetchGraph } from '../api';
import { panelEnter } from '../animations/variants';
import StatusMessage from '../components/StatusMessage';
import Button from '../controls/Button';
import Toolbar from '../controls/Toolbar';
import useAbortableAction from '../hooks/useAbortableAction';
import Panel from '../panel/Panel';
import { useSessionContext } from '../session/SessionContext';
import { buildFlowElements, resolveGraphPalette } from '../utils/graphTransforms';

function GraphViewerPage() {
  const location = useLocation();
  const { activeSession } = useSessionContext();
  const [functionName, setFunctionName] = useState('');
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [rawGraph, setRawGraph] = useState(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [hasRenderedFlowNodes, setHasRenderedFlowNodes] = useState(false);
  const [hasCheckedFlowRender, setHasCheckedFlowRender] = useState(false);
  const [collapsedNodeIds, setCollapsedNodeIds] = useState([]);
  const [layoutRevision, setLayoutRevision] = useState(0);
  const [hoveredNodeId, setHoveredNodeId] = useState('');
  const [themeMode, setThemeMode] = useState(() => document.documentElement.getAttribute('data-theme') || 'dark');
  const [status, setStatus] = useState({ type: '', text: '' });
  const [isLoading, setIsLoading] = useState(false);
  const graphContainerRef = useRef(null);
  const hasFittedViewRef = useRef(false);
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

  useEffect(() => {
    const root = document.documentElement;
    const observer = new MutationObserver(() => {
      setThemeMode(root.getAttribute('data-theme') || 'dark');
    });

    observer.observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  const palette = useMemo(() => resolveGraphPalette(), [themeMode]);

  useEffect(() => {
    if (!rawGraph) {
      return;
    }
    const flowElements = buildFlowElements(rawGraph, palette);
    setNodes(flowElements.nodes);
    setEdges(flowElements.edges);
    setCollapsedNodeIds([]);
    setHasRenderedFlowNodes(false);
    setHasCheckedFlowRender(false);
    setLayoutRevision((value) => value + 1);
  }, [rawGraph, palette]);

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
      setRawGraph(graph);
      hasFittedViewRef.current = false;

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

  const highlightedGraph = useMemo(() => {
    const collapsedSet = new Set(collapsedNodeIds);
    const outgoing = new Map();
    edges.forEach((edge) => {
      if (!outgoing.has(edge.source)) {
        outgoing.set(edge.source, []);
      }
      outgoing.get(edge.source).push(edge.target);
    });

    const hiddenNodeIds = new Set();
    collapsedSet.forEach((rootId) => {
      const stack = [...(outgoing.get(rootId) || [])];
      while (stack.length > 0) {
        const targetId = stack.pop();
        if (hiddenNodeIds.has(targetId) || collapsedSet.has(targetId)) {
          continue;
        }
        hiddenNodeIds.add(targetId);
        const next = outgoing.get(targetId) || [];
        next.forEach((nextId) => stack.push(nextId));
      }
    });

    const visibleNodes = nodes.filter((node) => !hiddenNodeIds.has(node.id));
    const visibleNodeIds = new Set(visibleNodes.map((node) => node.id));
    const visibleEdges = edges.filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target));

    if (!hoveredNodeId) {
      const baseNodes = visibleNodes.map((node) => ({
        ...node,
        style: {
          ...(node.style || {}),
          border: collapsedSet.has(node.id) ? `1px solid ${palette.accent}` : (node.style?.border || `1px solid ${palette.border}`),
          boxShadow: collapsedSet.has(node.id)
            ? `0 0 0 1px ${palette.accent}, 0 0 16px rgba(59, 130, 246, 0.22)`
            : (node.style?.boxShadow || 'none'),
        },
      }));
      return { nodes: baseNodes, edges: visibleEdges };
    }

    const nextNodes = visibleNodes.map((node) => {
      const isHovered = node.id === hoveredNodeId;
      const isConnected = visibleEdges.some((edge) => (edge.source === hoveredNodeId && edge.target === node.id)
        || (edge.target === hoveredNodeId && edge.source === node.id));

      return {
        ...node,
        style: {
          ...(node.style || {}),
          opacity: isHovered || isConnected ? 1 : 0.7,
          border: isHovered || collapsedSet.has(node.id) ? `1px solid ${palette.accent}` : `1px solid ${palette.border}`,
          boxShadow: isHovered ? `0 0 0 1px ${palette.accent}, 0 0 14px rgba(59, 130, 246, 0.2)` : (node.style?.boxShadow || 'none'),
        },
      };
    });

    const nextEdges = visibleEdges.map((edge) => {
      const isConnected = edge.source === hoveredNodeId || edge.target === hoveredNodeId;
      return {
        ...edge,
        animated: isConnected,
        style: {
          ...(edge.style || {}),
          stroke: isConnected ? palette.accentAlt : palette.edge,
          strokeWidth: isConnected ? 2.2 : 1.6,
          opacity: isConnected ? 1 : 0.82,
        },
      };
    });

    return { nodes: nextNodes, edges: nextEdges };
  }, [nodes, edges, hoveredNodeId, palette, collapsedNodeIds]);

  useEffect(() => {
    if (!reactFlowInstance || nodes.length === 0 || hasFittedViewRef.current) {
      return;
    }
    const timeoutId = window.setTimeout(() => {
      reactFlowInstance.fitView({ padding: 0.22, includeHiddenNodes: false });
      hasFittedViewRef.current = true;
    }, 40);
    return () => window.clearTimeout(timeoutId);
  }, [reactFlowInstance, layoutRevision, nodes.length]);

  useEffect(() => {
    if (nodes.length === 0) {
      setHasRenderedFlowNodes(false);
      setHasCheckedFlowRender(false);
      return;
    }

    let attempts = 0;
    const maxAttempts = 16;
    const intervalId = window.setInterval(() => {
      attempts += 1;
      const container = graphContainerRef.current;
      const renderedNodesCount = container?.querySelectorAll('.react-flow__node, [class*="react-flow__node-"]')?.length || 0;
      if (renderedNodesCount > 0) {
        setHasRenderedFlowNodes(true);
        setHasCheckedFlowRender(true);
        window.clearInterval(intervalId);
      } else if (attempts >= maxAttempts) {
        setHasRenderedFlowNodes(false);
        setHasCheckedFlowRender(true);
        window.clearInterval(intervalId);
      }
    }, 150);

    return () => window.clearInterval(intervalId);
  }, [nodes, edges]);

  const shouldShowFallback = nodes.length > 0 && hasCheckedFlowRender && !hasRenderedFlowNodes && !isLoading;

  function onFlowReady(instance) {
    setReactFlowInstance(instance);
  }

  function onNodeClick(_, node) {
    const clickedId = node?.id;
    if (!clickedId) {
      return;
    }
    setCollapsedNodeIds((previous) => {
      if (previous.includes(clickedId)) {
        return previous.filter((item) => item !== clickedId);
      }
      return [...previous, clickedId];
    });
  }

  function onResetView() {
    if (!reactFlowInstance || highlightedGraph.nodes.length === 0) {
      return;
    }
    reactFlowInstance.fitView({ padding: 0.22, includeHiddenNodes: false });
    hasFittedViewRef.current = true;
  }

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
          right={(
            <div className="graph-toolbar-actions">
              <Button type="button" variant="secondary" onClick={onResetView} disabled={isLoading || highlightedGraph.nodes.length === 0}>Reset View</Button>
              <Button type="submit" disabled={isLoading}>{isLoading ? 'Loading...' : 'Load Graph'}</Button>
            </div>
          )}
        />
      </Panel>
      <StatusMessage type={status.type}>{status.text}</StatusMessage>
      <Panel className="graph-panel graph-viewer-container" >
        <div className="graph-canvas" ref={graphContainerRef}>
          {nodes.length === 0 && <p className="graph-empty">Load a function graph to start exploring relationships.</p>}
          {nodes.length > 0 && (
            <p className="graph-hint">Click a node to collapse/expand downstream branches. Collapsed: {collapsedNodeIds.length}</p>
          )}
          {shouldShowFallback && (
            <div className="graph-fallback" aria-label="Graph fallback view">
              <div className="graph-fallback-header">
                <strong>Fallback Graph View</strong>
                <span>{nodes.length} nodes · {edges.length} edges</span>
              </div>
              <div className="graph-fallback-grid">
                {nodes.slice(0, 120).map((node) => (
                  <div key={node.id} className="graph-fallback-node">{node.data?.label || node.id}</div>
                ))}
              </div>
            </div>
          )}
          <ReactFlow
            key={`flow-${themeMode}`}
            nodes={highlightedGraph.nodes}
            edges={highlightedGraph.edges}
            minZoom={0.4}
            maxZoom={1.7}
            onLoad={onFlowReady}
            onInit={onFlowReady}
            onNodeMouseEnter={(_, node) => setHoveredNodeId(node?.id || '')}
            onNodeMouseLeave={() => setHoveredNodeId('')}
            onNodeClick={onNodeClick}
            panOnScroll
            zoomOnPinch
            zoomOnScroll
          >
          <Background variant="dots" gap={18} size={1.2} color={palette.bgDot} />
          <MiniMap
            nodeColor={palette.accent}
            maskColor={palette.minimapMask}
            style={{ background: palette.minimapBg, border: `1px solid ${palette.border}` }}
          />
          <Controls />
          </ReactFlow>
        </div>
      </Panel>
    </motion.section>
  );
}

export default GraphViewerPage;
