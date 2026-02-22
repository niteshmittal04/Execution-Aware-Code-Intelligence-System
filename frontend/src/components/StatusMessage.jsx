import { memo } from 'react';

function StatusMessage({ type = 'info', children }) {
  const normalizedText = typeof children === 'string'
    ? children.replace(/\s+/g, ' ').trim()
    : children;

  if (!normalizedText) {
    return null;
  }

  return <p className={`status-message ${type}`}>{normalizedText}</p>;
}

export default memo(StatusMessage);
