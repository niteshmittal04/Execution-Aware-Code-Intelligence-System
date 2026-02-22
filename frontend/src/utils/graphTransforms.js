export function getGraphSummary(graph) {
  const files = [...new Set(graph.nodes.map((node) => node.file).filter(Boolean))];
  const functions = graph.nodes
    .filter((node) => node.type === 'function')
    .map((node) => node.id);

  return { files, functions };
}

export function buildFlowElements(graph) {
  const nodes = graph.nodes.map((node, index) => ({
    id: node.id,
    data: { label: `${node.type}: ${node.id}` },
    position: { x: 120 + (index % 5) * 220, y: 80 + Math.floor(index / 5) * 140 },
    className: 'graph-node-entry',
    style: {
      border: '1px solid #1F2937',
      borderRadius: 10,
      padding: 8,
      background: '#161F2B',
      color: '#E6EDF3',
      willChange: 'opacity',
    },
  }));

  const edges = graph.edges.map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.type,
    style: {
      stroke: '#1F2937',
      strokeWidth: 1,
    },
  }));

  return { nodes, edges };
}
