import { Suspense, lazy, useEffect, useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import AppLayout from './layout/AppLayout';
import StatusBar from './layout/StatusBar';
import TopNavigation from './layout/TopNavigation';
import WorkspaceContainer from './layout/WorkspaceContainer';
import RepositoryStructurePanel from './components/RepositoryStructurePanel';
import { useSessionContext } from './session/SessionContext';

const THEME_STORAGE_KEY = 'execution-aware-ui-theme';

const RepositoryInputPage = lazy(() => import('./pages/RepositoryInputPage'));
const FunctionExplorerPage = lazy(() => import('./pages/FunctionExplorerPage'));
const ExplanationViewerPage = lazy(() => import('./pages/ExplanationViewerPage'));
const GraphViewerPage = lazy(() => import('./pages/GraphViewerPage'));
const CodeViewerPage = lazy(() => import('./pages/CodeViewerPage'));

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function detectInitialTheme() {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme;
  }
  return getSystemTheme();
}

function App() {
  const [theme, setTheme] = useState(detectInitialTheme);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const {
    activeSession,
    repoStructure,
    isSessionLoading,
    resetActiveSession,
    closeActiveSession,
  } = useSessionContext();

  useEffect(() => {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    function onResize() {
      if (window.innerWidth < 960) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    }

    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return (
    <AppLayout
      topNavigation={(
        <TopNavigation
          activeSession={activeSession}
          theme={theme}
          onThemeToggle={() => setTheme((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark'))}
          onToggleSidebar={() => setIsSidebarOpen((previous) => !previous)}
          onResetSession={() => resetActiveSession()}
          onCloseSession={() => closeActiveSession()}
        />
      )}
      workspace={(
        <WorkspaceContainer
          isSidebarOpen={isSidebarOpen}
          onCloseSidebar={() => setIsSidebarOpen(false)}
          sidebar={<RepositoryStructurePanel structure={repoStructure} activeSessionId={activeSession?.session_id} />}
        >
          <Suspense fallback={<div className="panel app-loading">Loading page...</div>}>
            <Routes>
              <Route path="/" element={<RepositoryInputPage />} />
              <Route path="/functions" element={<FunctionExplorerPage />} />
              <Route path="/explanation" element={<ExplanationViewerPage />} />
              <Route path="/graph" element={<GraphViewerPage />} />
              <Route path="/code" element={<CodeViewerPage />} />
            </Routes>
          </Suspense>
        </WorkspaceContainer>
      )}
      statusBar={<StatusBar activeSession={activeSession} isSessionLoading={isSessionLoading} />}
    />
  );
}

export default App;
