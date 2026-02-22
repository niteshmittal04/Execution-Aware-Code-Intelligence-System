import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  clearGraphCache,
  closeSession,
  createSession,
  getActiveSession,
  getSessionStructure,
  indexRepoBySession,
  resetSession,
} from '../api';

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [activeSession, setActiveSession] = useState(null);
  const [repoStructure, setRepoStructure] = useState(null);
  const [isSessionLoading, setIsSessionLoading] = useState(true);

  async function refreshActiveSession() {
    setIsSessionLoading(true);
    try {
      const payload = await getActiveSession();
      const session = payload?.session || null;
      setActiveSession(session);
      if (session?.session_id) {
        const structurePayload = await getSessionStructure(session.session_id);
        setRepoStructure(structurePayload?.structure || null);
      } else {
        setRepoStructure(null);
      }
    } finally {
      setIsSessionLoading(false);
    }
  }

  useEffect(() => {
    refreshActiveSession();
  }, []);

  async function createOrSwitchAndIndex({ repoUrl, branch, signal }) {
    const created = await createSession({ repoUrl, branch, signal });
    const session = created?.session || null;
    if (!session?.session_id) {
      throw new Error('Failed to create repository session.');
    }

    clearGraphCache();
    setActiveSession(session);
    const indexResult = await indexRepoBySession(session.session_id, { signal });
    const structurePayload = await getSessionStructure(session.session_id, { signal });
    setRepoStructure(structurePayload?.structure || null);

    return { session, indexResult };
  }

  async function refreshStructure(signal) {
    if (!activeSession?.session_id) {
      return null;
    }
    const payload = await getSessionStructure(activeSession.session_id, { signal });
    setRepoStructure(payload?.structure || null);
    return payload?.structure || null;
  }

  async function resetActiveSession(signal) {
    if (!activeSession?.session_id) {
      return null;
    }
    clearGraphCache();
    const payload = await resetSession(activeSession.session_id, { signal });
    const session = payload?.session || activeSession;
    setActiveSession(session);
    const structurePayload = await getSessionStructure(session.session_id, { signal });
    setRepoStructure(structurePayload?.structure || null);
    return payload;
  }

  async function closeActiveSession(signal) {
    if (!activeSession?.session_id) {
      return null;
    }
    await closeSession(activeSession.session_id, { signal });
    clearGraphCache();
    setActiveSession(null);
    setRepoStructure(null);
    return true;
  }

  const value = useMemo(
    () => ({
      activeSession,
      repoStructure,
      isSessionLoading,
      createOrSwitchAndIndex,
      refreshActiveSession,
      refreshStructure,
      resetActiveSession,
      closeActiveSession,
    }),
    [activeSession, repoStructure, isSessionLoading]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSessionContext() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSessionContext must be used inside SessionProvider');
  }
  return context;
}
