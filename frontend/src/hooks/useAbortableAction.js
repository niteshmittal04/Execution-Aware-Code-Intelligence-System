import { useEffect, useRef } from 'react';

function useAbortableAction() {
  const controllerRef = useRef(null);

  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
    };
  }, []);

  async function runAbortable(requestFactory) {
    controllerRef.current?.abort();

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      return await requestFactory(controller.signal);
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
      }
    }
  }

  return runAbortable;
}

export default useAbortableAction;
