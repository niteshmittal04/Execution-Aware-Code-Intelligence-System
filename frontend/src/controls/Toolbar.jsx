import { memo } from 'react';

function Toolbar({ left, center, right }) {
  return (
    <div className="toolbar" role="toolbar" aria-label="Page controls">
      <div className="toolbar-section toolbar-left">{left}</div>
      <div className="toolbar-section toolbar-center">{center}</div>
      <div className="toolbar-section toolbar-right">{right}</div>
    </div>
  );
}

export default memo(Toolbar);
