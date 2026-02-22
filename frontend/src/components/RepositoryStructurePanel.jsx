import { memo, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Button from '../controls/Button';
import Panel from '../panel/Panel';

function getNodeIcon(nodeType) {
  if (nodeType === 'repo') return '◈';
  if (nodeType === 'directory') return '▸';
  if (nodeType === 'file') return '•';
  if (nodeType === 'module') return '◦';
  if (nodeType === 'class') return '◇';
  if (nodeType === 'function') return 'ƒ';
  return '•';
}

function NodeActions({ value }) {
  const encoded = encodeURIComponent(value);
  return (
    <span className="node-actions">
      <Link to={`/functions?fn=${encoded}`} className="node-action-link">Explorer</Link>
      <Link to={`/graph?fn=${encoded}`} className="node-action-link">Graph</Link>
      <Link to={`/explanation?fn=${encoded}`} className="node-action-link">Explain</Link>
    </span>
  );
}

function collectExpandablePaths(node, parentPath = '') {
  const nodePath = parentPath ? `${parentPath}/${node.name}` : node.name;
  const children = Array.isArray(node.children) ? node.children : [];
  if (children.length === 0) {
    return [];
  }

  const nested = children.flatMap((child) => collectExpandablePaths(child, nodePath));
  return [nodePath, ...nested];
}

function StructureNode({
  node,
  parentPath = '',
  expandedNodePaths,
  onToggleNode,
}) {
  const nodePath = parentPath ? `${parentPath}/${node.name}` : node.name;
  const children = Array.isArray(node.children) ? node.children : [];
  const hasChildren = children.length > 0;
  const isExpanded = expandedNodePaths.has(nodePath);
  const targetValue = node.type === 'file' ? (node.name || '').replace(/\.[^/.]+$/, '') : node.name;

  return (
    <li className={`structure-node ${node.type}`}>
      <div className="structure-node-row">
        {hasChildren ? (
          <button
            type="button"
            className="node-toggle-btn"
            onClick={() => onToggleNode(nodePath)}
            aria-label={isExpanded ? `Collapse ${node.name}` : `Expand ${node.name}`}
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? '▾' : '▸'}
          </button>
        ) : (
          <span className="node-toggle-spacer" aria-hidden="true" />
        )}
        <span className={`structure-node-label ${node.type}`}>
          <span className="structure-node-icon" aria-hidden="true">{getNodeIcon(node.type)}</span>
          <span className="structure-node-name">{node.name}</span>
        </span>
      </div>
      {targetValue ? <NodeActions value={targetValue} /> : null}
      {hasChildren && isExpanded ? (
        <ul className="structure-tree-children" aria-label={nodePath}>
          {children.map((child, index) => (
            <StructureNode
              key={`${nodePath}-${child.type}-${child.name}-${index}`}
              node={child}
              parentPath={nodePath}
              expandedNodePaths={expandedNodePaths}
              onToggleNode={onToggleNode}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

function RepositoryStructurePanel({ structure }) {
  const allExpandablePaths = useMemo(() => {
    if (!structure) {
      return [];
    }
    return collectExpandablePaths(structure);
  }, [structure]);

  const [expandedNodePaths, setExpandedNodePaths] = useState(() => new Set(allExpandablePaths));

  useEffect(() => {
    setExpandedNodePaths(new Set(allExpandablePaths));
  }, [allExpandablePaths]);

  function onToggleNode(nodePath) {
    setExpandedNodePaths((previous) => {
      const next = new Set(previous);
      if (next.has(nodePath)) {
        next.delete(nodePath);
      } else {
        next.add(nodePath);
      }
      return next;
    });
  }

  function onExpandAll() {
    setExpandedNodePaths(new Set(allExpandablePaths));
  }

  function onCollapseAll() {
    setExpandedNodePaths(new Set());
  }

  if (!structure) {
    return (
      <Panel as="aside" className="repo-structure-panel">
        <h3 className="panel-heading">Repository Structure</h3>
        <p className="empty-state">No active repository session.</p>
      </Panel>
    );
  }

  return (
    <Panel as="aside" className="repo-structure-panel">
      <div className="repo-structure-header">
        <h3 className="panel-heading">Repository Structure</h3>
        <div className="repo-structure-controls">
          <Button type="button" variant="ghost" className="repo-structure-btn" onClick={onExpandAll}>Expand all</Button>
          <Button type="button" variant="ghost" className="repo-structure-btn" onClick={onCollapseAll}>Collapse all</Button>
        </div>
      </div>
      <ul className="structure-tree-root">
        <StructureNode
          node={structure}
          expandedNodePaths={expandedNodePaths}
          onToggleNode={onToggleNode}
        />
      </ul>
    </Panel>
  );
}

export default memo(RepositoryStructurePanel);
