import { memo } from 'react';
import Panel from '../panel/Panel';

function ListPanel({ title, count, items, emptyText }) {
  return (
    <Panel>
      <h3 className="panel-heading">
        {title} <span>{count}</span>
      </h3>
      {items.length === 0 ? (
        <p className="empty-state">{emptyText}</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export default memo(ListPanel);
