import { useEffect, useState } from 'react';

function getSize(node) {
  if (!node) {
    return { width: 0, height: 0 };
  }
  return {
    width: Math.round(node.clientWidth),
    height: Math.round(node.clientHeight),
  };
}

export default function useElementSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const target = ref.current;
    if (!target || typeof ResizeObserver === 'undefined') {
      return undefined;
    }

    const update = () => setSize(getSize(target));
    update();

    const observer = new ResizeObserver(() => {
      update();
    });

    observer.observe(target);
    return () => observer.disconnect();
  }, [ref]);

  return size;
}
