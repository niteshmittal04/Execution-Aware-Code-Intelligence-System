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
  }));

  const edges = graph.edges.map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.type,
  }));

  return { nodes, edges };
}
