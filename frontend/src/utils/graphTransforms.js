import dagre from 'dagre';

export function getGraphSummary(graph) {
  const files = [...new Set((graph?.nodes || []).map((node) => node.file).filter(Boolean))];
  const functions = (graph?.nodes || [])
    .filter((node) => node.type === 'function')
    .map((node) => node.id);

  return { files, functions };
}

function getCssVarValue(styles, name, fallback) {
  const value = styles?.getPropertyValue(name)?.trim();
  return value || fallback;
}

export function resolveGraphPalette() {
  if (typeof window === 'undefined' || !window.document?.documentElement) {
    return {
      border: '#1f2937',
      text: '#f3f7ff',
      edge: '#7f8ea3',
      accent: '#3b82f6',
      accentAlt: '#22d3ee',
      panelTop: 'rgba(22, 31, 43, 0.95)',
      panelBottom: 'rgba(17, 24, 39, 0.9)',
      glow: 'rgba(59, 130, 246, 0.22)',
      bgDot: '#2c3b52',
      minimapMask: 'rgba(11, 15, 20, 0.5)',
      minimapBg: 'rgba(11, 15, 20, 0.78)',
    };
  }

  const styles = window.getComputedStyle(window.document.documentElement);
  const bg0 = getCssVarValue(styles, '--bg-0', '#0b0f14');
  const bg1 = getCssVarValue(styles, '--bg-1', '#0f1620');

  return {
    border: getCssVarValue(styles, '--border', '#1f2937'),
    text: getCssVarValue(styles, '--graph-node-text', '#f3f7ff'),
    edge: getCssVarValue(styles, '--graph-edge', '#7f8ea3'),
    accent: getCssVarValue(styles, '--accent-0', '#3b82f6'),
    accentAlt: getCssVarValue(styles, '--graph-edge-active', '#22d3ee'),
    panelTop: `${bg1}ee`,
    panelBottom: `${bg0}dd`,
    glow: 'rgba(59, 130, 246, 0.22)',
    bgDot: getCssVarValue(styles, '--graph-dot', '#2c3b52'),
    minimapMask: getCssVarValue(styles, '--graph-minimap-mask', 'rgba(11, 15, 20, 0.5)'),
    minimapBg: getCssVarValue(styles, '--graph-minimap-bg', 'rgba(11, 15, 20, 0.78)'),
  };
}

function truncateLabel(value, max = 56) {
  if (!value) {
    return '';
  }
  if (value.length <= max) {
    return value;
  }
  return `${value.slice(0, max - 1)}…`;
}

function createNodeLabel(node) {
  if (!node?.id) {
    return `${node?.type || 'node'}`;
  }

  if (node.type === 'function') {
    const parts = String(node.id).split(':');
    const functionName = parts.length >= 2 ? parts[parts.length - 2] : parts[parts.length - 1];
    return `function: ${truncateLabel(functionName, 40)}`;
  }

  return `${node.type || 'node'}: ${truncateLabel(String(node.id), 36)}`;
}

function buildDagrePositions(nodeIds, edges) {
  const graph = new dagre.graphlib.Graph({ multigraph: false, compound: false });
  graph.setGraph({ rankdir: 'LR', ranksep: 180, nodesep: 90, edgesep: 30, marginx: 80, marginy: 60 });
  graph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 250;
  const nodeHeight = 54;

  nodeIds.forEach((id) => {
    graph.setNode(id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
      graph.setEdge(edge.source, edge.target);
    }
  });

  dagre.layout(graph);

  const positions = new Map();
  nodeIds.forEach((id) => {
    const node = graph.node(id);
    if (!node) {
      return;
    }
    positions.set(id, {
      x: Math.round(node.x - nodeWidth / 2),
      y: Math.round(node.y - nodeHeight / 2),
    });
  });

  return positions;
}

export function buildFlowElements(graph, palette = resolveGraphPalette()) {
  const allNodes = Array.isArray(graph?.nodes) ? graph.nodes : [];
  const allEdges = Array.isArray(graph?.edges) ? graph.edges : [];

  const finalNodes = allNodes;
  const finalNodeIds = new Set(finalNodes.map((node) => node.id));
  const finalEdges = allEdges.filter((edge) => finalNodeIds.has(edge.source) && finalNodeIds.has(edge.target));

  const nodeIdMap = new Map();
  finalNodes.forEach((node, index) => {
    nodeIdMap.set(node.id, `n-${index}`);
  });

  const sanitizedEdges = finalEdges
    .map((edge, index) => {
      const source = nodeIdMap.get(edge.source);
      const target = nodeIdMap.get(edge.target);
      if (!source || !target) {
        return null;
      }
      return {
        id: `e-${index}`,
        source,
        target,
        type: 'smoothstep',
        data: { relation: edge.type },
        style: {
          stroke: palette.edge,
          strokeWidth: 1.9,
          opacity: 0.9,
        },
      };
    })
    .filter(Boolean);

  let layoutPositions;
  try {
    layoutPositions = buildDagrePositions(
      finalNodes.map((node, index) => `n-${index}`),
      sanitizedEdges
    );
  } catch {
    layoutPositions = new Map();
  }

  const nodes = finalNodes.map((node, index) => {
    const safeId = `n-${index}`;
    const layoutPos = layoutPositions.get(safeId);
    const isFinitePosition = Number.isFinite(layoutPos?.x) && Number.isFinite(layoutPos?.y);
    const position = isFinitePosition
      ? layoutPos
      : { x: 120 + (index % 7) * 260, y: 90 + Math.floor(index / 7) * 130 };

    return {
      id: safeId,
      data: { label: createNodeLabel(node), rawId: node.id, type: node.type },
      position,
      className: 'graph-node-entry',
      style: {
        border: `1px solid ${palette.border}`,
        borderRadius: 10,
        padding: 8,
        background: `linear-gradient(180deg, ${palette.panelTop}, ${palette.panelBottom})`,
        color: palette.text,
        boxShadow: `0 0 0 1px ${palette.glow}, 0 8px 18px rgba(3, 8, 20, 0.36)`,
        willChange: 'opacity, transform',
        width: 250,
        fontSize: 12.5,
        fontWeight: 600,
        lineHeight: 1.3,
      },
    };
  });

  return { nodes, edges: sanitizedEdges };
}
