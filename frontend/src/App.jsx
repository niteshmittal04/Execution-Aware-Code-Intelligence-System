import { Link, Route, Routes } from 'react-router-dom';
import RepositoryInputPage from './pages/RepositoryInputPage';
import FunctionExplorerPage from './pages/FunctionExplorerPage';
import ExplanationViewerPage from './pages/ExplanationViewerPage';
import GraphViewerPage from './pages/GraphViewerPage';

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Execution Aware RAG Code Explainer</h1>
        <nav>
          <Link to="/">Repository Input</Link>
          <Link to="/functions">Function Explorer</Link>
          <Link to="/explanation">Explanation Viewer</Link>
          <Link to="/graph">Graph Viewer</Link>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<RepositoryInputPage />} />
          <Route path="/functions" element={<FunctionExplorerPage />} />
          <Route path="/explanation" element={<ExplanationViewerPage />} />
          <Route path="/graph" element={<GraphViewerPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
